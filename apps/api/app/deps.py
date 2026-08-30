import re
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from .config import Settings,get_settings
from .database import get_db
from .models import User,LearnerProfile,Progress,SubscriptionEntitlement
PATTERN=re.compile(r"^[A-Za-z0-9_-]{3,64}$")
def current_user(db:Session=Depends(get_db),x_demo_user:str|None=Header(default=None),settings:Settings=Depends(get_settings)):
 if not settings.demo_mode or settings.app_env=="production": raise HTTPException(status.HTTP_401_UNAUTHORIZED,"Demo identity is disabled outside local demo mode.")
 user_id=x_demo_user or "demo-learner"
 if not PATTERN.fullmatch(user_id): raise HTTPException(422,"X-Demo-User must contain 3-64 letters, digits, underscores, or hyphens.")
 user=db.get(User,user_id)
 if not user:
  user=User(id=user_id);db.add_all([user,LearnerProfile(user_id=user_id),Progress(user_id=user_id),SubscriptionEntitlement(user_id=user_id,plan="free",active=True,source="demo")]);db.commit();db.refresh(user)
 return user
