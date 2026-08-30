import os
os.environ["MENGO_DATABASE_URL"]="sqlite:///./test_mengo.db"
os.environ["MENGO_APP_ENV"]="test"
os.environ["MENGO_DEMO_MODE"]="true"
import pytest
from fastapi.testclient import TestClient
from app.database import Base, SessionLocal, engine
from app.main import app
from app.seed import seed_scenarios
@pytest.fixture(autouse=True)
def clean_database():
 Base.metadata.drop_all(engine);Base.metadata.create_all(engine);db=SessionLocal();seed_scenarios(db);db.close();yield;Base.metadata.drop_all(engine)
@pytest.fixture
def client():
 with TestClient(app) as item: yield item
@pytest.fixture
def headers(): return {"X-Demo-User":"test-learner"}
