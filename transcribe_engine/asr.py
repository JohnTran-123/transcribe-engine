"""Chunked Gemini ASR. Each chunk is uploaded with a context-injected prompt."""
import math
import os
import subprocess
import time

from .context import Context
from .prompts import ASR_PROMPT

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG = "ffmpeg"


def get_duration(filepath: str) -> float:
    """Audio duration in seconds, via ffmpeg probe. Returns 0 on failure."""
    cmd = [FFMPEG, "-i", filepath]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    for line in result.stderr.split("\n"):
        if "Duration:" in line:
            time_str = line.split("Duration:")[1].split(",")[0].strip()
            parts = time_str.split(":")
            return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    return 0


def split_audio(filepath: str, chunk_secs: int, temp_dir: str):
    """Split audio into chunks. Returns (chunk_paths, total_duration_secs)."""
    os.makedirs(temp_dir, exist_ok=True)
    duration = get_duration(filepath)
    if duration == 0:
        print("  WARNING: Could not detect duration. Uploading whole file.")
        return [filepath], 0
    n_chunks = math.ceil(duration / chunk_secs)

    chunks = []
    for i in range(n_chunks):
        start = i * chunk_secs
        chunk_path = os.path.join(temp_dir, f"chunk{i:02d}.mp3")
        cmd = [
            FFMPEG, "-y", "-i", filepath,
            "-ss", str(start), "-t", str(chunk_secs),
            "-acodec", "copy", chunk_path,
        ]
        subprocess.run(cmd, capture_output=True, timeout=60)
        if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 1000:
            chunks.append(chunk_path)
        elif os.path.exists(chunk_path):
            cmd2 = [
                FFMPEG, "-y", "-ss", str(start), "-i", filepath,
                "-t", str(chunk_secs), "-vn",
                "-acodec", "libmp3lame", "-q:a", "2", chunk_path,
            ]
            subprocess.run(cmd2, capture_output=True, timeout=120)
            if os.path.exists(chunk_path) and os.path.getsize(chunk_path) > 1000:
                chunks.append(chunk_path)
    return chunks, duration


def transcribe_chunks(client, chunks, duration: float, ctx: Context,
                      chunk_minutes: int, extra_context: str = "") -> str:
    """Run ASR on each chunk via Gemini. Returns the concatenated raw transcript."""
    total_chunks = len(chunks)
    all_text = []

    for i, chunk_path in enumerate(chunks):
        start_min = i * chunk_minutes
        end_min = (
            min((i + 1) * chunk_minutes, duration / 60)
            if duration > 0 else (i + 1) * chunk_minutes
        )

        prompt = ASR_PROMPT.format(
            chunk_num=i + 1,
            total_chunks=total_chunks,
            start_min=f"{start_min}",
            end_min=f"{end_min:.0f}",
            domain_description=ctx.domain_description or "",
            language_note=ctx.language_note or "",
            glossary_block=ctx.glossary_block,
            extra_context=extra_context or "",
        )

        print(f"  ASR {i+1}/{total_chunks} [{start_min}-{end_min:.0f} min]...", end=" ", flush=True)
        t0 = time.time()

        try:
            uploaded = client.files.upload(file=chunk_path)
            response = client.models.generate_content(
                model=ctx.model,
                contents=[uploaded, prompt],
            )
            text = response.text or ""
            if not text and response.candidates:
                for c in response.candidates:
                    if c.content and c.content.parts:
                        text = "".join(
                            p.text for p in c.content.parts
                            if hasattr(p, "text") and p.text
                        )

            elapsed = time.time() - t0
            print(f"done ({elapsed:.0f}s, {len(text)} chars)")
            all_text.append(f"\n## [{start_min}:00 - {end_min:.0f}:00]\n\n{text}")

            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                pass
        except Exception as e:
            elapsed = time.time() - t0
            print(f"ERROR ({elapsed:.0f}s): {e}")
            all_text.append(f"\n## [{start_min}:00 - {end_min:.0f}:00]\n\n[ERROR: {e}]\n")

        time.sleep(2)

    return "\n".join(all_text)
