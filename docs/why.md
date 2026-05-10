# Why — Design Rationale

The story behind every choice.

## Why this exists at all

Generic transcription tools (Whisper, off-the-shelf Gemini ASR) treat every recording as a fresh start. They don't know your acronyms, your colleagues' names, your project codenames, or your team's running jokes. So they get them wrong — every meeting, the same way.

But most working environments are **repetitive**. The same five people. The same dozen acronyms. The same recurring projects. There's a fixed institutional vocabulary that should be carried *into* the model, not relearned by accident.

`transcribe-engine` is built around that observation. It's not a smarter ASR — it's a **context-anchored ASR**. The engine is generic; the context is yours, owned by you, and grows over time.

## Why multi-pass

A single ASR pass is fundamentally limited: the model has to commit to a transcription before it has full context. Multi-pass beats single-pass on every benchmark we've seen.

| Paper | Year | Finding |
|---|---|---|
| HyPoradise (ICLR 2024) | 2024 | LLMs surpass traditional re-ranking for ASR correction; up to 30% WER reduction |
| 3-Stage ASR Framework | 2025 | Detection + correction + verification yields 21% CER reduction |
| Lightweight Prompt Biasing | 2025 | Glossary injection at the prompt level: 30.7% Entity WER reduction |

So we do two passes. Phase 1 is fast and committed. Phase 2 reads the whole transcript with the full glossary and structures it.

## Why context injection (not fine-tuning)

Fine-tuning a transcription model on your jargon would work — and is wildly expensive, retraining-required, and quickly stale. Prompt-level context injection gives ~80% of the benefit at ~0% of the cost. The 2025 prompt-biasing paper above is the smoking gun.

Our trick: inject the glossary at **both** passes. Phase 1 uses it as a token-bias hint while listening. Phase 2 uses it as ground truth while correcting.

## Why a "growing context anchor"

Here's the unique angle. A static glossary captures whatever you happened to know on day one. A **growing** glossary captures whatever you've ever learned.

The intended workflow:

1. Run engine on a meeting.
2. Read the output. Find errors.
3. Add the missing terms / fix the wrong attributions in your context pack.
4. Commit the pack to git.
5. Next meeting is smarter. Repeat.

Over months, your context pack becomes a **map of your team's spoken language**. New hires can read it. New tools can consume it. The institutional memory stops living in five people's heads.

## Why Gemini

We tried Whisper + GPT-4o (a common 2-pass setup). Gemini wins on:

- **Native multi-modal:** one call per chunk, audio + text together. No separate ASR step that throws away acoustic information.
- **Long context:** the refine pass can read a 2-hour transcript at once. GPT-4o's effective context is shorter and more expensive.
- **Cost:** Gemini Flash is cheap enough to run on every recording.
- **Multi-lingual:** handles code-switching out of the box.

If a better model arrives, the swap is one line of config. The engine isn't married to Gemini.

## Why preprocess

Most meeting recordings are not studio audio. They're laptop mic, conference room, Zoom-compressed. Two cheap operations make a big difference:

- **Spectral-gating noise reduction** (`noisereduce`) — kills constant background hum without destroying speech
- **Peak normalization** to -1dB — ASR models are sensitive to volume

Preprocessing is optional. If you have clean audio, skip it with `--raw`.

## Why batch (not realtime)

Meetings are async products. You record now, you read later. Batch buys us:

- Multi-pass refinement (impossible in realtime)
- Long-context glossary injection (impossible in chunks)
- Structure extraction over the whole transcript (impossible incrementally)

The price is latency. We pay it because the output quality difference is huge.

## Why this shape (engine + pack)

Engine and context are fundamentally different things:

- **Engine** is code. Versioned by maintainers. Stable interface. Updates rarely.
- **Pack** is content. Versioned by you. Updates after every meeting.

Coupling them would mean every glossary update is a code change. Decoupling them means the engine can be a library that 100 different teams use with 100 different packs, each one carrying its own institutional memory.

That's the bet.
