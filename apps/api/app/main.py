import logging
import json
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from .analytics import analytics
from .config import Settings, get_settings
from .database import Base, SessionLocal, engine, get_db
from .deps import current_user
from .models import AnalyticsEvent, Feedback, LearnerProfile, LessonSession, Progress, ReviewItem, SavedVocabulary, Scenario, SubscriptionEntitlement, TranscriptTurn, User
from .providers import AudioInput, ConversationRequest, build_ai_providers
from .schemas import DeleteAccount, DemoAuth, FeedbackOut, ProfileOut, ProfileUpdate, ReviewGrade, ScenarioOut, SessionCreate, SessionOut, TurnCreate, TurnResponse, WordCreate
from .seed import seed_scenarios
from .subscriptions import MockEntitlementProvider

class SafeJsonFormatter(logging.Formatter):
 def format(self, record: logging.LogRecord) -> str:
  event = {"timestamp": self.formatTime(record), "level": record.levelname, "logger": record.name, "event": record.getMessage()}
  for key in ("method", "path", "status", "event_name"):
   if hasattr(record, key): event[key] = getattr(record, key)
  return json.dumps(event)

handler = logging.StreamHandler()
handler.setFormatter(SafeJsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler], force=True)
logger=logging.getLogger("mengo.api")
settings=get_settings()
hits:dict[str,deque[float]]=defaultdict(deque)
@asynccontextmanager
async def lifespan(_: FastAPI):
 Base.metadata.create_all(engine)
 db=SessionLocal()
 try: seed_scenarios(db)
 finally: db.close()
 build_ai_providers(settings) # fail closed rather than activate any live provider
 yield

app=FastAPI(title="Mengo API",version="0.1.0",description="Local Mandarin-learning MVP API",lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=settings.allowed_origins,allow_credentials=False,allow_methods=["GET","POST","PUT","DELETE"],allow_headers=["Content-Type","X-Demo-User"])

@app.middleware("http")
async def rate_limit(request:Request,call_next):
 key=request.client.host if request.client else "unknown"; now=time.monotonic(); bucket=hits[key]
 while bucket and bucket[0] <= now-60: bucket.popleft()
 if len(bucket)>=settings.rate_limit_per_minute: return JSONResponse(429,{"detail":"Development rate limit exceeded. Try again shortly."})
 bucket.append(now); response=await call_next(request)
 logger.info("request_complete",extra={"method":request.method,"path":request.url.path,"status":response.status_code})
 return response

@app.exception_handler(ValueError)
async def bad_value(_:Request,exc:ValueError): return JSONResponse(422,{"detail":str(exc)})

@app.get("/health")
def health(): return {"status":"ok","provider_mode":settings.ai_provider_mode,"demo_mode":settings.demo_mode}

@app.post("/v1/auth/demo")
def demo_auth(body:DemoAuth,db:Session=Depends(get_db),app_settings:Settings=Depends(get_settings)):
 if not app_settings.demo_mode or app_settings.app_env=="production": raise HTTPException(401,"Demo identity is disabled outside local demo mode.")
 user_id="demo-"+uuid.uuid5(uuid.NAMESPACE_DNS,body.display_name.lower()).hex[:12]
 user=db.get(User,user_id)
 if not user:
  db.add_all([User(id=user_id,display_name=body.display_name),LearnerProfile(user_id=user_id),Progress(user_id=user_id),SubscriptionEntitlement(user_id=user_id,plan="free",active=True,source="demo")]);db.commit()
 return {"demo_user_id":user_id,"warning":"Local demo identity only; not authentication."}

@app.get("/v1/me/profile",response_model=ProfileOut)
def profile(user:User=Depends(current_user),db:Session=Depends(get_db)): return db.get(LearnerProfile,user.id)

