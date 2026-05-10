# How — User Guide (end to end)

This guide walks you from "I have an audio file" to "I have a structured transcript with the right names, the right jargon, and a growing context anchor that gets smarter every meeting."

## 1. Install

```bash
pip install git+https://github.com/JohnTran-123/transcribe-engine
```

You'll also need `ffmpeg` available on PATH (or installed via `imageio-ffmpeg`, which the package pulls in).

## 2. Get a Gemini API key

1. Go to https://aistudio.google.com/apikey
2. Create a key
3. Set it in your shell:

```bash
export GEMINI_API_KEY=your_key_here       # macOS/Linux
$env:GEMINI_API_KEY="your_key_here"        # Windows PowerShell
```

Or drop it in a `.env` next to your context pack — see `.env.example`.

## 3. Create your context pack

A context pack is just a folder. Start by copying the sample:

```bash
cp -r samples/starter-pack ./my-pack
```

You now have:

```
my-pack/
├── transcribe.config.yaml    # entry point — paths + engine settings
├── glossary.md               # domain terms, acronyms, projects
├── participants.md           # who's in your meetings, voice cues
└── meeting-prompt.md         # optional extra framing
```

Open each file. **Strip the sample content. Replace with your own.** See [context-pack.md](context-pack.md) for the full author's guide.

## 4. First run

```bash
transcribe-engine path/to/meeting.mp3 --context-pack ./my-pack
```

What happens:

```
[Phase 0] Preprocess     noise reduction + volume normalize
[Phase 1] ASR            chunk audio -> Gemini transcribes each chunk with your glossary
[Phase 2] Refine         second LLM pass: corrects errors, attributes speakers, extracts decisions
```

You get two files next to your audio:

- `meeting_raw.md` — Phase 1 output, useful for debugging
- `meeting_transcript.md` — Phase 2 refined, with sections for Decisions / Action Items / Debates / Topics

## 5. Grow your context anchor

This is the part that makes the engine learn over time:

1. Open `meeting_transcript.md`. Skim it.
2. Find every misspelled acronym, mis-attributed speaker, or wrong domain term.
3. Add or fix the entry in `glossary.md` / `participants.md`.
4. Commit your context pack to git. (It IS your institutional memory — version it.)
5. Next meeting: same engine, smarter output.

The longer you run it, the better it gets. That's the point.

## 6. Embedding in another repo

The engine auto-discovers `transcribe.config.yaml` in the current directory:

```bash
cd /any/repo
ls
# transcribe.config.yaml   glossary.md   participants.md   meeting.mp3

transcribe-engine meeting.mp3
# (no --context-pack flag needed — found via cwd)
```

So a teammate's repo can carry its own pack. No copy-paste, no global state.

## 7. Common flags

```bash
transcribe-engine meeting.mp3 --raw                    # skip preprocessing
transcribe-engine meeting.mp3 --no-refine              # skip the second LLM pass
transcribe-engine meeting.mp3 --extra-context agenda.md # inject one-off context
transcribe-engine meeting.mp3 --model gemini-2.5-pro   # override model
transcribe-engine meeting.mp3 --chunk-minutes 5        # smaller chunks for short files
```
