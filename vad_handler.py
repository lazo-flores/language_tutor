"""
Streaming Voice-Activity Detection (VAD)

Lets the app run hands-free: instead of clicking "Stop", the user just talks,
and this module detects when they've finished speaking so the app can
auto-transcribe and send.

It wraps silero-vad. A `StreamingVAD` instance is created per Gradio session
(stored in a `gr.State`) and fed raw microphone chunks from the Audio `.stream`
event. When it detects speech followed by a sustained pause, `add_chunk`
returns the finished utterance as audio, which the caller transcribes.

The silero model only accepts 16 kHz mono frames of 512 samples, so chunks are
resampled to 16 kHz *for detection only*. The original-rate audio is preserved
and handed to the speech-to-text provider, so transcription quality isn't
degraded by the downsample.
"""

import os
import wave
import tempfile
import uuid
from typing import Optional, Tuple

import numpy as np
import torch

# silero-vad frame requirements
SILERO_SR = 16000          # silero operates at 16 kHz
FRAME_SAMPLES = 512        # silero expects exactly 512-sample frames at 16 kHz
FRAME_MS = FRAME_SAMPLES / SILERO_SR * 1000.0  # 32 ms per frame

# Detection tuning (milliseconds). These are the knobs to adjust if auto-send
# fires too eagerly (raise SILENCE_HANG_MS) or clips the user off.
SPEECH_THRESHOLD = 0.5     # frame speech-probability above which it counts as speech
MIN_SPEECH_MS = 250        # require this much speech before a pause can trigger a send
SILENCE_HANG_MS = 900      # trailing silence that means "they've stopped talking"
PREROLL_MS = 300           # audio kept before speech onset so we don't clip the first word
MAX_UTTERANCE_MS = 30000   # safety cap: force a send if someone talks this long nonstop

# Anti-hallucination gates. Whisper invents text (e.g. "Untertitel der
# Amara.org-Community") when fed silence/noise, so we discard any "utterance"
# that isn't both confidently speech and actually loud enough to be a voice.
MIN_PEAK_PROB = 0.85       # need at least one clearly-speech frame, else it's noise
MIN_RMS = 0.01             # need real audio energy (silence/breath sits well below this)

_model = None


def _get_model():
    """Lazily load the shared silero-vad model."""
    global _model
    if _model is None:
        torch.set_num_threads(1)  # avoid oversubscription on small CPU hosts (e.g. HF Spaces)
        from silero_vad import load_silero_vad
        _model = load_silero_vad()
    return _model


def _to_mono_float32(audio: np.ndarray) -> np.ndarray:
    """Coerce a Gradio audio chunk to mono float32 in [-1, 1].

    Gradio streams ``type="numpy"`` mic audio as int16; integer dtypes are
    scaled to [-1, 1]. Float input is assumed already normalized.
    """
    audio = np.asarray(audio)
    is_int = np.issubdtype(audio.dtype, np.integer)
    if audio.ndim > 1:                      # (samples, channels) -> mono
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float32)
    if is_int:                              # int16 (or other int) -> normalize by full scale
        audio = audio / 32768.0
    return audio


def _resample_to_16k(audio: np.ndarray, sr: int) -> np.ndarray:
    """Linear-interpolation resample to 16 kHz (sufficient for VAD detection)."""
    if sr == SILERO_SR or audio.size == 0:
        return audio
    new_len = int(round(audio.shape[0] * SILERO_SR / sr))
    if new_len <= 0:
        return np.zeros(0, dtype=np.float32)
    x_old = np.linspace(0.0, 1.0, num=audio.shape[0], endpoint=False)
    x_new = np.linspace(0.0, 1.0, num=new_len, endpoint=False)
    return np.interp(x_new, x_old, audio).astype(np.float32)


class StreamingVAD:
    """Accumulates streamed mic audio and detects end-of-utterance.

    One instance per session. Reusable: after it returns an utterance it resets
    itself and keeps listening for the next one.
    """

    def __init__(self):
        self._reset()
        _get_model().reset_states()

    def _reset(self):
        self.orig_sr: Optional[int] = None
        self.orig_buffer = np.zeros(0, dtype=np.float32)  # utterance audio at mic sample rate
        self._frame_carry = np.zeros(0, dtype=np.float32)  # leftover < one 16k frame
        self.speech_started = False
        self.speech_ms = 0.0
        self.silence_ms = 0.0
        self.peak_prob = 0.0  # highest speech probability seen this utterance

    def reset(self):
        """Discard any in-progress audio and clear model state."""
        self._reset()
        _get_model().reset_states()

    def add_chunk(self, sr: int, audio: np.ndarray) -> Optional[Tuple[np.ndarray, int]]:
        """Feed one mic chunk.

        Returns ``(utterance_audio, sample_rate)`` once end-of-speech is
        detected (and resets for the next utterance), otherwise ``None``.
        """
        model = _get_model()
        mono = _to_mono_float32(audio)
        if mono.size == 0:
            return None
        if self.orig_sr is None:
            self.orig_sr = sr

        # Accumulate full audio once speech has started; before that, keep only a
        # short pre-roll so leading silence doesn't bloat the buffer or the clip.
        self.orig_buffer = np.concatenate([self.orig_buffer, mono])
        if not self.speech_started:
            preroll = int(PREROLL_MS / 1000.0 * (self.orig_sr or sr))
            if self.orig_buffer.shape[0] > preroll:
                self.orig_buffer = self.orig_buffer[-preroll:]

        # Frame the new audio at 16 kHz and score each frame for speech.
        work = np.concatenate([self._frame_carry, _resample_to_16k(mono, sr)])
        n_frames = work.shape[0] // FRAME_SAMPLES
        for i in range(n_frames):
            frame = work[i * FRAME_SAMPLES:(i + 1) * FRAME_SAMPLES]
            prob = model(torch.from_numpy(frame), SILERO_SR).item()
            self.peak_prob = max(self.peak_prob, prob)
            if prob >= SPEECH_THRESHOLD:
                self.speech_ms += FRAME_MS
                self.silence_ms = 0.0
                if self.speech_ms >= MIN_SPEECH_MS:
                    self.speech_started = True
            elif self.speech_started:
                self.silence_ms += FRAME_MS
        self._frame_carry = work[n_frames * FRAME_SAMPLES:]

        utterance_ms = self.orig_buffer.shape[0] / (self.orig_sr or sr) * 1000.0
        end_of_speech = self.speech_started and self.silence_ms >= SILENCE_HANG_MS
        too_long = self.speech_started and utterance_ms >= MAX_UTTERANCE_MS

        if end_of_speech or too_long:
            audio = self.orig_buffer.copy()
            sr_out = self.orig_sr or sr
            peak = self.peak_prob
            rms = float(np.sqrt(np.mean(audio ** 2))) if audio.size else 0.0
            self.reset()
            # Reject anything that wasn't confidently speech AND loud enough — this
            # is what stops the silence -> Whisper-hallucination -> resend loop.
            if peak < MIN_PEAK_PROB or rms < MIN_RMS:
                return None
            return (audio, sr_out)
        return None


def save_wav(audio: np.ndarray, sr: int) -> str:
    """Write float32 mono audio to a unique temp WAV and return its path."""
    path = os.path.join(tempfile.gettempdir(), f"utt_{uuid.uuid4().hex}.wav")
    pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return path
