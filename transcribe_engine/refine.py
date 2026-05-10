"""LLM refinement pass — error correction + structure extraction over the raw transcript."""
import time

from .context import Context
from .prompts import REFINE_PROMPT


def refine_transcript(client, raw_transcript: str, ctx: Context) -> str | None:
    """Second-pass LLM refinement. Returns refined text, or None on failure."""
    print("\n  REFINE pass...", end=" ", flush=True)
    t0 = time.time()

    prompt = REFINE_PROMPT.format(
        domain_description=ctx.domain_description or "(no domain description provided)",
        participants_block=ctx.participants_block,
        glossary_block=ctx.glossary_block or "(no glossary provided)",
        raw_transcript=raw_transcript,
        prompt_overlay=ctx.prompt_overlay or "",
    )

    try:
        response = client.models.generate_content(
            model=ctx.model,
            contents=[prompt],
        )
        refined = response.text or ""
        if not refined and response.candidates:
            for c in response.candidates:
                if c.content and c.content.parts:
                    refined = "".join(
                        p.text for p in c.content.parts
                        if hasattr(p, "text") and p.text
                    )

        elapsed = time.time() - t0
        print(f"done ({elapsed:.0f}s, {len(refined)} chars)")
        return refined
    except Exception as e:
        elapsed = time.time() - t0
        print(f"ERROR ({elapsed:.0f}s): {e}")
        return None
