"""Orchestrates: preprocess -> chunked ASR -> LLM refine."""
import os
import shutil
import tempfile
import time

from .asr import split_audio, transcribe_chunks
from .context import Context
from .preprocess import preprocess_audio
from .refine import refine_transcript


def run(client, filepath: str, ctx: Context, extra_context: str = "") -> str:
    """Full pipeline. Returns the path to the primary output file."""
    basename = os.path.splitext(os.path.basename(filepath))[0]
    out_dir = os.path.dirname(os.path.abspath(filepath))
    raw_path = os.path.join(out_dir, f"{basename}_raw.md")
    refined_path = os.path.join(out_dir, f"{basename}_transcript.md")
    temp_dir = os.path.join(tempfile.gettempdir(), f"transcribe_engine_{os.getpid()}")
    os.makedirs(temp_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"File:     {os.path.basename(filepath)}")
    print(f"Size:     {os.path.getsize(filepath)/1024/1024:.1f} MB")
    print(f"Model:    {ctx.model}")
    print(f"Pipeline: {'preprocess' if ctx.preprocess else 'raw'} -> ASR -> {'refine' if ctx.refine else 'done'}")
    print(f"Pack:     {ctx.pack_root or '(none — zero-context mode)'}")

    total_start = time.time()

    if ctx.preprocess:
        print("\n[Phase 0] Preprocessing audio...")
        audio_path = preprocess_audio(filepath, temp_dir)
    else:
        audio_path = filepath

    print("\n[Phase 1] Transcribing with Gemini ASR...")
    chunk_secs = ctx.chunk_minutes * 60
    chunk_dir = os.path.join(temp_dir, "chunks")
    chunks, duration = split_audio(audio_path, chunk_secs, chunk_dir)
    total_chunks = len(chunks)
    dur_str = f"{duration/60:.1f} min" if duration > 0 else "unknown"
    print(f"  Duration: {dur_str} -> {total_chunks} chunks of {ctx.chunk_minutes} min")

    raw_transcript = transcribe_chunks(client, chunks, duration, ctx, ctx.chunk_minutes, extra_context)

    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(f"# Raw Transcription: {os.path.basename(filepath)}\n")
        f.write(f"# Model: {ctx.model}\n")
        f.write(f"# Audio duration: {dur_str}\n")
        f.write(f"# Preprocessed: {ctx.preprocess}\n\n")
        f.write(raw_transcript)
    print(f"\n  Raw saved: {raw_path}")

    final_path = raw_path

    if ctx.refine:
        print("\n[Phase 2] Refining transcript with LLM second pass...")
        refined = refine_transcript(client, raw_transcript, ctx)

        if refined:
            total_elapsed = time.time() - total_start
            with open(refined_path, "w", encoding="utf-8") as f:
                f.write(f"# Meeting Transcript: {os.path.basename(filepath)}\n")
                f.write(f"# Model: {ctx.model} (2-pass: ASR + refinement)\n")
                f.write(f"# Audio duration: {dur_str}\n")
                f.write(f"# Processing time: {total_elapsed:.0f}s\n")
                f.write(f"# Preprocessed: {ctx.preprocess}\n\n")
                f.write(refined)
            print(f"  Refined saved: {refined_path}")
            final_path = refined_path
        else:
            print("  Refinement failed — raw transcript is the final output.")

    total_elapsed = time.time() - total_start
    print(f"\n  TOTAL: {total_elapsed:.0f}s ({total_elapsed/60:.1f} min)")

    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    return final_path
