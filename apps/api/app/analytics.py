import logging
from sqlalchemy.orm import Session
from .models import AnalyticsEvent
logger=logging.getLogger(__name__)
EVENT_ALLOWLIST={"onboarding_completed","lesson_started","lesson_completed","word_saved","review_completed","account_deleted"}
class MockAnalytics:
 def track(self,db:Session,name:str,user_id:str|None,properties:dict):
  if name not in EVENT_ALLOWLIST: raise ValueError("Analytics event is not allowlisted")
  db.add(AnalyticsEvent(user_id=user_id,name=name,properties=properties)); logger.info("analytics_event",extra={"event_name":name})
def analytics(): return MockAnalytics()
# PostHog is a configuration placeholder only: no network adapter ships in this MVP.
