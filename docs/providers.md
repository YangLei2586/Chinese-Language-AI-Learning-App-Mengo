# AI and speech provider design

## Status and defaults

The checked-in application runs only deterministic mocks. It does **not** import vendor SDKs, make network calls, accept audio, or activate a paid provider. `MENGO_AI_PROVIDER_MODE=mock` is mandatory for normal local development and CI.

The production recommendations below are defaults for an English-speaking Mandarin-learning MVP, not vendor commitments:

| Capability | Recommended primary | AWS-native option | Additional supported configuration choices |
| --- | --- | --- | --- |
| Conversational LLM | OpenAI GPT (`openai`, `gpt-4.1-mini`) | Amazon Bedrock (`aws-bedrock`, model ID chosen per approved region) | Anthropic Claude (`anthropic`), Google Gemini (`google-gemini`) |
| Mandarin STT | Deepgram (`deepgram`, `nova-3`) | AWS Transcribe (`aws-transcribe`) | OpenAI transcription (`openai`), Google Cloud Speech-to-Text (`google-cloud`) |
| Mandarin TTS | ElevenLabs (`elevenlabs`, `eleven_multilingual_v2`) | Amazon Polly (`amazon-polly`) | OpenAI TTS (`openai`), Google Cloud Text-to-Speech (`google-cloud`) |

The suggested models and names are configuration defaults, not a quality claim or fixed pricing guarantee. Product, security, and language-quality evaluation must confirm current model availability, Mandarin performance, data handling, latency, and price before a deployment. Pronunciation scoring remains a separate `PronunciationScoringProvider` contract and must be validated against qualified Mandarin pedagogy; it must not be represented as an objective assessment.

## Abstractions

`apps/api/app/providers.py` isolates app logic from a vendor:

- `AudioInput` carries a local transcript hint **or** a private object reference, language, and content type.
- `SpeechToTextProvider` returns `TranscriptionResult`; a production implementation reads an authorized private object and returns text plus an optional confidence measure.
- `TextToSpeechProvider` accepts `SpeechSynthesisRequest` and returns either short-lived bytes or a protected object reference.
- `ConversationalLLMProvider` receives a bounded `ConversationRequest` containing scenario, learner text, locales, and turn number and returns a `TutorReply`.
- `PronunciationScoringProvider` receives an audio reference plus confirmed transcript and returns a bounded score/hint.
- `ProviderSelection` records configured provider/model names for safe operational metadata; it must not record prompts, transcript text, audio, or credentials.

The mock classes implement the same contracts and produce stable results for local testing. A production adapter must be a new, reviewed module; it must not be added by changing a model name or environment value alone.

## Configuration

`apps/api/.env.example` and root `.env.example` contain blank placeholders only:

```dotenv
MENGO_AI_PROVIDER_MODE=mock
MENGO_LLM_PROVIDER=openai
MENGO_STT_PROVIDER=deepgram
MENGO_TTS_PROVIDER=elevenlabs
MENGO_LLM_MODEL=gpt-4.1-mini
MENGO_STT_MODEL=nova-3
MENGO_TTS_MODEL=eleven_multilingual_v2
MENGO_TTS_VOICE_ID=
MENGO_OPENAI_API_KEY=
MENGO_ANTHROPIC_API_KEY=
MENGO_GOOGLE_API_KEY=
MENGO_GOOGLE_APPLICATION_CREDENTIALS=
MENGO_DEEPGRAM_API_KEY=
MENGO_ELEVENLABS_API_KEY=
MENGO_AWS_REGION=
MENGO_AWS_IAM_AUTH_ENABLED=false
MENGO_BEDROCK_MODEL_ID=
```

Allowed selection values are:

| Variable | Values |
| --- | --- |
| `MENGO_LLM_PROVIDER` | `openai`, `anthropic`, `google-gemini`, `aws-bedrock` |
| `MENGO_STT_PROVIDER` | `deepgram`, `openai`, `google-cloud`, `aws-transcribe` |
| `MENGO_TTS_PROVIDER` | `elevenlabs`, `openai`, `google-cloud`, `amazon-polly` |

