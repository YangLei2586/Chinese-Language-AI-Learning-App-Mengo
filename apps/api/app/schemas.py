from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
class ORM(BaseModel): model_config=ConfigDict(from_attributes=True)
class ProfileUpdate(BaseModel):
 goal:str=Field(min_length=2,max_length=120); level:str=Field(pattern="^(beginner|elementary|intermediate)$"); minutes_per_day:int=Field(ge=5,le=120)
class ProfileOut(ProfileUpdate,ORM): onboarding_complete:bool
class ScenarioOut(ORM):
 id:str; title:str; title_zh:str; category:str; level:str; duration_minutes:int; prompt:str; vocabulary:list[dict[str,str]]
class SessionCreate(BaseModel): scenario_id:str=Field(min_length=1,max_length=64)
class SessionOut(ORM): id:str; scenario_id:str; status:str; turn_count:int; created_at:datetime
class TurnCreate(BaseModel): transcript:str=Field(min_length=1,max_length=600); audio_duration_seconds:int|None=Field(default=None,ge=0,le=120)
class FeedbackOut(ORM): grammar:str; vocabulary:str; tones:str; pronunciation_score:float
class TurnResponse(BaseModel): learner_transcript:str; tutor_response:str; tutor_pinyin:str; feedback:FeedbackOut; session_completed:bool
class WordCreate(BaseModel): hanzi:str=Field(min_length=1,max_length=64); pinyin:str=Field(min_length=1,max_length=128); english:str=Field(min_length=1,max_length=200)
class ReviewGrade(BaseModel): rating:int=Field(ge=0,le=3)
class DemoAuth(BaseModel): display_name:str=Field(default="Mengo learner",min_length=2,max_length=80)
class DeleteAccount(BaseModel): confirm:str=Field(pattern="^DELETE$")
