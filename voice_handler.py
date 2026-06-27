"""
Voice Handler Module
Provides Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities
with multiple provider options for different cost/quality tiers.
"""

import os
import tempfile
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, List, Dict
import asyncio

# Import voice processing libraries
from openai import OpenAI
import whisper
import edge_tts
from gtts import gTTS


# ============================================================================
# Configuration and Cost Tiers
# ============================================================================

class VoiceConfig:
    """Configuration for voice providers and their characteristics."""

    # Language definitions with their codes and display names
    LANGUAGES = {
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "German": "de",
        "Italian": "it",
        "Portuguese": "pt",
        "Dutch": "nl",
        "Russian": "ru",
        "Chinese (Mandarin)": "zh",
        "Japanese": "ja",
        "Korean": "ko",
        "Arabic": "ar",
        "Hindi": "hi",
        "Turkish": "tr",
        "Polish": "pl",
        "Swedish": "sv",
        "Danish": "da",
        "Norwegian": "no",
        "Finnish": "fi",
        "Greek": "el",
        "Czech": "cs",
        "Romanian": "ro",
        "Hungarian": "hu",
        "Thai": "th",
        "Vietnamese": "vi",
        "Indonesian": "id",
        "Malay": "ms",
        "Filipino": "fil",
        "Hebrew": "he",
        "Ukrainian": "uk",
    }

    # Multilingual Edge TTS voices organized by language
    EDGE_TTS_VOICES = {
        "en": ["en-US-JennyNeural", "en-US-GuyNeural", "en-US-AriaNeural", "en-GB-SoniaNeural", "en-GB-RyanNeural", "en-AU-NatashaNeural"],
        "es": ["es-ES-ElviraNeural", "es-ES-AlvaroNeural", "es-MX-DaliaNeural", "es-MX-JorgeNeural", "es-AR-ElenaNeural"],
        "fr": ["fr-FR-DeniseNeural", "fr-FR-HenriNeural", "fr-CA-SylvieNeural", "fr-CA-AntoineNeural", "fr-BE-CharlineNeural"],
        "de": ["de-DE-KatjaNeural", "de-DE-ConradNeural", "de-AT-IngridNeural", "de-CH-LeniNeural"],
        "it": ["it-IT-ElsaNeural", "it-IT-DiegoNeural", "it-IT-IsabellaNeural"],
        "pt": ["pt-BR-FranciscaNeural", "pt-BR-AntonioNeural", "pt-PT-RaquelNeural", "pt-PT-DuarteNeural"],
        "nl": ["nl-NL-ColetteNeural", "nl-NL-MaartenNeural", "nl-BE-DenaNeural"],
        "ru": ["ru-RU-SvetlanaNeural", "ru-RU-DmitryNeural"],
        "zh": ["zh-CN-XiaoxiaoNeural", "zh-CN-YunxiNeural", "zh-TW-HsiaoChenNeural", "zh-HK-HiuMaanNeural"],
        "ja": ["ja-JP-NanamiNeural", "ja-JP-KeitaNeural"],
        "ko": ["ko-KR-SunHiNeural", "ko-KR-InJoonNeural"],
        "ar": ["ar-SA-ZariyahNeural", "ar-SA-HamedNeural", "ar-EG-SalmaNeural"],
        "hi": ["hi-IN-SwaraNeural", "hi-IN-MadhurNeural"],
        "tr": ["tr-TR-EmelNeural", "tr-TR-AhmetNeural"],
        "pl": ["pl-PL-ZofiaNeural", "pl-PL-MarekNeural"],
        "sv": ["sv-SE-SofieNeural", "sv-SE-MattiasNeural"],
        "da": ["da-DK-ChristelNeural", "da-DK-JeppeNeural"],
        "no": ["nb-NO-PernilleNeural", "nb-NO-FinnNeural"],
        "fi": ["fi-FI-NooraNeural", "fi-FI-HarriNeural"],
        "el": ["el-GR-AthinaNeural", "el-GR-NestorasNeural"],
        "cs": ["cs-CZ-VlastaNeural", "cs-CZ-AntoninNeural"],
        "ro": ["ro-RO-AlinaNeural", "ro-RO-EmilNeural"],
        "hu": ["hu-HU-NoemiNeural", "hu-HU-TamasNeural"],
        "th": ["th-TH-PremwadeeNeural", "th-TH-NiwatNeural"],
        "vi": ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"],
        "id": ["id-ID-GadisNeural", "id-ID-ArdiNeural"],
        "ms": ["ms-MY-YasminNeural", "ms-MY-OsmanNeural"],
        "fil": ["fil-PH-BlessicaNeural", "fil-PH-AngeloNeural"],
        "he": ["he-IL-HilaNeural", "he-IL-AvriNeural"],
        "uk": ["uk-UA-PolinaNeural", "uk-UA-OstapNeural"],
    }

    # STT Provider definitions
    STT_PROVIDERS = {
        "OpenAI Whisper API": {
            "id": "openai_whisper",
            "cost_tier": "medium",
            "cost_per_minute": 0.006,
            "requires_api_key": True,
        },
        "Local Whisper (Tiny)": {
            "id": "local_whisper_tiny",
            "cost_tier": "free",
            "cost_per_minute": 0.0,
            "requires_api_key": False,
        },
        "Local Whisper (Base)": {
            "id": "local_whisper_base",
            "cost_tier": "free",
            "cost_per_minute": 0.0,
            "requires_api_key": False,
        },
    }

    # TTS Provider definitions
    TTS_PROVIDERS = {
        "Edge-TTS (Free)": {
            "id": "edge_tts",
            "cost_tier": "free",
            "cost_per_1k_chars": 0.0,
            "requires_api_key": False,
            "voices": []  # Will be populated dynamically based on language
        },
        "OpenAI TTS": {
            "id": "openai_tts",
            "cost_tier": "medium",
            "cost_per_1k_chars": 0.015,
            "requires_api_key": True,
            "voices": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        },
        "gTTS (Free)": {
            "id": "gtts",
            "cost_tier": "free",
            "cost_per_1k_chars": 0.0,
            "requires_api_key": False,
            "voices": ["default"]
        },
    }

    # Default selections
    DEFAULT_STT = "OpenAI Whisper API"
    DEFAULT_TTS = "gTTS (Free)"  # More reliable on cloud platforms like HF Spaces
    DEFAULT_TTS_VOICE = "default"
    DEFAULT_LANGUAGE = "English"


