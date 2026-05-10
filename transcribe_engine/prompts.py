"""Prompt templates. Pure templates — no domain content, no hard-coded names.

All domain knowledge enters via the context pack (see context.py).
"""

ASR_PROMPT = """Transcribe this audio recording verbatim in its original language(s).

This is chunk {chunk_num}/{total_chunks} (minutes {start_min}-{end_min}) of a longer recording.

{domain_description}

{language_note}

{glossary_block}

{extra_context}

Transcription rules:
1. Transcribe EVERYTHING verbatim — do not summarize or skip any speech.
2. Preserve the original language(s) as spoken. Do not translate.
3. When you detect a different speaker's voice, write: **[Speaker: short description]** (e.g. [Speaker: male, deeper voice]).
4. Include timestamps every 30-60 seconds: **[MM:SS]**.
5. If a word is unclear, write **[unclear]** rather than guessing.
6. For overlapping speech, transcribe what you can hear and mark **[overlap]**.
7. Preserve filler words only when they carry meaning. Skip pure hesitation noise.
8. When speakers debate or disagree, capture BOTH positions clearly.
9. Mark key moments: decisions with **[DECISION]**, action items with **[ACTION]**, questions with **[QUESTION]**.
"""


REFINE_PROMPT = """You are an expert meeting transcript editor. Correct and structure this raw meeting transcript that was produced by an automatic speech recognition system. The raw output contains errors — especially in domain terminology, speaker attribution, and complex multi-party arguments.

## Working Environment
{domain_description}

## Participants
{participants_block}

## Domain Glossary (use these EXACT spellings)
{glossary_block}

## Raw Transcript
{raw_transcript}

## Instructions

### Phase 1: Error Correction
- Fix domain term misspellings using the glossary above as ground truth.
- Fix obviously wrong diacritics, accents, or phonetic mishearings.
- Remove pure repetition artifacts from the ASR (looping/stuttering that isn't real speech).
- Keep genuine speech patterns (real hesitations, self-corrections by speakers).

### Phase 2: Speaker Identification
- Use the participant list above + voice cues + content cues to assign speaker names where possible.
- If uncertain about a speaker, use [Speaker ?] rather than guessing wrong.

### Phase 3: Structure Extraction
At the END of the corrected transcript, add these sections:

**## Decisions Made**
List every decision with: what was decided, who decided, timestamp.

**## Action Items**
List every commitment with: who, what, deadline (if mentioned).

**## Key Arguments & Debates**
For each disagreement: the question, each person's position, the resolution (or note if unresolved).

**## Topics Covered**
Bulleted list with timestamp ranges.

### Output Format
- Use markdown headers (##) for major topic shifts.
- Use **bold** for speaker names: **Name:**
- Preserve original-language text as-is. Do not translate.
- Include timestamps [MM:SS] every 1-2 minutes.
- Mark remaining uncertainties with [?].

{prompt_overlay}
"""
