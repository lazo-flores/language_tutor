import os
import re

import gradio as gr
from openai import OpenAI
from dotenv import load_dotenv
from voice_handler import (
    create_stt_provider,
    create_tts_provider,
    get_available_stt_providers,
    get_available_tts_providers,
    get_voices_for_provider,
    get_available_languages,
    get_language_code,
    get_default_voice_for_language,
    VoiceConfig
)
from vad_handler import StreamingVAD, save_wav

load_dotenv(override=True)

# Initialize the tutor LLM via Google Gemini's OpenAI-compatible endpoint.
# The `openai` SDK (already a dependency) talks to Gemini by pointing base_url
# at the Generative Language API. Auth uses GEMINI_API_KEY from .env.
model_name = "gemini-3.5-flash"
short_model_name = "Gemini 3.5 Flash"
client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "missing-gemini-api-key",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

# High-precision signatures Whisper fabricates from silence/noise (video-subtitle
# credits, YouTube outros). A learner practicing conversation never says these, so
# they're safe to drop. This backs up the VAD's energy gate in vad_handler.py.
_HALLUCINATION_MARKERS = [
    "amara.org",
    "untertitel der",
    "untertitel im auftrag",
    "im auftrag des zdf",
    "untertitelung des zdf",
    "thanks for watching",
    "thank you for watching",
    "please subscribe",
    "subtitles by",
]


def is_probable_hallucination(text):
    """True if a transcription looks like a known Whisper silence-hallucination."""
    low = text.strip().lower()
    if not low:
        return True
    return any(marker in low for marker in _HALLUCINATION_MARKERS)


# The tutor separates its correction block from its conversational reply with a
# horizontal rule ("---"). We split on it to speak only the conversation aloud.
_SPEECH_SEPARATOR_RE = re.compile(r"\n\s*-{3,}\s*\n")


def split_corrections_and_conversation(text):
    """Return (corrections, conversation). With no separator, it's all conversation."""
    parts = _SPEECH_SEPARATOR_RE.split(text, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return "", text.strip()


def clean_text_for_tts(text):
    """Strip emojis, markdown and bullet glyphs so TTS doesn't read them aloud."""
    # Emoji / pictographs / arrows that gTTS would spell out or choke on
    text = re.sub(
        r"[\U0001F000-\U0001FAFF\U00002600-\U000027BF←-⇿⌀-⏿️]",
        "",
        text,
    )
    text = re.sub(r"[*_`#>~|]", "", text)       # markdown emphasis/heading/code/table
    text = re.sub(r"[▹•·◦‣▪◆■]", "", text)       # bullet glyphs
    text = _SPEECH_SEPARATOR_RE.sub("\n", text)  # horizontal-rule separators
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()

def format_messages(message, chat_history, system_prompt):
    """Format the conversation into messages list."""
    messages = []

    # Add system prompt if provided
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt})

    # Add chat history (already in messages format)
    messages.extend(chat_history)

    # Add current message
    messages.append({"role": "user", "content": message})

    return messages


