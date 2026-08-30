"""Provider contracts, catalog, and fail-closed production configuration.

Only deterministic mock implementations are executable in this repository.
Production adapters belong behind these contracts after separate review.
"""

from dataclasses import dataclass
from typing import Literal, Protocol

from .config import Settings


LLMProviderName = Literal["openai", "anthropic", "google-gemini", "aws-bedrock"]
STTProviderName = Literal["deepgram", "openai", "google-cloud", "aws-transcribe"]
TTSProviderName = Literal["elevenlabs", "openai", "google-cloud", "amazon-polly"]


@dataclass(frozen=True)
class AudioInput:
    """A local hint or private object reference; never log either raw value."""

    language: str = "zh-CN"
    transcript_hint: str | None = None
    object_key: str | None = None
    content_type: str | None = None


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    confidence: float | None


@dataclass(frozen=True)
class SpeechSynthesisRequest:
    text: str
    language: str = "zh-CN"
    voice: str | None = None


@dataclass(frozen=True)
class SynthesizedAudio:
    content_type: str
    data: bytes | None = None
    object_key: str | None = None


@dataclass(frozen=True)
class ConversationRequest:
    scenario_id: str
    learner_text: str
    turn_number: int
    learner_locale: str = "en"
    target_locale: str = "zh-CN"


@dataclass(frozen=True)
class TutorReply:
    text: str
    pinyin: str


@dataclass(frozen=True)
class PronunciationResult:
    score: float
    tones: str


class SpeechToTextProvider(Protocol):
    def transcribe(self, source: AudioInput) -> TranscriptionResult: ...


class TextToSpeechProvider(Protocol):
    def synthesize(self, request: SpeechSynthesisRequest) -> SynthesizedAudio: ...


class ConversationalLLMProvider(Protocol):
    def reply(self, request: ConversationRequest) -> TutorReply: ...


class PronunciationScoringProvider(Protocol):
    def score(self, source: AudioInput, transcript: str) -> PronunciationResult: ...


class MockSTT:
    def transcribe(self, source: AudioInput) -> TranscriptionResult:
        return TranscriptionResult(text=(source.transcript_hint or "").strip(), confidence=1.0)


class MockTTS:
    def synthesize(self, request: SpeechSynthesisRequest) -> SynthesizedAudio:
        return SynthesizedAudio(content_type="audio/mock", data=f"MOCK-AUDIO:{request.text}".encode())


class MockConversation:
    replies = {
        "introductions": TutorReply("你好！很高兴认识你。你叫什么名字？", "Nǐ hǎo! Hěn gāoxìng rènshi nǐ. Nǐ jiào shénme míngzi?"),
        "ordering-food": TutorReply("当然。你想吃什么？我们有饺子和面条。", "Dāngrán. Nǐ xiǎng chī shénme? Wǒmen yǒu jiǎozi hé miàntiáo."),
        "travel": TutorReply("地铁站在前面。你可以坐二号线。", "Dìtiě zhàn zài qiánmiàn. Nǐ kěyǐ zuò èr hào xiàn."),
        "work-meeting": TutorReply("好的，我们十点开始会议。请准备你的想法。", "Hǎode, wǒmen shí diǎn kāishǐ huìyì. Qǐng zhǔnbèi nǐ de xiǎngfǎ."),
    }

    def reply(self, request: ConversationRequest) -> TutorReply:
        if request.turn_number >= 3:
            return TutorReply("做得很好！你完成了这个练习。", "Zuò de hěn hǎo! Nǐ wánchéng le zhège liànxí.")
        return self.replies.get(request.scenario_id, self.replies["introductions"])


class MockPronunciation:
    def score(self, source: AudioInput, transcript: str) -> PronunciationResult:
        score = min(round(0.68 + (sum(map(ord, transcript)) % 25) / 100, 2), 0.92)
        tones = "Tone practice: keep the third tone low before rising." if "你" in transcript else "Tone practice: make each syllable distinct."
        return PronunciationResult(score, tones)


@dataclass(frozen=True)
class ProviderSelection:
    llm: LLMProviderName
    stt: STTProviderName
    tts: TTSProviderName
    llm_model: str
    stt_model: str
    tts_model: str


@dataclass(frozen=True)
class Providers:
    stt: SpeechToTextProvider
    tts: TextToSpeechProvider
    conversation: ConversationalLLMProvider
    pronunciation: PronunciationScoringProvider
    selection: ProviderSelection
    mode: str


def provider_selection(settings: Settings) -> ProviderSelection:
    return ProviderSelection(
        llm=settings.llm_provider,
        stt=settings.stt_provider,
        tts=settings.tts_provider,
        llm_model=settings.llm_model,
        stt_model=settings.stt_model,
        tts_model=settings.tts_model,
    )


def missing_live_configuration(settings: Settings) -> list[str]:
    """Return names of required configuration, without inspecting secret values."""

    missing: list[str] = []
    credentials = {
        "openai": (settings.openai_api_key, "MENGO_OPENAI_API_KEY or OPENAI_API_KEY"),
        "anthropic": (settings.anthropic_api_key, "MENGO_ANTHROPIC_API_KEY or ANTHROPIC_API_KEY"),
        "google-gemini": (settings.google_api_key, "MENGO_GOOGLE_API_KEY or GOOGLE_API_KEY"),
        "deepgram": (settings.deepgram_api_key, "MENGO_DEEPGRAM_API_KEY or DEEPGRAM_API_KEY"),
        "elevenlabs": (settings.elevenlabs_api_key, "MENGO_ELEVENLABS_API_KEY or ELEVENLABS_API_KEY"),
        "google-cloud": (settings.google_application_credentials, "MENGO_GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_APPLICATION_CREDENTIALS"),
    }
    for selected in (settings.llm_provider, settings.stt_provider, settings.tts_provider):
        if selected in credentials:
            value, name = credentials[selected]
            if not value:
                missing.append(name)
    for selected in (settings.llm_provider, settings.stt_provider, settings.tts_provider):
        if selected in {"aws-bedrock", "aws-transcribe", "amazon-polly"}:
            if not settings.aws_region:
                missing.append("MENGO_AWS_REGION or AWS_REGION")
            if not settings.aws_iam_auth_enabled:
                missing.append("MENGO_AWS_IAM_AUTH_ENABLED=true")
    if settings.llm_provider == "aws-bedrock" and not settings.bedrock_model_id:
        missing.append("MENGO_BEDROCK_MODEL_ID")
    if settings.tts_provider == "elevenlabs" and not settings.tts_voice_id:
        missing.append("MENGO_TTS_VOICE_ID")
    return sorted(set(missing))


def build_ai_providers(settings: Settings) -> Providers:
    if settings.ai_provider_mode == "live":
        missing = missing_live_configuration(settings)
        if missing:
            raise RuntimeError(f"Live AI mode requires explicitly configured credentials/configuration: {', '.join(missing)}")
        raise RuntimeError("Live AI mode is disabled: no reviewed provider adapter is bundled.")
    return Providers(
        stt=MockSTT(),
        tts=MockTTS(),
        conversation=MockConversation(),
        pronunciation=MockPronunciation(),
        selection=provider_selection(settings),
        mode="mock",
    )