# ============================================================================
# Abstract Base Classes
# ============================================================================

class STTProvider(ABC):
    """Abstract base class for Speech-to-Text providers."""

    @abstractmethod
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file
            language: Optional ISO-639-1 code (e.g. "de") to constrain detection

        Returns:
            Transcribed text
        """
        pass


class TTSProvider(ABC):
    """Abstract base class for Text-to-Speech providers."""

    @abstractmethod
    def synthesize(self, text: str, output_path: Optional[str] = None) -> str:
        """
        Synthesize text to speech.

        Args:
            text: Text to convert to speech
            output_path: Optional path to save audio file

        Returns:
            Path to generated audio file
        """
        pass

    @abstractmethod
    def get_available_voices(self) -> List[str]:
        """Get list of available voices for this provider."""
        pass


# ============================================================================
# STT Provider Implementations
# ============================================================================

class OpenAIWhisperSTT(STTProvider):
    """OpenAI Whisper API implementation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=self.api_key)

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        """Transcribe audio using OpenAI Whisper API."""
        try:
            kwargs = {"model": "whisper-1"}
            if language:
                # Constrain detection to the practice language so Whisper doesn't
                # mis-detect (and hallucinate) on short or accented utterances.
                kwargs["language"] = language
            with open(audio_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    file=audio_file,
                    **kwargs
                )
            return transcript.text
        except Exception as e:
            raise Exception(f"OpenAI Whisper transcription failed: {str(e)}")


