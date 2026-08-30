def test_onboarding_profile_flow(client,headers):
 auth=client.post("/v1/auth/demo",json={"display_name":"Taylor"})
 assert auth.status_code==200
 assert client.get("/v1/entitlement",headers={"X-Demo-User":auth.json()["demo_user_id"]}).status_code==200
 assert client.get("/v1/me/profile",headers=headers).json()["onboarding_complete"] is False
 response=client.put("/v1/me/profile",headers=headers,json={"goal":"Order food on a trip","level":"beginner","minutes_per_day":15})
 assert response.status_code==200 and response.json()["onboarding_complete"] is True

def test_mock_conversation_feedback_and_completion(client,headers):
 scenarios=client.get("/v1/scenarios",headers=headers).json();assert {x["id"] for x in scenarios}=={"introductions","ordering-food","travel","work-meeting"}
 assert client.get("/v1/lessons",headers=headers).status_code==200
 session=client.post("/v1/sessions",headers=headers,json={"scenario_id":"introductions"}).json()
 for _ in range(3): response=client.post(f"/v1/sessions/{session['id']}/turns",headers=headers,json={"transcript":"你好，我叫 Sam","audio_duration_seconds":2})
 body=response.json();assert body["session_completed"] is True;assert body["tutor_response"]=="做得很好！你完成了这个练习。";assert .68<=body["feedback"]["pronunciation_score"]<=.92

def test_review_and_progress(client,headers):
 assert client.post("/v1/words",headers=headers,json={"hanzi":"你好","pinyin":"nǐ hǎo","english":"hello"}).status_code==201
 queue=client.get("/v1/review",headers=headers).json();assert len(queue)==1
 assert client.post(f"/v1/review/{queue[0]['id']}",headers=headers,json={"rating":3}).json()["interval_days"]==2
 session=client.post("/v1/sessions",headers=headers,json={"scenario_id":"travel"}).json()
 for _ in range(3): client.post(f"/v1/sessions/{session['id']}/turns",headers=headers,json={"transcript":"地铁站在哪儿？"})
 progress=client.get("/v1/progress",headers=headers).json();assert progress["completed_lessons"]==1 and progress["current_streak"]==1

def test_live_provider_without_configuration_is_refused():
 import pytest
 from app.config import Settings
 from app.providers import build_ai_providers
 with pytest.raises(RuntimeError,match="requires explicitly configured credentials"): build_ai_providers(Settings(ai_provider_mode="live"))

def test_demo_account_deletion_removes_sessions(client,headers):
 session=client.post("/v1/sessions",headers=headers,json={"scenario_id":"introductions"}).json()
 assert client.request("DELETE","/v1/me",headers=headers,json={"confirm":"DELETE"}).status_code==204
 assert client.get(f"/v1/sessions/{session['id']}",headers=headers).status_code==404
