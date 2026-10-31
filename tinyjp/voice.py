"""Voice synthesis (edge-tts, free). A missing voice is a hard error - nothing is faked silently."""
import asyncio, os, subprocess, sys, time, wave
import numpy as np
from .config import SR, VOICE_RATE

def write_wav(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

def read_wav(path):
    with wave.open(path, "rb") as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float32) / 32768

def synth(text, voice, out_wav, dummy=False, rate=None, pitch=None):
    """Write a mono SR-Hz wav of `text`. dummy=True makes a LOUDLY-labelled test tone (never for real renders)."""
    if dummy:
        n = int(max(0.8, len(text) * 0.07) * SR); t = np.arange(n) / SR
        write_wav(out_wav, 0.3 * np.sin(2 * np.pi * 220 * t) * np.abs(np.sin(2 * np.pi * 3.5 * t)) ** 0.7)
        return
    try:
        import edge_tts
    except ImportError:
        sys.exit("ERROR: edge-tts is not installed (pip install -r requirements.txt)")
    mp3, last = out_wav + ".mp3", None
    for attempt in range(1, 6):
        try:
            kw = {"pitch": pitch} if pitch else {}
            asyncio.run(edge_tts.Communicate(text, voice, rate=rate or VOICE_RATE, **kw).save(mp3))
            if os.path.getsize(mp3) < 500:
                raise RuntimeError("voice service returned empty audio")
            break
        except Exception as e:
            last = e
            print(f"edge-tts attempt {attempt}/5 failed for voice {voice}: {e}", file=sys.stderr)
            time.sleep(3 * attempt)
    else:
        sys.exit(f"::error::The voice {voice} is unavailable ({last}). No fallback voice is used; re-run later.")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ar", str(SR), "-ac", "1", out_wav], check=True)
    os.remove(mp3)
