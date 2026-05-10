# What — Engine Architecture

Three phases, six modules, one config file. That's the whole engine.

## Pipeline

```
audio file
   |
   v
[Phase 0] Preprocess         noisereduce + peak normalization (optional)
   |
   v
[Phase 1] ASR                ffmpeg-split into N-min chunks
                             each chunk -> Gemini multimodal call with
                             { audio, ASR_PROMPT(glossary, participants, domain) }
                             output: raw transcript with timestamps + speaker tags
   |
   v
[Phase 2] Refine             single LLM call over raw transcript with
                             REFINE_PROMPT(glossary, participants, raw)
                             output: corrected + speaker-attributed +
                             structured (Decisions / Actions / Debates / Topics)
   |
   v
{filename}_transcript.md
```

## Module map

```
transcribe_engine/
├── cli.py            argparse, env handling, main entry
├── pipeline.py       orchestrates the 3 phases, handles file IO
├── preprocess.py     noisereduce + peak-normalize via ffmpeg
├── asr.py            chunking + chunked Gemini ASR
├── refine.py         single-shot refinement LLM call
├── context.py        loads transcribe.config.yaml + glossary + participants
└── prompts.py        ASR_PROMPT and REFINE_PROMPT templates (no domain content)
```

## Where context is injected

Two prompt templates, three injection points each:

| Injection | ASR_PROMPT (per chunk) | REFINE_PROMPT (one-shot) |
|---|---|---|
| `{domain_description}` | yes — frames the recording | yes — frames the editor's role |
| `{glossary_block}` | yes — biases ASR token choice | yes — ground truth for correction |
| `{participants_block}` | no | yes — drives speaker attribution |
| `{language_note}` | yes — multi-lingual hint | (inherits from domain) |
| `{prompt_overlay}` | no | yes — your custom rules |
| `{extra_context}` | yes — one-off per run | no |

The engine itself contains zero domain knowledge. Every domain-specific token comes from your context pack.

## Data flow at runtime

1. **`cli.main()`** — parses args, sets up Gemini client.
2. **`context.load_context()`** — discovers config (cwd / env / flag), reads glossary + participants, returns a `Context` dataclass.
3. **`pipeline.run()`** — calls preprocess → ASR → refine, writes outputs.
4. **`asr.transcribe_chunks()`** — for each chunk, formats `ASR_PROMPT` with the loaded `Context`, uploads audio, calls Gemini.
5. **`refine.refine_transcript()`** — formats `REFINE_PROMPT` with the loaded `Context` + the raw transcript from step 4, calls Gemini.

## Outputs

| File | When |
|---|---|
| `{name}_raw.md` | Always — Phase 1 output, useful for diffing against refined |
| `{name}_transcript.md` | When refine is enabled (default) — Phase 2 output |

## Dependencies

- **Required:** `google-genai` (Gemini SDK), `pyyaml` (config parsing)
- **Recommended:** `imageio-ffmpeg` (bundled ffmpeg binary), `noisereduce` + `soundfile` + `scipy` + `numpy` (preprocessing)
- **External:** ffmpeg on PATH (auto-handled if `imageio-ffmpeg` is installed)

## What it is NOT

- Not realtime — batch only. Meetings are async.
- Not a speaker-diarization library — it leans on Gemini's voice differentiation + your participant list.
- Not a search/RAG layer — it produces transcripts. Index them with your tool of choice.
- Not GUI — it's a CLI + Python module.
