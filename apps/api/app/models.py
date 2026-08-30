from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base
def now(): return datetime.utcnow()
class User(Base):
 __tablename__="users"; id: Mapped[str]=mapped_column(String(64),primary_key=True); display_name: Mapped[str]=mapped_column(String(80),default="Mengo learner"); created_at: Mapped[datetime]=mapped_column(DateTime,default=now)
class LearnerProfile(Base):
 __tablename__="learner_profiles"; user_id: Mapped[str]=mapped_column(ForeignKey("users.id"),primary_key=True); goal: Mapped[str]=mapped_column(String(120),default="Travel confidently"); level: Mapped[str]=mapped_column(String(32),default="beginner"); minutes_per_day: Mapped[int]=mapped_column(Integer,default=10); onboarding_complete: Mapped[bool]=mapped_column(Boolean,default=False)
class Scenario(Base):
 __tablename__="scenarios"; id: Mapped[str]=mapped_column(String(64),primary_key=True); title: Mapped[str]=mapped_column(String(120)); title_zh: Mapped[str]=mapped_column(String(120)); category: Mapped[str]=mapped_column(String(60)); level: Mapped[str]=mapped_column(String(32)); duration_minutes: Mapped[int]=mapped_column(Integer); prompt: Mapped[str]=mapped_column(Text); vocabulary: Mapped[list]=mapped_column(JSON,default=list)
class LessonSession(Base):
 __tablename__="lesson_sessions"; id: Mapped[str]=mapped_column(String(64),primary_key=True); user_id: Mapped[str]=mapped_column(ForeignKey("users.id"),index=True); scenario_id: Mapped[str]=mapped_column(ForeignKey("scenarios.id")); status: Mapped[str]=mapped_column(String(24),default="active"); turn_count: Mapped[int]=mapped_column(Integer,default=0); created_at: Mapped[datetime]=mapped_column(DateTime,default=now); completed_at: Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
class TranscriptTurn(Base):
 __tablename__="transcript_turns"; id: Mapped[int]=mapped_column(primary_key=True); session_id: Mapped[str]=mapped_column(ForeignKey("lesson_sessions.id"),index=True); role: Mapped[str]=mapped_column(String(16)); text: Mapped[str]=mapped_column(Text); created_at: Mapped[datetime]=mapped_column(DateTime,default=now)
class Feedback(Base):
 __tablename__="feedback"; id: Mapped[int]=mapped_column(primary_key=True); session_id: Mapped[str]=mapped_column(ForeignKey("lesson_sessions.id"),index=True); grammar: Mapped[str]=mapped_column(Text); vocabulary: Mapped[str]=mapped_column(Text); tones: Mapped[str]=mapped_column(Text); pronunciation_score: Mapped[float]=mapped_column(Float); created_at: Mapped[datetime]=mapped_column(DateTime,default=now)
class SavedVocabulary(Base):
 __tablename__="saved_vocabulary"; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[str]=mapped_column(ForeignKey("users.id"),index=True); hanzi: Mapped[str]=mapped_column(String(64)); pinyin: Mapped[str]=mapped_column(String(128)); english: Mapped[str]=mapped_column(String(200)); created_at: Mapped[datetime]=mapped_column(DateTime,default=now); __table_args__=(UniqueConstraint("user_id","hanzi",name="uq_saved_word"),)
class ReviewItem(Base):
 __tablename__="review_items"; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[str]=mapped_column(ForeignKey("users.id"),index=True); vocabulary_id: Mapped[int]=mapped_column(ForeignKey("saved_vocabulary.id")); due_at: Mapped[datetime]=mapped_column(DateTime,default=now); interval_days: Mapped[int]=mapped_column(Integer,default=1)
class Progress(Base):
 __tablename__="progress"; user_id: Mapped[str]=mapped_column(ForeignKey("users.id"),primary_key=True); completed_lessons: Mapped[int]=mapped_column(Integer,default=0); total_minutes: Mapped[int]=mapped_column(Integer,default=0); current_streak: Mapped[int]=mapped_column(Integer,default=0); last_activity_date: Mapped[str|None]=mapped_column(String(10),nullable=True)
class SubscriptionEntitlement(Base):
 __tablename__="subscription_entitlements"; user_id: Mapped[str]=mapped_column(ForeignKey("users.id"),primary_key=True); plan: Mapped[str]=mapped_column(String(32),default="free"); active: Mapped[bool]=mapped_column(Boolean,default=True); source: Mapped[str]=mapped_column(String(32),default="demo")
class AnalyticsEvent(Base):
 __tablename__="analytics_events"; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[str|None]=mapped_column(String(64),nullable=True); name: Mapped[str]=mapped_column(String(80),index=True); properties: Mapped[dict]=mapped_column(JSON,default=dict); created_at: Mapped[datetime]=mapped_column(DateTime,default=now)
