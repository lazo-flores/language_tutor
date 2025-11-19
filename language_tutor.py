import gradio as gr
from huggingface_hub import InferenceClient
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

load_dotenv(override=True)

# Initialize the Hugging Face Inference Client
model_name = "swiss-ai/Apertus-70B-Instruct-2509"
short_model_name = "Apertus-70B-Instruct"
client = InferenceClient(model=model_name)

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


def create_language_tutor_prompt(native_language, target_language):
    """
    Create a system prompt for the language tutor based on native and target languages.

    Args:
        native_language: User's native language
        target_language: Language the user wants to learn

    Returns:
        System prompt string
    """
    prompt = f"""You are an expert language tutor helping a {native_language} speaker learn {target_language}.

Your role:
- Respond primarily in {target_language} to provide immersive practice
- Provide {native_language} translations when the user seems confused or asks for help
- Correct mistakes gently and explain grammar rules when appropriate
- Adjust your vocabulary and sentence complexity based on the user's level
- Ask engaging questions to encourage conversation practice
- Provide cultural context when relevant
- Be patient, encouraging, and supportive

Guidelines:
- Keep responses conversational and natural
- Use {target_language} for the main response
- Include {native_language} explanations in parentheses when helpful
- Praise progress and provide constructive feedback
- Adapt difficulty based on the user's responses

Start by greeting the user and asking what they'd like to practice today."""

    return prompt


def transcribe_audio(audio_path, stt_provider_name):
    """
    Transcribe audio to text using selected STT provider.

    Args:
        audio_path: Path to audio file
        stt_provider_name: Name of STT provider

    Returns:
        Transcribed text or error message
    """
    if audio_path is None:
        return ""

    try:
        stt_provider = create_stt_provider(stt_provider_name)
        text = stt_provider.transcribe(audio_path)
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
         enable_tts, tts_provider_name, tts_voice, target_language):
    """Generate a response from the Hugging Face hosted model."""
    if not message.strip():
        return "", chat_history, None

    # Format the messages
    messages = format_messages(message, chat_history, system_prompt)

    try:
        # Call the Hugging Face Inference API
        response = client.chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=False
        )

        # Extract the assistant's reply
        assistant_message = response.choices[0].message.content

        # Update chat history with messages format
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": assistant_message})

        # Generate TTS audio if enabled
        audio_output = None
        if enable_tts:
            audio_output = synthesize_speech(assistant_message, tts_provider_name, tts_voice, target_language)

        return "", chat_history, audio_output

    except Exception as e:
        error_message = f"Error: {str(e)}"
        chat_history.append({"role": "user", "content": message})
        chat_history.append({"role": "assistant", "content": error_message})
        return "", chat_history, None


def process_voice_input(audio, stt_provider_name):
    """
    Process voice input and return transcribed text.

    Args:
        audio: Audio file from microphone
        stt_provider_name: Name of STT provider

    Returns:
        Transcribed text
    """
    if audio is None:
        return ""

    transcribed_text = transcribe_audio(audio, stt_provider_name)
    return transcribed_text

# Create Gradio interface
with gr.Blocks(title="Language Tutor with Apertus-70B", theme=gr.themes.Glass(primary_hue="indigo")) as demo:
    gr.Markdown("# 🌍 Language Tutor")
    gr.Markdown(f"Practice any language with an AI tutor powered by **Swiss AI {short_model_name}** - trained on 1000+ languages!")
    # gr.Markdown("⚠️ **Note**: You may need a Hugging Face token for API access. Set it with `huggingface-cli login` or pass it to InferenceClient.")
    
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

            # Voice input section
            with gr.Row():
                voice_input = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    label="Voice Input (Recording auto-transcribes when you stop)",
                    waveform_options=gr.WaveformOptions(
                        show_controls=False
                    )
                )

            # Voice output section
            voice_output = gr.Audio(
                label="Assistant Voice Response",
                autoplay=True,
                visible=True
            )

            clear = gr.Button("Clear Conversation")

        with gr.Column(scale=1):
            gr.Markdown("### 🌐 Language Settings")

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

            system_prompt = gr.Textbox(
                label="System Prompt (Auto-generated)",
                placeholder="System prompt is automatically generated based on language selection...",
                lines=5,
                value=create_language_tutor_prompt("English", "German"),
                interactive=True,
                info="You can customize this if needed",
                visible=False  # Hidden from UI, but still functional in backend
            )

            gr.Markdown("### Voice Settings")

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

            gr.Markdown("### Generation Parameters")

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

    # Update system prompt when languages change
    def update_system_prompt(native_lang, target_lang):
        return create_language_tutor_prompt(native_lang, target_lang)

    native_language.change(
        update_system_prompt,
        inputs=[native_language, target_language],
        outputs=[system_prompt]
    )

    target_language.change(
        update_system_prompt,
        inputs=[native_language, target_language],
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
                enable_voice_output, tts_provider, tts_voice, target_language],
        outputs=[msg, chatbot, voice_output]
    )

    msg.submit(
        chat,
        inputs=[msg, chatbot, system_prompt, max_tokens, temperature, top_p,
                enable_voice_output, tts_provider, tts_voice, target_language],
        outputs=[msg, chatbot, voice_output]
    )

    # Automatic voice input transcription when recording stops
    voice_input.stop_recording(
        process_voice_input,
        inputs=[voice_input, stt_provider],
        outputs=[msg]
    )

    # Also trigger on audio change (for uploaded files)
    voice_input.change(
        process_voice_input,
        inputs=[voice_input, stt_provider],
        outputs=[msg]
    )

    # Clear conversation
    clear.click(
        lambda: ([], None),
        outputs=[chatbot, voice_output]
    )

# Launch the app
if __name__ == "__main__":
    demo.launch(share=False)