class LocalWhisperSTT(STTProvider):
    """Local Whisper model implementation."""

    def __init__(self, model_size: str = "base"):
        """
        Initialize local Whisper model.

        Args:
            model_size: Model size (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None

    def _load_model(self):
        """Lazy load the model."""
        if self.model is None:
            self.model = whisper.load_model(self.model_size)

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        """Transcribe audio using local Whisper model."""
        self._load_model()
        try:
            result = self.model.transcribe(audio_path, language=language)
            return result["text"]
        except Exception as e:
            raise Exception(f"Local Whisper transcription failed: {str(e)}")


# ============================================================================
# TTS Provider Implementations
# ============================================================================

class EdgeTTSProvider(TTSProvider):
    """Microsoft Edge TTS implementation (free)."""

    def __init__(self, voice: str = "en-US-JennyNeural"):
        self.voice = voice

    def synthesize(self, text: str, output_path: Optional[str] = None) -> str:
        """Synthesize speech using Edge TTS."""

        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.mp3")

        try:
            # Edge TTS requires async
            async def _synthesize():
                communicate = edge_tts.Communicate(text, self.voice)
                await communicate.save(output_path)

            asyncio.run(_synthesize())
            return output_path
        except Exception as e:
            raise Exception(f"Edge TTS synthesis failed: {str(e)}")

    def get_available_voices(self) -> List[str]:
        """Get available Edge TTS voices."""
        return VoiceConfig.TTS_PROVIDERS["Edge-TTS (Free)"]["voices"]


class OpenAITTSProvider(TTSProvider):
    """OpenAI TTS implementation."""

    def __init__(self, voice: str = "nova", api_key: Optional[str] = None):
        self.voice = voice
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=self.api_key)

    def synthesize(self, text: str, output_path: Optional[str] = None) -> str:
        """Synthesize speech using OpenAI TTS."""
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.mp3")

        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=self.voice,
                input=text
            )
            response.stream_to_file(output_path)
            return output_path
        except Exception as e:
            raise Exception(f"OpenAI TTS synthesis failed: {str(e)}")

    def get_available_voices(self) -> List[str]:
        """Get available OpenAI TTS voices."""
        return VoiceConfig.TTS_PROVIDERS["OpenAI TTS"]["voices"]


class GTTSProvider(TTSProvider):
    """Google TTS implementation (free, basic quality)."""

    def __init__(self, voice: str = "default", language: str = "en"):
        self.voice = voice
        self.language = language

    def synthesize(self, text: str, output_path: Optional[str] = None) -> str:
        """Synthesize speech using gTTS."""

        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.mp3")

        try:
            tts = gTTS(text=text, lang=self.language)
            tts.save(output_path)
            return output_path
        except Exception as e:
            raise Exception(f"gTTS synthesis failed: {str(e)}")

    def get_available_voices(self) -> List[str]:
        """Get available gTTS voices."""
        return VoiceConfig.TTS_PROVIDERS["gTTS (Free)"]["voices"]


# ============================================================================
# Factory Functions
# ============================================================================

def create_stt_provider(provider_name: str) -> STTProvider:
    """
    Create an STT provider instance.

    Args:
        provider_name: Name of the provider (from VoiceConfig.STT_PROVIDERS)

    Returns:
        STTProvider instance
    """
    provider_id = VoiceConfig.STT_PROVIDERS[provider_name]["id"]

    if provider_id == "openai_whisper":
        return OpenAIWhisperSTT()
    elif provider_id == "local_whisper_tiny":
        return LocalWhisperSTT(model_size="tiny")
    elif provider_id == "local_whisper_base":
        return LocalWhisperSTT(model_size="base")
    else:
        raise ValueError(f"Unknown STT provider: {provider_name}")


def create_tts_provider(provider_name: str, voice: Optional[str] = None, language: str = "en") -> TTSProvider:
    """
    Create a TTS provider instance.

    Args:
        provider_name: Name of the provider (from VoiceConfig.TTS_PROVIDERS)
        voice: Optional voice name
        language: Language code (ISO 639-1)

    Returns:
        TTSProvider instance
    """
    provider_id = VoiceConfig.TTS_PROVIDERS[provider_name]["id"]
    provider_info = VoiceConfig.TTS_PROVIDERS[provider_name]

    # Use default voice if not specified
    if voice is None:
        voice = provider_info["voices"][0] if provider_info["voices"] else None

    if provider_id == "edge_tts":
        return EdgeTTSProvider(voice=voice)
    elif provider_id == "openai_tts":
        return OpenAITTSProvider(voice=voice)
    elif provider_id == "gtts":
        return GTTSProvider(voice=voice, language=language)
    else:
        raise ValueError(f"Unknown TTS provider: {provider_name}")


def get_available_stt_providers() -> List[str]:
    """Get list of available STT provider names."""
    return list(VoiceConfig.STT_PROVIDERS.keys())


def get_available_tts_providers() -> List[str]:
    """Get list of available TTS provider names."""
    return list(VoiceConfig.TTS_PROVIDERS.keys())


def get_voices_for_provider(provider_name: str, language: str = "en") -> List[str]:
    """
    Get available voices for a TTS provider, optionally filtered by language.

    Args:
        provider_name: Name of the provider
        language: Language code (ISO 639-1) for filtering voices

    Returns:
        List of available voices
    """
    if provider_name not in VoiceConfig.TTS_PROVIDERS:
        return []

    provider_id = VoiceConfig.TTS_PROVIDERS[provider_name]["id"]

    # For Edge TTS, return language-specific voices
    if provider_id == "edge_tts":
        return VoiceConfig.EDGE_TTS_VOICES.get(language, VoiceConfig.EDGE_TTS_VOICES.get("en", []))

    # For other providers, return all voices
    return VoiceConfig.TTS_PROVIDERS[provider_name]["voices"]


def get_provider_info(provider_name: str, provider_type: str = "tts") -> Dict:
    """
    Get information about a provider.

    Args:
        provider_name: Name of the provider
        provider_type: "stt" or "tts"

    Returns:
        Provider information dictionary
    """
    if provider_type == "tts":
        return VoiceConfig.TTS_PROVIDERS.get(provider_name, {})
    else:
        return VoiceConfig.STT_PROVIDERS.get(provider_name, {})


def get_available_languages() -> List[str]:
    """Get list of available language names."""
    return list(VoiceConfig.LANGUAGES.keys())


def get_language_code(language_name: str) -> str:
    """
    Get language code from language name.

    Args:
        language_name: Display name of the language (e.g., "English")

    Returns:
        Language code (e.g., "en")
    """
    return VoiceConfig.LANGUAGES.get(language_name, "en")


def get_default_voice_for_language(language_name: str, provider_name: str = "Edge-TTS (Free)") -> str:
    """
    Get the default voice for a specific language and provider.

    Args:
        language_name: Display name of the language
        provider_name: Name of the TTS provider

    Returns:
        Default voice ID for the language
    """
    language_code = get_language_code(language_name)
    voices = get_voices_for_provider(provider_name, language_code)

    if voices:
        return voices[0]

    # Fallback to English if language not supported
    return VoiceConfig.DEFAULT_TTS_VOICE
