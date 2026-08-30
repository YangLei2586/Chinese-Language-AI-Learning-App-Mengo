# API quick reference

All API routes use JSON. Local development identifies a learner through `X-Demo-User` (letters, numbers, `_`, `-`, 3–64 chars); it is not authentication and is rejected outside demo mode. Errors use FastAPI's `{ "detail": "..." }` shape. Request bodies are size- and field-validated.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Local health and provider mode |
| `POST` | `/v1/auth/demo` | Derive a deterministic local demo identity |
| `GET`, `PUT` | `/v1/me/profile` | Retrieve/update onboarding profile |
| `DELETE` | `/v1/me` | Demo-only deletion; body `{ "confirm": "DELETE" }` |
| `GET` | `/v1/scenarios` | Seeded scenario catalog |
| `GET` | `/v1/lessons` | Lesson catalog (the scenario-backed MVP lessons) |
| `GET` | `/v1/scenarios/{id}` | One scenario and vocabulary |
| `POST` | `/v1/sessions` | Start scenario with `{ "scenario_id": "introductions" }` |
| `GET` | `/v1/sessions/{id}` | Read local transcript/session state |
| `POST` | `/v1/sessions/{id}/turns` | Send `{ "transcript": "你好", "audio_duration_seconds": 0 }` to mock flow |
| `POST` | `/v1/words` | Save `{ "hanzi", "pinyin", "english" }` |
| `GET` | `/v1/review` | Due review cards |
| `POST` | `/v1/review/{id}` | Grade card `{ "rating": 0..3 }` |
| `GET` | `/v1/progress` | Completion, minutes, streak |
| `GET` | `/v1/entitlement` | Mock free entitlement, purchase disabled |
| `GET` | `/v1/admin/analytics` | Aggregate local-demo metrics only |

Interactive API documentation is available at `/docs` while the backend is running.

## Example

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/scenarios -Headers @{ 'X-Demo-User' = 'demo-learner' }
```
