# Limitations and production readiness checklist

## Current limitations

- Demo header identity is **not** authentication, authorization, or multi-tenant protection.
- SQLite automatic schema initialization has no migration history, backup, concurrency, or encryption strategy.
- Tutor, STT, TTS, pronunciation, analytics, and entitlement providers are deterministic mocks; TTS exposes an interface but no audio endpoint because this MVP does not handle audio.
- Feedback is heuristic and must not be presented as an objective pronunciation assessment or educational guarantee.
- The dashboard is local-demo only and only looks protected; it is not an admin security boundary.
- Rate limiting is in memory and per process, suitable only for local development.
- Pricing UI cannot accept payments. Apple App Store/Google Play billing and RevenueCat require real production credentials plus server-side receipt validation.

## Required before production

### AWS target and infrastructure

Mengo's documented production target is AWS. The design in [infrastructure/aws/README.md](../infrastructure/aws/README.md) is not a deployed environment and does not require AWS credentials. It selects CloudFront + private S3 for the static Next.js export and API Gateway HTTP API → VPC Link → internal ALB → ECS Fargate for the FastAPI API and asynchronous workers.

- [ ] Implement reviewed Terraform modules with separately protected staging/production state, policy checks, resource tags, and short-lived CI OIDC roles. Do not store credentials, account IDs, state, or `.tfvars` secrets in this repository.
- [ ] Create a multi-AZ VPC: only CloudFront/API Gateway are public; ALB, ECS, RDS, Redis, and media services use private subnets and least-privilege security groups.
- [ ] Attach separate AWS WAF Web ACLs to CloudFront and regional API Gateway, establish rate/abuse rules, and validate false-positive handling.
- [ ] Deploy the static Next.js export to a private S3 bucket through CloudFront. Enforce bucket public-access blocks, TLS, cache invalidation discipline, and origin-only access.
- [ ] Deploy immutable, scanned/signed FastAPI and worker image digests from ECR to ECS Fargate. API Gateway must use a Cognito JWT authorizer and VPC Link, and ECS must be reachable only from the internal ALB.
- [ ] Migrate to RDS PostgreSQL using Alembic. Configure Multi-AZ as required, encryption, connection management, AWS Backup plans, restore drills, and approved RPO/RTO.
- [ ] Provision ElastiCache Redis only for ephemeral caches, distributed rate limits, sessions, and queue coordination; protect it in private subnets and never treat it as durable learner data.
- [ ] Store runtime secrets exclusively in Secrets Manager with KMS and narrowly scoped task roles. Rotate, audit, and never expose secret values to web or Expo/EAS builds.
- [ ] Use CloudWatch structured redacted logs, metrics/alarms, retention controls, and X-Ray traces. Audio, transcript content, tokens, secrets, and payment details must be excluded.

### Identity, authorization, and privacy

- [ ] Replace demo headers with Cognito User Pools/OIDC, API Gateway JWT validation, secure sessions, and role-based authorization.
- [ ] Enforce tenant isolation, audit logs, admin SSO, CSRF strategy where applicable, and account-data export/deletion workflows.
- [ ] Produce a privacy notice, consent UX, age/region assessment, retention schedule, DPIA/legal review, and data processor agreements.
- [ ] Encrypt data in transit and at rest; manage secrets with a managed secret store—not environment files in source control.

### AI and speech

- [ ] Implement only a reviewed adapter from the [provider design](providers.md): the proposed primary set is OpenAI GPT, Deepgram, and ElevenLabs; Bedrock/Transcribe/Polly are AWS-native alternatives. Revalidate vendor/model availability, Mandarin quality, pricing, terms, and regional suitability before selection.
- [ ] Obtain explicit audio/voice consent. Use private SSE-KMS S3 with scoped presigned uploads, public-access blocks, and an approved lifecycle (initial proposal: delete raw audio after 7 days; abort incomplete uploads after 1 day).
- [ ] Submit opaque object keys and minimal metadata to SQS STT/TTS/feedback queues; run bounded-retry ECS workers with DLQs. Do not put audio or transcript text in queue payloads, logs, X-Ray, or analytics.
- [ ] Implement account deletion to cancel outstanding jobs, delete eligible audio, and remove derived records according to an approved retention policy.
- [ ] Add prompt-injection defenses, output moderation, language-quality evaluation, provider outage fallback, usage budgets, and human escalation policy.
- [ ] Apply explicit provider-specific timeout, token/audio-size, quota, concurrency, budget-alarm, circuit-breaker, and consent-aware fallback policies. A provider fallback must not silently introduce a new processor or region.
- [ ] Validate learning outcomes with qualified educators; describe feedback as assistive, not authoritative.

### Platform and payments

- [ ] Use Apple/Google native billing or RevenueCat with production keys stored server-side, webhook verification, and server-side receipt validation. Never trust a client plan flag.
- [ ] Implement secure media upload handling, virus/malware controls where applicable, and background processing.
- [ ] Continue using Expo/EAS for mobile builds. Mobile apps authenticate with Cognito and call AWS APIs over HTTPS; do not place AWS long-lived credentials, Secrets Manager values, or direct RDS/Redis access in a mobile build.

### Analytics and operations

- [ ] Define an analytics allowlist, consent controls, sampling/retention, and a reviewed PostHog adapter. Never send audio, transcript text, PII, payment data, or identifiers that are unnecessary for product measurement.
- [ ] Use EventBridge Scheduler/rules to enqueue consent-gated reminders and a separate delivery worker for SES email or an approved SNS mobile-push integration. Track delivery safely and honor opt-out preferences.
- [ ] Add centralized structured logging/redaction, health checks, metrics, alerts, incident response, penetration testing, dependency/SBOM scanning, and CloudWatch/X-Ray operating procedures.
- [ ] Load test API/provider failures, test accessibility/localization, and complete App Store/Play Store compliance and review requirements.
