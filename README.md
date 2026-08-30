# Mengo

**Mengo** is a local MVP/research product for English-speaking Mandarin learners. It helps learners prepare for real conversations—introductions, food, travel, and work—through compact scenario practice, English explanations, vocabulary review, and deterministic tutor feedback.

> This repository deliberately ships **no production AI, speech, analytics, or payment credentials**. It is not a fluency, educational, medical, or safety guarantee.

## Run locally (Windows PowerShell)

### Prerequisites

- Python 3.11 or newer (`py -3.11 --version`)
- Node.js 20+ and npm 10+
- Optional: Expo Go on a phone or an Android emulator

### 1. Start the API

```powershell
Set-Location 'E:\AppStore\MengoApp\apps\api'
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e '.[dev]'
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

The API initializes its local SQLite schema and seeds scenarios at startup. Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for OpenAPI documentation.

### 2. Start the website

In a second PowerShell window:

```powershell
Set-Location 'E:\AppStore\MengoApp'
Copy-Item apps\web\.env.example apps\web\.env.local
npm install
npm run web:dev
```

Open [http://localhost:3000](http://localhost:3000). The local-demo dashboard is at `/dashboard`.

### 3. Start the Expo learner app

In a third PowerShell window:

```powershell
Set-Location 'E:\AppStore\MengoApp'
Copy-Item apps\mobile\.env.example apps\mobile\.env
npm run mobile:start
```

For Android emulators, the sample `EXPO_PUBLIC_API_URL=http://10.0.2.2:8000/v1` works. For a physical device, replace it with `http://<your-LAN-IP>:8000/v1` and add that exact origin to `MENGO_CORS_ORIGINS` if using Expo web. The app is intentionally typed-input plus mock-speech; it does not record microphone audio.

### Optional: run API in Docker

```powershell
Set-Location 'E:\AppStore\MengoApp'
docker compose -f infrastructure\docker-compose.yml up --build
```

## Documented AWS production target

Local development remains SQLite and deterministic mock providers. The documented production target is AWS and is deliberately design-only: it does not provision resources or require credentials.

- Static Next.js export: **CloudFront + private S3**, protected by AWS WAF
- FastAPI/API workers: **API Gateway HTTP API → VPC Link → internal ALB → ECS Fargate**
- Data/platform: **RDS PostgreSQL**, ElastiCache Redis, private SSE-KMS S3 audio, SQS + DLQs, Cognito, Secrets Manager, CloudWatch/X-Ray, EventBridge, SES/SNS, KMS, VPC private subnets/security groups, and AWS Backup
- Mobile: iOS/Android builds remain **Expo/EAS** applications that authenticate with Cognito and call AWS APIs over HTTPS; they never contain AWS credentials or direct database access.

See [the AWS IaC-oriented design](infrastructure/aws/README.md) before implementing a cloud environment. It covers media lifecycle, queues, encryption, networking, deployment, and explicit production review gates.

## Provider configuration and local mocks

Mengo defaults to deterministic local mocks. The documented production recommendation is OpenAI GPT for conversation, Deepgram for Mandarin STT, and ElevenLabs for Mandarin TTS, with Anthropic Claude, Google Gemini/Cloud Speech/Text-to-Speech, and AWS Bedrock/Transcribe/Polly as selectable alternatives. Provider names and model IDs are configuration only; this repository includes no vendor SDK or live adapter.

```dotenv
MENGO_AI_PROVIDER_MODE=mock
MENGO_LLM_PROVIDER=openai
MENGO_STT_PROVIDER=deepgram
MENGO_TTS_PROVIDER=elevenlabs
MENGO_OPENAI_API_KEY=
MENGO_DEEPGRAM_API_KEY=
MENGO_ELEVENLABS_API_KEY=
```

Keep all keys blank locally. In the AWS target, approved runtime secrets come only from Secrets Manager; AWS-native Bedrock/Transcribe/Polly use ECS task-role IAM rather than static access keys. Live mode validates required selected-provider configuration, then fails closed because no reviewed live adapter is bundled. See [provider design, consent, cost, latency, and fallback policy](docs/providers.md).

## Verify

```powershell
Set-Location 'E:\AppStore\MengoApp\apps\api'
.\.venv\Scripts\python.exe -m pytest

Set-Location 'E:\AppStore\MengoApp'
npm run web:typecheck
npm run web:build
npm run mobile:typecheck
```

## Repository layout

```text
apps/api                 FastAPI + SQLAlchemy local API
apps/mobile              Expo / React Native learner experience
apps/web                 Next.js public site and local-demo dashboard
packages/shared-types    TypeScript contracts shared across clients
docs                     Architecture, runbook, privacy/production notes
infrastructure           Local Docker Compose configuration
infrastructure/aws       AWS production IaC-oriented target design (non-provisioning)
```

## What is implemented

- English-first onboarding: goal, level, and daily time commitment
- Scenario dashboard: introductions, food, travel, and work meetings
- Deterministic mock conversation, mock STT/TTS interfaces, transcript, feedback, and completion flow
- Grammar, vocabulary, tone, and reproducible pronunciation feedback
- Saved words and a compact spaced-review queue
- Completion, minutes, and streak tracking
- Free/Plus pricing and a clearly non-purchasable local paywall
- Local-demo entitlement and aggregate admin analytics view
- Account deletion in demo mode
- Seeded SQLite data, API tests, CORS allowlist, validation, local rate limiting, and structured non-content logging

## Technology roles

| Technology | Role in this MVP | Production direction |
| --- | --- | --- |
| React Native + Expo/EAS | Learner app and mobile builds | Cognito-authenticated HTTPS client; no embedded AWS credentials |
| Next.js | Landing page plus local-demo admin dashboard | Static export deployed to private S3 through CloudFront + WAF |
| FastAPI | Typed HTTP API and OpenAPI docs | ECS Fargate API behind API Gateway, VPC Link, and an internal ALB |
| SQLite | Zero-configuration local persistence | RDS PostgreSQL with Alembic migrations and AWS Backup |
| SQLAlchemy / Pydantic | Models, schema initialization, and validated settings/input | Alembic migrations and stronger domain constraints |
| Redis | Not needed locally | ElastiCache for shared rate limits, caches, sessions, and job coordination |
| STT/TTS/LLM | Interfaces and deterministic mocks only | Reviewed providers with consent, retention controls, cost limits |
| PostHog | Environment placeholder only; no network adapter | Consent-gated allowlisted product metadata only |
| AWS platform services | Not used for local mock mode | Cognito, Secrets Manager, SQS, S3/KMS, EventBridge, SES/SNS, CloudWatch/X-Ray, WAF, VPC, and Backup |

Start with the plain-English [technical guide and diagrams](docs/TECHNICAL_GUIDE.md). The supporting references are [architecture](docs/architecture.md), [API reference](docs/api.md), [provider design](docs/providers.md), [runbook](docs/runbook.md), [production readiness](docs/production-readiness.md), and the [AWS target design](infrastructure/aws/README.md).