@app.put("/v1/me/profile",response_model=ProfileOut)
def update_profile(body:ProfileUpdate,user:User=Depends(current_user),db:Session=Depends(get_db)):
 item=db.get(LearnerProfile,user.id);item.goal,item.level,item.minutes_per_day,item.onboarding_complete=body.goal,body.level,body.minutes_per_day,True
 analytics().track(db,"onboarding_completed",user.id,{"level":body.level,"minutes_per_day":body.minutes_per_day});db.commit();db.refresh(item);return item

@app.get("/v1/scenarios",response_model=list[ScenarioOut])
def scenarios(_:User=Depends(current_user),db:Session=Depends(get_db)): return db.scalars(select(Scenario).order_by(Scenario.duration_minutes)).all()

@app.get("/v1/lessons",response_model=list[ScenarioOut])
def lessons(_:User=Depends(current_user),db:Session=Depends(get_db)):
 return db.scalars(select(Scenario).order_by(Scenario.duration_minutes)).all()

@app.get("/v1/scenarios/{scenario_id}",response_model=ScenarioOut)
def scenario(scenario_id:str,_:User=Depends(current_user),db:Session=Depends(get_db)):
 item=db.get(Scenario,scenario_id)
 if not item: raise HTTPException(404,"Scenario not found")
 return item

