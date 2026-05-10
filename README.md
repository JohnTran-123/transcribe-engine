# transcribe-engine

> **Multi-pass transcription with a growing context anchor.** Built for recurring meetings where the same people, same jargon, and same projects come up again and again — and a generic ASR keeps getting them wrong.

```
audio file  →  preprocess  →  Gemini ASR (chunked)  →  LLM refine  →  structured transcript
                                       ↑                       ↑
                                       └──── your context pack ┘
                                            (glossary + participants + domain framing)
```

The engine is generic. The context pack is yours, lives in your repo, and **grows over time** — every meeting teaches it a new term, a new name, a new project. Generic ASR gives you the same mistakes forever. This gives you compounding accuracy.

## Why use this over Whisper / generic Gemini?

- **Context injection at both passes** — your glossary biases ASR token choice (Phase 1) AND grounds the refinement (Phase 2). [30.7% Entity WER reduction in published benchmarks](docs/why.md).
- **Structured output, not just words** — the refine pass extracts Decisions, Action Items, Debates, and Topics automatically.
- **Speaker attribution from voice cues + content cues** — the participant list isn't a label, it's a hint.
- **Portable** — drop a `transcribe.config.yaml` into any repo, the engine auto-discovers it.

## Quickstart

```bash
pip install git+https://github.com/JohnTran-123/transcribe-engine

export GEMINI_API_KEY=your_key   # https://aistudio.google.com/apikey

# Copy and personalize the starter pack
cp -r samples/starter-pack ./my-pack
# ...edit my-pack/glossary.md, participants.md, transcribe.config.yaml...

transcribe-engine meeting.mp3 --context-pack ./my-pack
```

You get `meeting_raw.md` (Phase 1) and `meeting_transcript.md` (Phase 2 — the structured one).

## Embedding in another repo

Drop `transcribe.config.yaml` + `glossary.md` + `participants.md` at the root of any project. From that directory:

```bash
transcribe-engine meeting.mp3
# (no flag needed — engine auto-discovers cwd config)
```

## Documentation

| Doc | What it covers |
|---|---|
| [docs/how.md](docs/how.md) | User guide, end-to-end |
| [docs/what.md](docs/what.md) | Engine architecture (3 phases, 6 modules) |
| [docs/why.md](docs/why.md) | Design rationale (multi-pass + prompt biasing + growing anchor) |
| [docs/context-pack.md](docs/context-pack.md) | How to author and grow your context pack |

## Sample pack

[samples/starter-pack/](samples/starter-pack/) — fully fictional Acme Synthetics example. Copy it, rename it, replace every line with your own.

## Status

`v0.1.0` — alpha. Working. Used in production by the author. Bug reports welcome via Issues.

## License

MIT — see [LICENSE](LICENSE).
