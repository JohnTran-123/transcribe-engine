"""Audio preprocessing: noise reduction + peak normalization.

Optional — engine runs fine without it. If `noisereduce` / `soundfile` aren't
installed, this module silently passes the original file through.
"""
import os
import subprocess

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG = "ffmpeg"


def preprocess_audio(filepath: str, temp_dir: str) -> str:
    """Noise-reduce + peak-normalize. Returns path to cleaned audio (or original on failure)."""
    try:
        import noisereduce as nr
        import soundfile as sf
        import numpy as np
    except ImportError:
        print("  SKIP preprocessing (install: pip install noisereduce soundfile)")
        return filepath

    clean_path = os.path.join(temp_dir, "preprocessed.wav")
    wav_path = os.path.join(temp_dir, "input.wav")

    print("  Converting to WAV...", end=" ", flush=True)
    cmd = [FFMPEG, "-y", "-i", filepath, "-ar", "16000", "-ac", "1", "-f", "wav", wav_path]
    r = subprocess.run(cmd, capture_output=True, timeout=120)
    if r.returncode != 0 or not os.path.exists(wav_path):
        print("failed, skipping preprocessing")
        return filepath
    print("done")

    data, sr = sf.read(wav_path)

    print("  Noise reduction...", end=" ", flush=True)
    try:
        reduced = nr.reduce_noise(
            y=data, sr=sr,
            prop_decrease=0.6,
            n_fft=2048,
            stationary=False,
        )
        print("done")
    except Exception as e:
        print(f"failed ({e}), using original")
        reduced = data

    print("  Normalizing volume...", end=" ", flush=True)
    peak = np.max(np.abs(reduced))
    if peak > 0:
        target_peak = 10 ** (-1.0 / 20.0)
        reduced = reduced * (target_peak / peak)
    print("done")

    sf.write(clean_path, reduced, sr)

    mp3_path = os.path.join(temp_dir, "preprocessed.mp3")
    cmd = [FFMPEG, "-y", "-i", clean_path, "-acodec", "libmp3lame", "-q:a", "2", mp3_path]
    subprocess.run(cmd, capture_output=True, timeout=120)
    if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 1000:
        return mp3_path
    return clean_path