@app.post("/v1/sessions",response_model=SessionOut,status_code=201)
def create_session(body:SessionCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
 if not db.get(Scenario,body.scenario_id): raise HTTPException(404,"Scenario not found")
 item=LessonSession(id=uuid.uuid4().hex,user_id=user.id,scenario_id=body.scenario_id);db.add(item);analytics().track(db,"lesson_started",user.id,{"scenario_id":body.scenario_id});db.commit();db.refresh(item);return item

@app.get("/v1/sessions/{session_id}")
def session(session_id:str,user:User=Depends(current_user),db:Session=Depends(get_db)):
 item=db.get(LessonSession,session_id)
 if not item or item.user_id!=user.id: raise HTTPException(404,"Session not found")
 turns=db.scalars(select(TranscriptTurn).where(TranscriptTurn.session_id==session_id).order_by(TranscriptTurn.id)).all()
 return {"id":item.id,"scenario_id":item.scenario_id,"status":item.status,"turn_count":item.turn_count,"turns":[{"role":x.role,"text":x.text} for x in turns]}

@app.post("/v1/sessions/{session_id}/turns",response_model=TurnResponse)
def turn(session_id:str,body:TurnCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
 lesson=db.get(LessonSession,session_id)
 if not lesson or lesson.user_id!=user.id: raise HTTPException(404,"Session not found")
 if lesson.status=="completed": raise HTTPException(409,"Session is already completed")
 provider=build_ai_providers(settings); source=AudioInput(transcript_hint=body.transcript); transcript=provider.stt.transcribe(source).text; number=lesson.turn_count+1; reply=provider.conversation.reply(ConversationRequest(scenario_id=lesson.scenario_id,learner_text=transcript,turn_number=number)); score=provider.pronunciation.score(source,transcript)
 feedback=Feedback(session_id=session_id,grammar="Try the pattern: subject + 想 + verb.",vocabulary="Nice attempt. Reuse one scenario word in your next reply.",tones=score.tones,pronunciation_score=score.score)
 db.add_all([TranscriptTurn(session_id=session_id,role="learner",text=transcript),TranscriptTurn(session_id=session_id,role="tutor",text=reply.text),feedback]);lesson.turn_count=number; completed=number>=3
 if completed:
  lesson.status="completed";lesson.completed_at=datetime.utcnow();progress=db.get(Progress,user.id);today=date.today().isoformat();progress.current_streak=progress.current_streak+1 if progress.last_activity_date!=today else progress.current_streak;progress.last_activity_date=today;progress.completed_lessons+=1;progress.total_minutes+=db.get(Scenario,lesson.scenario_id).duration_minutes;analytics().track(db,"lesson_completed",user.id,{"scenario_id":lesson.scenario_id})
 db.commit()
 return TurnResponse(learner_transcript=transcript,tutor_response=reply.text,tutor_pinyin=reply.pinyin,feedback=FeedbackOut.model_validate(feedback),session_completed=completed)

@app.post("/v1/words",status_code=201)
def save_word(body:WordCreate,user:User=Depends(current_user),db:Session=Depends(get_db)):
 old=db.scalar(select(SavedVocabulary).where(SavedVocabulary.user_id==user.id,SavedVocabulary.hanzi==body.hanzi))
 if old: return {"id":old.id,"created":False}
 word=SavedVocabulary(user_id=user.id,**body.model_dump());db.add(word);db.flush();db.add(ReviewItem(user_id=user.id,vocabulary_id=word.id));analytics().track(db,"word_saved",user.id,{"hanzi_length":len(body.hanzi)});db.commit();return {"id":word.id,"created":True}

@app.get("/v1/review")
def review(user:User=Depends(current_user),db:Session=Depends(get_db)):
 rows=db.execute(select(ReviewItem,SavedVocabulary).join(SavedVocabulary,ReviewItem.vocabulary_id==SavedVocabulary.id).where(ReviewItem.user_id==user.id,ReviewItem.due_at<=datetime.utcnow()).order_by(ReviewItem.due_at)).all()
 return [{"id":item.id,"due_at":item.due_at,"interval_days":item.interval_days,"word":{"hanzi":word.hanzi,"pinyin":word.pinyin,"english":word.english}} for item,word in rows]

@app.post("/v1/review/{review_id}")
def grade(review_id:int,body:ReviewGrade,user:User=Depends(current_user),db:Session=Depends(get_db)):
 item=db.get(ReviewItem,review_id)
 if not item or item.user_id!=user.id: raise HTTPException(404,"Review item not found")
 item.interval_days=max(1,item.interval_days*(2 if body.rating>=2 else 1));item.due_at=datetime.utcnow()+timedelta(days=item.interval_days);analytics().track(db,"review_completed",user.id,{"rating":body.rating});db.commit();return {"id":item.id,"next_review_at":item.due_at,"interval_days":item.interval_days}

@app.get("/v1/progress")
def progress(user:User=Depends(current_user),db:Session=Depends(get_db)): return db.get(Progress,user.id)

@app.get("/v1/entitlement")
def entitlement(user:User=Depends(current_user),db:Session=Depends(get_db)):
 item=MockEntitlementProvider().get(db,user.id)
 db.commit()
 return {"plan":item.plan,"active":item.active,"source":item.source,"purchase_enabled":False}

@app.get("/v1/admin/analytics")
def admin(_:User=Depends(current_user),db:Session=Depends(get_db)):
 return {"mode":"local-demo","learners":db.scalar(select(func.count()).select_from(User)) or 0,"completed_lessons":db.scalar(select(func.count()).select_from(LessonSession).where(LessonSession.status=="completed")) or 0,"allowlisted_events":db.scalar(select(func.count()).select_from(AnalyticsEvent)) or 0,"privacy_note":"Counts only; audio and transcripts are excluded."}

@app.delete("/v1/me",status_code=204)
def delete_account(body:DeleteAccount,user:User=Depends(current_user),db:Session=Depends(get_db)):
 if not settings.demo_mode: raise HTTPException(403,"Deletion endpoint is demo-mode only")
 session_ids=db.scalars(select(LessonSession.id).where(LessonSession.user_id==user.id)).all()
 if session_ids: db.query(TranscriptTurn).filter(TranscriptTurn.session_id.in_(session_ids)).delete(synchronize_session=False);db.query(Feedback).filter(Feedback.session_id.in_(session_ids)).delete(synchronize_session=False)
 for model in (LessonSession,ReviewItem,SavedVocabulary,Progress,LearnerProfile,SubscriptionEntitlement): db.query(model).filter_by(user_id=user.id).delete()
 db.query(User).filter_by(id=user.id).delete();analytics().track(db,"account_deleted",None,{"mode":"demo"});db.commit();return Response(status_code=204)