def create_language_tutor_prompt(native_language, target_language, enable_translations=True):
    """
    Create a system prompt for the language tutor based on native and target languages.

    Args:
        native_language: User's native language
        target_language: Language the user wants to learn
        enable_translations: Whether to include native language translations

    Returns:
        System prompt string
    """
    if enable_translations:
        translation_guidance = (
            f"- Provide {native_language} translations when the user seems confused or asks for help\n"
            f"- In the corrections, you may add a brief {native_language} explanation in parentheses when it aids understanding"
        )
        correction_language = f"in {target_language}, with short {native_language} notes in parentheses where helpful"
    else:
        translation_guidance = (
            f"- Keep responses entirely in {target_language} for full immersion\n"
            f"- Only use {native_language} if the user explicitly asks for translation or clarification"
        )
        correction_language = f"in {target_language}"

    prompt = f"""You are an expert language tutor helping a {native_language} speaker learn {target_language}.

Your role:
- Respond primarily in {target_language} to provide immersive practice
{translation_guidance}
- Adjust your vocabulary and sentence complexity based on the user's level
- Ask engaging questions to encourage conversation practice
- Provide cultural context when relevant
- Be patient, encouraging, and supportive

CORRECTING THE USER (important — do this every turn):
The user is practicing speaking, and their messages come from speech that has been transcribed, so treat them as spoken {target_language}. Actively look for mistakes in grammar, word choice, verb conjugation, gender/agreement, word order, and unnatural phrasing.
- If you find one or more mistakes, BEGIN your reply with a brief "📝 Corrections" section, written {correction_language}:
  - Show what the user said and the corrected, natural version.
  - In one short phrase, name the rule or reason (e.g. wrong case, verb at the end, wrong gender).
  - Keep it to the most important 1–3 points — don't overwhelm; ignore trivial typos that don't affect meaning.
- If the message is fully correct and natural, BEGIN with a brief "✅" line confirming it was correct (and, when worth it, offer a more natural or advanced alternative phrasing).
- Then ALWAYS output a separator line containing only three dashes: ---
- AFTER the --- separator, continue the conversation naturally in {target_language} with an engaging follow-up. Keep this part free of correction notes — it is the part that may be read aloud. Always include the --- separator, even when the only thing above it is the ✅ confirmation.

Note: you only receive text, not audio, so you cannot judge pronunciation directly — focus your corrections on grammar, vocabulary, and phrasing.

Guidelines:
- Keep responses conversational and natural
- Use {target_language} for the main conversational response
- Praise genuine progress and keep feedback constructive and encouraging
- Adapt difficulty based on the user's responses

Start by greeting the user and asking what they'd like to practice today."""

    return prompt


def transcribe_audio(audio_path, stt_provider_name, language=None):
    """
    Transcribe audio to text using selected STT provider.

    Args:
        audio_path: Path to audio file
        stt_provider_name: Name of STT provider
        language: Optional ISO-639-1 code (e.g. "de") of the practice language

    Returns:
        Transcribed text or error message
    """
    if audio_path is None:
        return ""

    try:
        stt_provider = create_stt_provider(stt_provider_name)
        text = stt_provider.transcribe(audio_path, language=language)
        return text
    except Exception as e:
        return f"[Transcription Error: {str(e)}]"


def synthesize_speech(text, tts_provider_name, tts_voice, target_language="English"):
    """
    Synthesize text to speech using selected TTS provider.

    Args:
        text: Text to synthesize
        tts_provider_name: Name of TTS provider
        tts_voice: Voice to use
        target_language: Target language name for TTS

    Returns:
        Path to generated audio file or None if failed
    """
    if not text or not text.strip():
        return None

    try:
        language_code = get_language_code(target_language)
        tts_provider = create_tts_provider(tts_provider_name, voice=tts_voice, language=language_code)
        audio_path = tts_provider.synthesize(text)
        return audio_path
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        return None


def update_voice_dropdown(tts_provider_name, target_language="English"):
    """
    Update the voice dropdown based on selected TTS provider and target language.

    Args:
        tts_provider_name: Name of TTS provider
        target_language: Target language for voice selection

    Returns:
        Updated dropdown configuration
    """
    language_code = get_language_code(target_language)
    voices = get_voices_for_provider(tts_provider_name, language_code)
    return gr.Dropdown(choices=voices, value=voices[0] if voices else None)