When `MENGO_AI_PROVIDER_MODE=live`, startup first verifies that the selected non-AWS providers have their matching explicitly configured secret and that AWS-native selections have a region plus explicit IAM-workload configuration. Bedrock additionally requires a model ID; ElevenLabs requires a chosen voice ID. It then still fails closed because no reviewed live adapter is bundled. This prevents a model/provider setting from silently causing a paid request.

In AWS production, non-AWS vendor secrets are stored only in Secrets Manager and injected into ECS tasks through scoped task roles. Bedrock, Transcribe, and Polly use an ECS task role and `MENGO_AWS_REGION`, not `AWS_ACCESS_KEY_ID` or other static keys. Google credentials, if approved, require workload identity or a Secrets Manager-managed reference; never package a service-account file in an image or Expo/EAS app.

## Privacy, consent, and data minimization

Before enabling audio, obtain explicit, revocable voice-processing consent that identifies the selected processor(s), purpose, retention, transfer region, and deletion route. Consent and provider selection must be available to the worker before an audio job is queued.

- Private SSE-KMS S3 stores raw audio only after consent, with presigned URLs scoped to one user/object and an approved lifecycle (initial proposal: expire raw audio after 7 days and incomplete uploads after 1 day).
- Send the minimum necessary request data to a provider. Do not send a learner profile, analytics identifier, payment data, unrelated transcript history, or audio to a provider that does not need it.
- Never put raw audio, transcript text, prompt content, generated speech, API keys, or user-identifying values in PostHog, SQS metadata, CloudWatch logs, X-Ray annotations, crash reports, or metrics.
- Honor account deletion by cancelling jobs, deleting eligible source/derived objects, and following the approved provider deletion/retention process. Obtain DPAs and assess data residency and subprocessors.
- Require moderation, prompt-injection controls, output safety evaluation, and clear learner messaging before LLM responses are shown.

## Cost, latency, and fallback policy

Audio operations have variable cost and network latency. Set a maximum audio duration, upload size/type allowlist, per-user quota, provider-specific concurrency limit, daily/monthly budget alarm, and an absolute circuit breaker before rollout. Emit only allowlisted counters such as provider family, result status, duration bucket, and token/audio-second bucket.

| Path | Latency approach | Failure behavior |
| --- | --- | --- |
| LLM conversation | Keep the scenario prompt/context bounded; set short connect/read timeouts and a per-turn token cap. | Return a retryable, content-free error. Do not invent feedback. |
| STT/pronunciation | Queue longer audio through SQS and notify/poll for completion; use a short path only after load testing. | Retry idempotently with a DLQ; preserve no more source data than retention allows. |
| TTS | Cache approved, non-personal static lesson prompts where licensing permits; generate learner-specific speech asynchronously. | Show transcript/pinyin first; audio is an enhancement, not a blocker. |

Potential fallbacks are evaluated pairs, not automatic hidden routing: OpenAI GPT → approved Bedrock/Claude/Gemini; Deepgram → AWS Transcribe; ElevenLabs → Amazon Polly. A fallback may be used only when the learner has consented to that processor, the region/retention policy permits it, vendor terms and Mandarin quality have been tested, and the chosen provider is included in the current incident policy. Otherwise fail visibly and safely. Track spend and p95 latency separately for every approved provider/model/voice and regularly re-evaluate the primary choices.

## Adapter acceptance checklist

- [ ] Pin and scan each vendor SDK in a dedicated adapter dependency group; do not add it to mock-only local installs unnecessarily.
- [ ] Authenticate using Secrets Manager references or workload identity, verify egress allowlists, and redact SDK errors.
- [ ] Contract-test each adapter with recorded/synthetic non-user fixtures and test timeout, cancellation, retry, idempotency, and fallback behavior.
- [ ] Complete Mandarin language-quality, accessibility, regional, privacy, security, cost, legal, and procurement review.
- [ ] Update consent copy, data inventory, retention/deletion jobs, incident runbook, and user-facing availability messaging before activation.
