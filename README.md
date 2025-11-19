---
title: Language_Tutor
app_file: language_tutor.py
sdk: gradio
sdk_version: 5.49.1
---
# 🌍 Language Tutor - AI-Powered Multilingual Learning

An AI-powered conversational chatbot designed to help users practice speaking foreign languages in an interactive, adaptive environment. Powered by the **Apertus-70B-Instruct-2509** model, which is trained on 1000+ languages, this application provides immersive language learning with voice support.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Gradio](https://img.shields.io/badge/Gradio-UI-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🆕 What's New

- **Auto-Transcription:** Voice recordings automatically transcribe when you stop - no extra button needed!
- **Translation Control:** Toggle native language hints on/off for immersive or assisted learning
- **German Default:** Application now defaults to German language learning
- **Streamlined UI:** Organized settings (Language → Voice → Parameters) for better user flow

## ✨ Features

- 🗣️ **30+ Supported Languages** - Practice any of 30 major world languages
- 🎯 **Personalized Learning** - Select your native language and target language
- 🤖 **AI Tutor** - Powered by Apertus-70B, trained on 1000+ languages
- 🎤 **Auto-Transcription** - Voice input automatically transcribes when you stop recording
- 🔊 **Voice Output (TTS)** - Hear responses with native pronunciation
- 🌐 **Multilingual Voices** - Automatic voice matching for target language
- 📝 **Smart Prompts** - Auto-generated teaching prompts based on language pair
- 💡 **Adaptive Teaching** - Provides translations, corrections, and cultural context
- 🔄 **Translation Control** - Toggle native language hints on/off for immersive learning

## 📋 Table of Contents

- [Supported Languages](#supported-languages)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Code Structure](#code-structure)
- [API Providers](#api-providers)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🌐 Supported Languages

The application supports 30 languages with native TTS voices:

| Language | Code | TTS Voices Available |
|----------|------|---------------------|
| English | en | 6 voices (US, GB, AU) |
| Spanish | es | 5 voices (ES, MX, AR) |
| French | fr | 5 voices (FR, CA, BE) |
| German | de | 4 voices (DE, AT, CH) |
| Italian | it | 3 voices |
| Portuguese | pt | 4 voices (BR, PT) |
| Dutch | nl | 3 voices (NL, BE) |
| Russian | ru | 2 voices |
| Chinese (Mandarin) | zh | 4 voices (CN, TW, HK) |
| Japanese | ja | 2 voices |
| Korean | ko | 2 voices |
| Arabic | ar | 3 voices (SA, EG) |
| Hindi | hi | 2 voices |
| Turkish | tr | 2 voices |
| Polish | pl | 2 voices |
| Swedish | sv | 2 voices |
| Danish | da | 2 voices |
| Norwegian | no | 2 voices |
| Finnish | fi | 2 voices |
| Greek | el | 2 voices |
| Czech | cs | 2 voices |
| Romanian | ro | 2 voices |
| Hungarian | hu | 2 voices |
| Thai | th | 2 voices |
| Vietnamese | vi | 2 voices |
| Indonesian | id | 2 voices |
| Malay | ms | 2 voices |
| Filipino | fil | 2 voices |
| Hebrew | he | 2 voices |
| Ukrainian | uk | 2 voices |

## 🏗️ Architecture

The application consists of three main components:

```
┌─────────────────────────────────────────────────┐
│           Gradio Web Interface (UI)             │
│  - Language Selection                           │
│  - Chat Interface                               │
│  - Voice Controls                               │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│        Language Tutor Core (language_tutor.py)  │
│  - Message Formatting                           │
│  - System Prompt Generation                     │
│  - Hugging Face API Integration                 │
└─────────────────────┬───────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────┐
│        Voice Handler (voice_handler.py)         │
│  - STT Providers (Whisper, Local)               │
│  - TTS Providers (Edge-TTS, OpenAI, gTTS)       │
│  - Language/Voice Mapping                       │
└─────────────────────────────────────────────────┘
```

## 📦 Requirements

### System Requirements

- **UV** - Fast Python package manager (installation instructions below)
- Python 3.8 or higher (UV will manage this)
- Internet connection (for Hugging Face API and cloud TTS/STT)
- Microphone (optional, for voice input)
- Speakers/Headphones (optional, for voice output)

### Python Dependencies

```
gradio>=4.0.0
huggingface_hub>=0.19.0
python-dotenv>=1.0.0
openai>=1.0.0
edge-tts>=6.1.0
openai-whisper>=20231117
gtts>=2.5.0
```

## 🚀 Installation

### Prerequisites

This project uses **UV** - an extremely fast Python package manager and project manager written in Rust.

**Why UV?**
- ⚡ 10-100x faster than pip
- 🔒 Automatic virtual environment management
- 📦 Reproducible builds with `uv.lock`
- 🎯 Compatible with pip and PyPI

**Install UV:**

```bash
# macOS/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip (if you already have Python):
pip install uv

# Verify installation:
uv --version
```

### Step 1: Clone or Download the Repository

```bash
cd /path/to/language_tutor
```

### Step 2: Set Up Environment with UV

UV will automatically create a virtual environment and install all dependencies:

```bash
# Install dependencies from requirements.txt
uv pip install -r requirements.txt

# Or if using pyproject.toml (recommended):
uv sync
```

### Step 3: Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Hugging Face API Token (required)
HF_TOKEN=your_huggingface_token_here

# OpenAI API Key (optional, only if using OpenAI providers)
OPENAI_API_KEY=your_openai_api_key_here
```

**Getting a Hugging Face Token:**
1. Visit https://huggingface.co/settings/tokens
2. Create a new token with "Read" access
3. Copy the token to your `.env` file

Or use the CLI:
```bash
huggingface-cli login
```

## ⚙️ Configuration

### Voice Provider Options

#### Speech-to-Text (STT) Providers

1. **OpenAI Whisper API** (Recommended)
   - Cost: $0.006 per minute
   - Quality: High
   - Requires: OpenAI API key

2. **Local Whisper (Tiny)**
   - Cost: Free
   - Quality: Good for simple conversations
   - Requires: Local processing

3. **Local Whisper (Base)**
   - Cost: Free
   - Quality: Better, but slower
   - Requires: Local processing

#### Text-to-Speech (TTS) Providers

1. **Edge-TTS** (Recommended)
   - Cost: Free
   - Quality: High
   - Languages: 30+ with native voices
   - Requires: Internet connection

2. **OpenAI TTS**
   - Cost: $0.015 per 1K characters
   - Quality: Very High
   - Languages: Limited (English-focused)
   - Requires: OpenAI API key

3. **gTTS (Google TTS)**
   - Cost: Free
   - Quality: Basic
   - Languages: 30+ supported
   - Requires: Internet connection

### Translation Control Feature

The **"Enable Native Language Hints"** checkbox controls how the AI tutor communicates with you:

#### Enabled (Default - Recommended for Beginners)
- AI provides translations in parentheses: `"Guten Morgen! (Good morning!)"`
- Offers explanations when you seem confused
- Helps you understand new vocabulary and grammar
- Builds confidence while learning

#### Disabled (Full Immersion Mode)
- AI responds entirely in target language
- No automatic translations or hints
- Forces you to think in the target language
- Only translates when you explicitly ask
- Ideal for intermediate/advanced learners

### Customizing System Prompts

The system prompt is automatically generated based on:
- Your native language selection
- Your target language selection (defaults to German)
- Translation hints preference (enabled/disabled)

The prompt updates automatically when you change any of these settings. Advanced users can manually edit the system prompt (currently hidden in UI, but functional in backend).

## 🎮 Usage

### Starting the Application

```bash
# Using UV (recommended):
uv run python language_tutor.py

# Or if you've activated the virtual environment:
python language_tutor.py
```

The application will launch a web interface at `http://127.0.0.1:7860`

### Basic Workflow

1. **Configure Language Settings**
   - Choose your native language (for explanations)
   - Choose the language you want to practice (defaults to German)
   - Toggle "Enable Native Language Hints" for translations in parentheses
   - The system prompt auto-generates based on your selections

2. **Configure Voice Settings** (Optional)
   - Enable Voice Input (STT) - recording auto-transcribes when you stop
   - Enable Voice Output (TTS) to hear responses
   - Select preferred voice provider and voice style
   - Voice automatically matches your target language

3. **Start Learning**
   - Type your message or click the microphone to record
   - Voice recordings auto-transcribe when you stop (no extra button needed)
   - The AI tutor responds primarily in the target language
   - Receive corrections, explanations, and cultural context

4. **Customize Your Experience**
   - Toggle native language hints for full immersion or beginner support
   - Adjust generation parameters (temperature, max tokens)
   - Change voice providers/styles for different accents

### Example Conversations

#### Example 1: English → German (With Native Language Hints)

**You:** "Hello! I want to practice ordering food at a restaurant."

**AI Tutor:** "Hallo! Perfekt, lass uns das üben. (Hello! Perfect, let's practice.)

Stell dir vor, du bist in einem deutschen Restaurant. Ich bin der Kellner. (Imagine you're in a German restaurant. I'm the waiter.)

Was möchtest du bestellen? (What would you like to order?)"

**You:** "Ich möchte eine Pizza, bitte."

**AI Tutor:** "Sehr gut! Dein Satz ist korrekt. (Very good! Your sentence is correct.)

In Deutschland würde man auch sagen: 'Ich hätte gerne eine Pizza' (I would like a pizza - more polite).

Und zum Trinken? Was möchtest du trinken? (And to drink? What would you like to drink?)"

#### Example 2: English → German (Full Immersion Mode - Hints Disabled)

**You:** "Hallo! Wie geht es dir?"

**AI Tutor:** "Hallo! Mir geht es sehr gut, danke! Und dir?

Möchtest du heute über ein bestimmtes Thema sprechen? Vielleicht Reisen, Essen, oder Arbeit?"

**You:** "Can you translate that?"

**AI Tutor:** "Of course! I said: Hello! I'm doing very well, thanks! And you? Would you like to talk about a specific topic today? Maybe travel, food, or work?"

## 📂 Code Structure

### Main Files

#### `language_tutor.py`
Main application file containing the Gradio interface and core logic.

**Key Functions:**

- `create_language_tutor_prompt(native_language, target_language, enable_translations)` - Generates intelligent system prompts with optional translation hints
- `format_messages(message, chat_history, system_prompt)` - Formats conversation for the LLM
- `transcribe_audio(audio_path, stt_provider_name)` - Converts speech to text (auto-triggered on recording stop)
- `synthesize_speech(text, tts_provider_name, tts_voice, target_language)` - Converts text to speech with language awareness
- `chat(...)` - Main chat function that handles LLM inference
- `update_voice_dropdown(tts_provider_name, target_language)` - Dynamically updates voice options
- `process_voice_input(audio, stt_provider_name)` - Processes and transcribes voice input automatically

**UI Organization:**
- **Language Settings** - Native language, target language (default: German), translation hints toggle
- **Voice Settings** - STT/TTS providers with auto-transcription and language-matched voices
- **Generation Parameters** - Advanced AI tuning options (temperature, tokens, top-p)

#### `voice_handler.py`
Voice processing module with STT/TTS provider implementations.

**Key Classes:**

- `VoiceConfig` - Configuration for languages, voices, and providers
- `STTProvider` (Abstract) - Base class for speech-to-text providers
- `TTSProvider` (Abstract) - Base class for text-to-speech providers
- `OpenAIWhisperSTT` - OpenAI Whisper API implementation
- `LocalWhisperSTT` - Local Whisper model implementation
- `EdgeTTSProvider` - Microsoft Edge TTS (free, multilingual)
- `OpenAITTSProvider` - OpenAI TTS implementation
- `GTTSProvider` - Google TTS implementation

**Key Functions:**

- `get_available_languages()` - Returns list of 30 supported languages
- `get_language_code(language_name)` - Converts language name to ISO code
- `get_voices_for_provider(provider_name, language)` - Gets available voices for a language
- `get_default_voice_for_language(language_name, provider_name)` - Gets default voice for language
- `create_stt_provider(provider_name)` - Factory for STT providers
- `create_tts_provider(provider_name, voice, language)` - Factory for TTS providers

### Configuration Files

- `requirements.txt` - Python dependencies for pip/uv compatibility
- `pyproject.toml` - Project metadata and dependencies (UV format)
- `uv.lock` - Dependency lock file (managed by UV, ensures reproducible builds)
- `.env` - Environment variables (API keys, not committed to git)

## 🔌 API Providers

### Hugging Face Inference API

The application uses the Hugging Face Inference API to access the **Apertus-70B-Instruct-2509** model.

**Model Info:**
- **Name:** swiss-ai/Apertus-70B-Instruct-2509
- **Size:** 70B parameters
- **Training:** 1000+ languages
- **Context:** Supports long conversations
- **Hosting:** Hugging Face Inference Endpoints

**Rate Limits:**
- Free tier: Limited requests per hour
- Pro tier: Higher rate limits available

### Voice Provider APIs

- **Edge-TTS:** Free, no API key required
- **OpenAI:** Requires API key, pay-per-use
- **gTTS:** Free, no API key required
- **Whisper API:** Requires OpenAI API key
- **Local Whisper:** No API key, runs locally

## 🐛 Troubleshooting

### Common Issues

**Issue: "UV not found" or "Command not found: uv"**
```bash
# Install UV first:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via pip:
pip install uv

# Verify installation:
uv --version
```

**Issue: "Hugging Face token not found"**
```bash
# Solution 1: Set in .env file
echo "HF_TOKEN=your_token_here" > .env

# Solution 2: Use CLI login
huggingface-cli login
```

**Issue: "OpenAI API key required"**
```bash
# Only needed if using OpenAI providers
echo "OPENAI_API_KEY=your_key_here" >> .env
```

**Issue: "Model loading failed" or "Rate limit exceeded"**
- Wait a few minutes and try again
- Check your Hugging Face token is valid
- Consider using a Pro account for higher limits

**Issue: "Voice not working"**
- Check internet connection (Edge-TTS and gTTS require internet)
- Verify microphone permissions for voice input
- Try switching to a different TTS provider

**Issue: "Local Whisper is slow"**
- Local Whisper models run on your CPU/GPU
- Use "Tiny" model for faster performance
- Consider using OpenAI Whisper API for cloud-based processing

### Debug Mode

Enable debug output:
```python
# Add to the top of language_tutor.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎯 Best Practices

### For Best Learning Results

1. **Start Simple:** Begin with basic conversations before advanced topics
2. **Use Translation Hints Strategically:**
   - **Beginners:** Keep hints enabled to build vocabulary confidence
   - **Intermediate:** Toggle on/off based on topic difficulty
   - **Advanced:** Disable for full immersion practice
3. **Be Consistent:** Practice regularly, even if just 10-15 minutes daily
4. **Use Voice Features:** Enable both STT and TTS to practice speaking and listening
   - Record yourself speaking in the target language
   - Auto-transcription helps you see what you said
   - Listen to native pronunciation with TTS
5. **Ask Questions:** Request grammar explanations when confused
6. **Progressive Learning:** Start with hints, gradually disable them as you improve

### For Best Performance

1. **Use Edge-TTS:** Free and high-quality for most languages with regional variants
2. **Auto-Transcription:** Recordings automatically transcribe - no extra button needed
3. **Voice Settings:** STT and TTS automatically match your target language
4. **Adjust Token Limits:** Lower max_tokens (256-512) for faster, more concise responses
5. **Monitor Costs:** Track API usage if using paid providers (OpenAI Whisper/TTS)

## 📊 Cost Estimates

### Free Configuration (Recommended)
- **STT:** Local Whisper (Tiny or Base)
- **TTS:** Edge-TTS or gTTS
- **LLM:** Hugging Face (Free tier)
- **Total:** $0/month ✅

### Paid Configuration (Premium Quality)
- **STT:** OpenAI Whisper API (~$0.006/minute)
- **TTS:** OpenAI TTS (~$0.015/1K chars)
- **LLM:** Hugging Face (Free or Pro)
- **Example:** 10 hours/month ≈ $3.60 STT + ~$5 TTS = ~$8.60/month

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- **Language Support:** Add more languages and regional voice variants
- **Learning Modes:** Add grammar-focused, conversation-focused, or exam-prep modes
- **Progress Tracking:** Implement analytics and learning progress dashboards
- **Conversation History:** Export conversations for review and study
- **Specialized Prompts:** Create templates for business, travel, academic contexts
- **Interactive Exercises:** Add grammar quizzes, vocabulary drills, pronunciation practice
- **Difficulty Levels:** Auto-adjust based on user performance (A1-C2 CEFR levels)
- **Translation Memory:** Remember commonly confused words and revisit them
- **Voice Recording Playback:** Let users hear their own recordings for self-assessment
- **Multi-modal Learning:** Add image descriptions, video transcriptions, etc.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Apertus-70B** by Swiss AI Lab - Multilingual LLM
- **UV** by Astral - Fast Python package manager
- **Gradio** - Web interface framework
- **Hugging Face** - Model hosting and inference
- **Edge-TTS** - Free multilingual text-to-speech
- **OpenAI Whisper** - Speech recognition

## 📞 Support

For issues, questions, or feature requests, please open an issue on the repository.

---

**Happy Learning! 🎓🌍**

Made with ❤️ for language learners worldwide.
