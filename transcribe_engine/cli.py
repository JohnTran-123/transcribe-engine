"""Command-line entry point. `transcribe-engine <audio>` after pip install."""
import argparse
import os
import sys

from . import __version__
from .context import load_context
from .pipeline import run


def main():
    parser = argparse.ArgumentParser(
        prog="transcribe-engine",
        description="Multi-pass transcription with a growing context anchor.",
        epilog='Example: transcribe-engine meeting.mp3 --context-pack ./my-pack/',
    )
    parser.add_argument("files", nargs="+", help="Audio file(s) to transcribe")
    parser.add_argument("--context-pack", default=None,
                        help="Path to a context-pack folder or transcribe.config.yaml. "
                             "Defaults to TRANSCRIBE_CONTEXT_PACK env or ./transcribe.config.yaml.")
    parser.add_argument("--model", default=None, help="Override the Gemini model")
    parser.add_argument("--chunk-minutes", type=int, default=None, help="Override chunk size in minutes")
    parser.add_argument("--raw", action="store_true", help="Skip preprocessing (use raw audio)")
    parser.add_argument("--no-refine", action="store_true", help="Skip the LLM refinement pass")
    parser.add_argument("--extra-context", default=None,
                        help="Path to a file with additional one-off context (e.g. agenda for this specific meeting)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = parser.parse_args()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set.")
        print("Get a key at https://aistudio.google.com/apikey")
        sys.exit(1)

    try:
        from google import genai
    except ImportError:
        print("ERROR: google-genai not installed. Install with: pip install google-genai")
        sys.exit(1)

    ctx = load_context(args.context_pack)

    if args.model:
        ctx.model = args.model
    if args.chunk_minutes:
        ctx.chunk_minutes = args.chunk_minutes
    if args.raw:
        ctx.preprocess = False
    if args.no_refine:
        ctx.refine = False

    extra_context = ""
    if args.extra_context and os.path.exists(args.extra_context):
        with open(args.extra_context, "r", encoding="utf-8") as f:
            extra_context = f.read()

    client = genai.Client(api_key=api_key)

    for filepath in args.files:
        if not os.path.exists(filepath):
            print(f"ERROR: File not found: {filepath}")
            continue
        run(client, filepath, ctx, extra_context=extra_context)


if __name__ == "__main__":
    main()