def chat(message, chat_history, system_prompt, max_tokens, temperature, top_p,
         enable_tts, tts_provider_name, tts_voice, target_language,
         read_corrections_aloud=False, controller=None):
    """Stream a response from the tutor model.

    Yields partial chat history as tokens arrive so the reply appears
    progressively instead of after the whole generation completes. TTS is
    synthesized once, from the final text. ``controller`` is a shared per-session
    dict whose ``busy`` flag tells the mic VAD to stop listening while we respond.
    """
    if not message.strip():
        yield "", chat_history, gr.skip()
        return

    # Format the messages (uses history *before* the current turn is appended)
    messages = format_messages(message, chat_history, system_prompt)

    # Append the user turn and an empty assistant turn we'll fill as we stream
    chat_history = chat_history + [
        {"role": "user", "content": message},
        {"role": "assistant", "content": ""},
    ]

    # Mute the mic VAD for the duration of generation + synthesis.
    if controller is not None:
        controller["busy"] = True

    try:
        assistant_message = ""
        for chunk in client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            # Gemini 3.5 Flash is a "thinking" model; its hidden reasoning eats
            # into max_tokens (truncating the reply mid-word) and adds latency.
            # This is a conversational tutor, so turn thinking off — full replies,
            # roughly 2x faster.
            reasoning_effort="none",
            stream=True
        ):
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content or ""
            if delta:
                assistant_message += delta
                chat_history[-1]["content"] = assistant_message
                # Stream text only; leave the audio player untouched so its
                # value changes exactly once (below) and autoplay fires cleanly.
                yield "", chat_history, gr.skip()

        # Generate TTS audio once. By default speak only the conversational part
        # (after the --- separator), not the correction notes, and strip symbols
        # so they aren't read aloud. The full reply still shows in the chat.
        audio_output = None
        if enable_tts and assistant_message.strip():
            _, conversation = split_corrections_and_conversation(assistant_message)
            speech_source = assistant_message if read_corrections_aloud else conversation
            speech_text = clean_text_for_tts(speech_source)
            if speech_text:
                audio_output = synthesize_speech(speech_text, tts_provider_name, tts_voice, target_language)

        yield "", chat_history, audio_output

    except Exception as e:
        chat_history[-1]["content"] = f"Error: {str(e)}"
        yield "", chat_history, gr.skip()

    finally:
        if controller is not None:
            controller["busy"] = False


def vad_stream(new_chunk, vad_state, enable_voice_in, stt_provider_name,
               trigger_count, target_language, controller):
    """Process one streamed mic chunk for hands-free voice input.

    Feeds audio to the per-session VAD. While the user is still speaking it
    returns no UI changes. When the VAD detects they've stopped, it transcribes
    the utterance, puts the text in the message box, offers the recording for
    playback, and bumps ``auto_send_trigger`` so its ``.change`` fires ``chat``.

    Outputs: (message, vad_state, auto_send_trigger, user_playback)
    """
    if vad_state is None:
        vad_state = StreamingVAD()

    # Ignore the mic while the assistant is generating/speaking: this prevents
    # overlapping turns and stops the VAD from triggering on the assistant's
    # own voice. Keep the buffer cleared so we start fresh when it's our turn.
    if controller is not None and controller.get("busy"):
        vad_state.reset()
        return gr.skip(), vad_state, gr.skip(), gr.skip()

    # Skip silently when voice input is disabled or there's no audio yet.
    if not enable_voice_in or new_chunk is None:
        return gr.skip(), vad_state, gr.skip(), gr.skip()

    sample_rate, data = new_chunk
    result = vad_state.add_chunk(sample_rate, data)
    if result is None:
        # Still listening — don't touch any visible component.
        return gr.skip(), vad_state, gr.skip(), gr.skip()

    # End of speech detected: transcribe the finished utterance, constrained to
    # the practice language so Whisper doesn't mis-detect it as another language.
    utterance, utt_sr = result
    wav_path = save_wav(utterance, utt_sr)
    language_code = get_language_code(target_language)
    text = transcribe_audio(wav_path, stt_provider_name, language_code)

    # Offer the recording for playback regardless; only auto-send real text.
    # Drop transcription errors and known silence-hallucinations (the energy gate
    # in vad_handler should catch most; this is the final guard against the loop).
    if (not text or not text.strip()
            or text.startswith("[Transcription Error")
            or is_probable_hallucination(text)):
        return gr.skip(), vad_state, gr.skip(), wav_path

    return text, vad_state, (trigger_count or 0) + 1, wav_path

