# 🌍 Language Tutor - AI-Powered Multilingual Learning

An AI-powered conversational chatbot designed to help users practice speaking foreign languages in an interactive, adaptive environment. Powered by the **Apertus-70B-Instruct-2509** model, which is trained on 1000+ languages, this application provides immersive language learning with voice support.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Gradio](https://img.shields.io/badge/Gradio-UI-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

- 🗣️ **30+ Supported Languages** - Practice any of 30 major world languages
- 🎯 **Personalized Learning** - Select your native language and target language
- 🤖 **AI Tutor** - Powered by Apertus-70B, trained on 1000+ languages
- 🎤 **Voice Input (STT)** - Speak naturally using speech-to-text
- 🔊 **Voice Output (TTS)** - Hear responses with native pronunciation
- 🌐 **Multilingual Voices** - Automatic voice matching for target language
- 📝 **Smart Prompts** - Auto-generated teaching prompts based on language pair
- 💡 **Adaptive Teaching** - Provides translations, corrections, and cultural context

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

- Python 3.8 or higher
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

### Step 1: Clone or Download the Repository

```bash
cd /path/to/language_tutor
```

### Step 2: Create a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

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

### Customizing System Prompts

The system prompt is automatically generated based on your native and target language selection. You can customize it in the UI if you want to:
- Change the teaching style
- Focus on specific topics (grammar, conversation, business, etc.)
- Adjust difficulty level
- Add specific learning goals

## 🎮 Usage

### Starting the Application

```bash
python language_tutor.py
```

The application will launch a web interface at `http://127.0.0.1:7860`

### Basic Workflow

1. **Select Languages**
   - Choose your native language (for explanations)
   - Choose the language you want to practice
   - The system prompt will auto-generate

2. **Configure Voice Settings** (Optional)
   - Enable Voice Input (STT) to speak instead of typing
   - Enable Voice Output (TTS) to hear responses
   - Select preferred voice provider and voice style

3. **Start Learning**
   - Type or speak your message
   - The AI tutor responds primarily in the target language
   - Receive corrections, explanations, and cultural context

4. **Adjust Settings**
   - Tune generation parameters (temperature, max tokens)
   - Change voice providers/styles
   - Modify system prompt for specific learning goals

### Example Conversation (English → Spanish)

**You:** "Hello! I want to practice ordering food at a restaurant."

**AI Tutor:** "¡Hola! Perfecto, vamos a practicar. (Hello! Perfect, let's practice.)

Imagina que estás en un restaurante español. Yo soy el camarero. (Imagine you're in a Spanish restaurant. I'm the waiter.)

¿Qué te gustaría pedir? (What would you like to order?)"

**You:** "Quiero una pizza, por favor."

**AI Tutor:** "¡Muy bien! Tu frase es correcta. (Very good! Your sentence is correct.)

En España, dirías: 'Quisiera una pizza, por favor' (más formal) o 'Me pone una pizza, por favor' (más común).

¿Y para beber? ¿Qué te gustaría tomar? (And to drink? What would you like?)"

## 📂 Code Structure

### Main Files

#### `language_tutor.py`
Main application file containing the Gradio interface and core logic.

**Key Functions:**

- `create_language_tutor_prompt(native_language, target_language)` - Generates intelligent system prompts based on language pair
- `format_messages(message, chat_history, system_prompt)` - Formats conversation for the LLM
- `transcribe_audio(audio_path, stt_provider_name)` - Converts speech to text
- `synthesize_speech(text, tts_provider_name, tts_voice, target_language)` - Converts text to speech with language awareness
- `chat(...)` - Main chat function that handles LLM inference
- `update_voice_dropdown(tts_provider_name, target_language)` - Dynamically updates voice options

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

- `requirements.txt` - Python dependencies
- `.env` - Environment variables (API keys)
- `pyproject.toml` - Project metadata (if using uv)
- `uv.lock` - Dependency lock file (if using uv)

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
2. **Be Consistent:** Practice regularly, even if just 10-15 minutes daily
3. **Use Voice:** Enable TTS to improve pronunciation and listening skills
4. **Ask Questions:** Request grammar explanations when confused
5. **Set Goals:** Customize the system prompt with specific learning objectives

### For Best Performance

1. **Use Edge-TTS:** Free and high-quality for most languages
2. **Enable Voice Selectively:** TTS adds latency; use when practicing pronunciation
3. **Adjust Token Limits:** Lower max_tokens for faster responses
4. **Monitor Costs:** Track API usage if using paid providers (OpenAI)

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

- Add more languages to the voice mappings
- Implement conversation history export
- Add progress tracking and analytics
- Create specialized prompts (business, travel, academic)
- Add grammar exercises and quizzes
- Implement spaced repetition for vocabulary

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Apertus-70B** by Swiss AI Lab - Multilingual LLM
- **Gradio** - Web interface framework
- **Hugging Face** - Model hosting and inference
- **Edge-TTS** - Free multilingual text-to-speech
- **OpenAI Whisper** - Speech recognition

## 📞 Support

For issues, questions, or feature requests, please open an issue on the repository.

---

**Happy Learning! 🎓🌍**

Made with ❤️ for language learners worldwide.