# Create Gradio interface
with gr.Blocks(title=f"Language Tutor with {short_model_name}", theme=gr.themes.Glass(primary_hue="indigo")) as demo:
    gr.Markdown("# 🌍 Language Tutor")
    gr.Markdown(f"Practice any language with an AI tutor powered by **Google {short_model_name}**!")

    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="Conversation", height=400, type='messages')

            # Text input section
            with gr.Row():
                msg = gr.Textbox(
                    label="Your Message",
                    placeholder="Type your message here...",
                    scale=4,
                    lines=2
                )
                submit = gr.Button("Send", scale=1, variant="primary")

            # Voice input section — streaming mic with automatic end-of-speech detection
            with gr.Row():
                voice_input = gr.Audio(
                    sources=["microphone"],
                    streaming=True,
                    type="numpy",
                    label="🎙️ Click the mic once, then just talk — it auto-sends when you pause",
                    waveform_options=gr.WaveformOptions(
                        show_controls=False
                    )
                )

            # Playback of the user's own last utterance (for self-assessment)
            user_playback = gr.Audio(
                label="Your last recording (listen to your pronunciation)",
                interactive=False,
                visible=True
            )

            # Voice output section
            voice_output = gr.Audio(
                label="Assistant Voice Response (tap play once — then it autoplays)",
                autoplay=True,
                visible=True
            )

            clear = gr.Button("Clear Conversation")

            # Hidden plumbing for hands-free voice: per-session VAD state and a
            # counter whose .change fires chat() once per detected utterance.
            vad_state = gr.State(None)
            auto_send_trigger = gr.Number(value=0, visible=False)
            # Shared per-session flag so chat() can mute the mic VAD while it
            # generates/speaks (prevents overlapping turns and self-triggering).
            controller = gr.State({"busy": False})

        with gr.Column(scale=1):
            with gr.Accordion("🌐 Language Settings", open=False):
                native_language = gr.Dropdown(
                    choices=get_available_languages(),
                    value="English",
                    label="Your Native Language",
                    info="Language for explanations and help"
                )

                target_language = gr.Dropdown(
                    choices=get_available_languages(),
                    value="German",
                    label="Language to Practice",
                    info="Language you want to learn"
                )

                enable_translations = gr.Checkbox(
                    label="Enable Native Language Hints",
                    value=True,
                    info="Show translations and explanations in your native language (in parentheses)"
                )

                system_prompt = gr.Textbox(
                    label="System Prompt (Auto-generated)",
                    placeholder="System prompt is automatically generated based on language selection...",
                    lines=5,
                    value=create_language_tutor_prompt("English", "German", True),
                    interactive=True,
                    info="You can customize this if needed",
                    visible=False  # Hidden from UI, but still functional in backend
                )

            with gr.Accordion("🔊 Voice Settings", open=False):
                enable_voice_input = gr.Checkbox(
                    label="Enable Voice Input (STT)",
                    value=True,
                    info="Transcribe voice to text"
                )

                stt_provider = gr.Dropdown(
                    choices=get_available_stt_providers(),
                    value=VoiceConfig.DEFAULT_STT,
                    label="Speech-to-Text Provider",
                    info="Choose quality/cost tier"
                )

                enable_voice_output = gr.Checkbox(
                    label="Enable Voice Output (TTS)",
                    value=True,
                    info="Convert responses to speech"
                )

                read_corrections_aloud = gr.Checkbox(
                    label="Read correction notes aloud",
                    value=False,
                    info="Off: the voice speaks only the conversation (corrections still shown in chat). On: it reads the corrections too."
                )

                tts_provider = gr.Dropdown(
                    choices=get_available_tts_providers(),
                    value=VoiceConfig.DEFAULT_TTS,
                    label="Text-to-Speech Provider",
                    info="Choose quality/cost tier"
                )

                tts_voice = gr.Dropdown(
                    choices=get_voices_for_provider(VoiceConfig.DEFAULT_TTS, get_language_code("German")),
                    value=get_default_voice_for_language("German", VoiceConfig.DEFAULT_TTS),
                    label="TTS Voice",
                    info="Voice automatically matched to target language"
                )

            with gr.Accordion("⚙️ Generation Parameters", open=False):
                max_tokens = gr.Slider(
                    minimum=50,
                    maximum=2048,
                    value=512,
                    step=50,
                    label="Max Tokens",
                    info="Maximum length of the response"
                )

                temperature = gr.Slider(
                    minimum=0.0,
                    maximum=2.0,
                    value=0.7,
                    step=0.1,
                    label="Temperature",
                    info="Higher = more creative, Lower = more focused"
                )

                top_p = gr.Slider(
                    minimum=0.0,
                    maximum=1.0,
                    value=0.9,
                    step=0.05,
                    label="Top P",
                    info="Nucleus sampling threshold"
                )
    
    # Event handlers

    # Update system prompt when languages or translation setting changes
    def update_system_prompt(native_lang, target_lang, enable_trans):
        return create_language_tutor_prompt(native_lang, target_lang, enable_trans)

    native_language.change(
        update_system_prompt,
        inputs=[native_language, target_language, enable_translations],
        outputs=[system_prompt]
    )

    target_language.change(
        update_system_prompt,
        inputs=[native_language, target_language, enable_translations],
        outputs=[system_prompt]
    )

    enable_translations.change(
        update_system_prompt,
        inputs=[native_language, target_language, enable_translations],
        outputs=[system_prompt]
    )

    # Update TTS voice dropdown when target language or provider changes
    target_language.change(
        update_voice_dropdown,
        inputs=[tts_provider, target_language],
        outputs=[tts_voice]
    )

    tts_provider.change(
        update_voice_dropdown,
        inputs=[tts_provider, target_language],
        outputs=[tts_voice]
    )

    # Text message submit
    submit.click(
        chat,
        inputs=[msg, chatbot, system_prompt, max_tokens, temperature, top_p,
                enable_voice_output, tts_provider, tts_voice, target_language,
                read_corrections_aloud, controller],
        outputs=[msg, chatbot, voice_output]
    )

    msg.submit(
        chat,
        inputs=[msg, chatbot, system_prompt, max_tokens, temperature, top_p,
                enable_voice_output, tts_provider, tts_voice, target_language,
                read_corrections_aloud, controller],
        outputs=[msg, chatbot, voice_output]
    )

    # Hands-free voice: stream mic chunks through the VAD. It auto-sends on a
    # detected pause by bumping auto_send_trigger, whose .change fires chat().
    voice_input.stream(
        vad_stream,
        inputs=[voice_input, vad_state, enable_voice_input, stt_provider,
                auto_send_trigger, target_language, controller],
        outputs=[msg, vad_state, auto_send_trigger, user_playback],
        stream_every=0.4,
        show_progress="hidden"
    )

    auto_send_trigger.change(
        chat,
        inputs=[msg, chatbot, system_prompt, max_tokens, temperature, top_p,
                enable_voice_output, tts_provider, tts_voice, target_language,
                read_corrections_aloud, controller],
        outputs=[msg, chatbot, voice_output]
    )

    # Autoplay unlock: clicking the mic to start is itself a user gesture, so we
    # prime every audio element there. Browsers then permit the assistant's voice
    # to autoplay for the rest of the session — no separate "enable sound" step.
    voice_input.start_recording(
        None,
        js="""
        () => {
          document.querySelectorAll('audio').forEach(a => {
            try {
              const p = a.play();
              if (p && p.then) p.then(() => a.pause()).catch(() => {});
            } catch (e) {}
          });
        }
        """
    )

    # Clear conversation
    clear.click(
        lambda: ([], None),
        outputs=[chatbot, voice_output]
    )

# Launch the app
if __name__ == "__main__":
    on_hf_spaces = bool(os.environ.get("SPACE_ID"))
    demo.launch(share=False, inbrowser=not on_hf_spaces)