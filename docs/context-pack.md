# Context Pack — Author's Guide

The context pack is the part of `transcribe-engine` that makes it *yours*. The engine is generic; the pack is your team's spoken language, captured.

## Anatomy

```
my-pack/
├── transcribe.config.yaml    # required — entry point + engine settings
├── glossary.md               # domain terms, acronyms, projects, tools
├── participants.md           # who's in your meetings + voice cues
└── meeting-prompt.md         # optional — extra framing for the refine pass
```

## `transcribe.config.yaml`

```yaml
# Paths (relative to this file)
glossary: glossary.md             # or "glossary/" for a multi-file directory
participants: participants.md
prompt_overlay: meeting-prompt.md # optional — leave blank to skip

# Engine settings (overridable via CLI flags)
model: gemini-3-flash-preview
chunk_minutes: 10
preprocess: true
refine: true

# Free-text framing — injected into ASR + refine prompts
domain_description: |
  One paragraph describing your working environment.
  Example: "Engineering team standups at Acme Synthetics. Speakers
  are technical staff discussing materials R&D."

language_note: |
  Optional — only fill if your meetings have non-default language behavior.
  Example: "Speakers may code-switch between English and Spanish mid-sentence."
```

## `glossary.md`

The most important file. **Use exact spellings — whatever you write here is what the model will produce.**

### Recommended structure

Group by category. Keep entries short. Add a one-line note if context matters.

```markdown
## People (cross-reference with participants.md)
- Name (role): voice cues / common topics / common phrases

## Projects
- ProjectName: short description of what it is

## Acronyms
- ABC: Asynchronous Build Coordinator (internal tool)
- DEF: Data Exchange Format (industry-standard term)

## Domain jargon
- backpressure: rate-limiting in our pipeline; speakers say "back-pressure" or "BP"
- "the lab": shorthand for the materials testing facility on floor 3

## Tools / Infra
- Postgres-prod: the main production database (NOT to be confused with Postgres-staging)
- the dashboard: refers to the internal Grafana board, never to the public website

## Customers / Stakeholders
- Acme Co: largest customer; speakers may say "Acme" alone
```

### Growing it

After each meeting:

1. Open `{name}_transcript.md`.
2. Skim for: misspelled acronyms, wrong-name speaker tags, wrong domain terms.
3. Add the correct version to the right section of `glossary.md`.
4. `git commit` the change.

That's it. No need to overthink. The glossary grows organically, weighted toward what actually appears in your meetings.

### When to split into a directory

If `glossary.md` passes ~500-1000 lines, switch to a directory:

```
my-pack/
└── glossary/
    ├── 00-people.md
    ├── 10-projects.md
    ├── 20-acronyms.md
    ├── 30-jargon.md
    └── 40-tools.md
```

Update `transcribe.config.yaml`:

```yaml
glossary: glossary/   # engine concatenates all *.md in alpha order
```

The numeric prefixes (`00-`, `10-`) control order if order matters.

## `participants.md`

Speaker-attribution hints for Phase 2. The model uses voice cues + content cues + this file to assign speaker names.

```markdown
## Maya Chen (CTO)
- Voice: female, deeper register, fast pace
- Style: drives architecture decisions, pushes back on scope creep
- Common phrases: "what's the failure mode here?", "let's name the constraint"

## Diego Rivera (Senior Engineer)
- Voice: male, mid register, measured pace
- Style: asks scoping questions, surfaces edge cases
- Common phrases: "before we go further...", "what about <edge case>"

## Priya Patel (PM)
- Voice: female, mid register, brisk
- Style: facilitates, owns roadmap, redirects to action items
- Common phrases: "let's land this", "who's owning that?"
```

**Tip:** include not just bios but **distinctive verbal patterns**. The model uses them to disambiguate.

## `meeting-prompt.md` (optional)

Extra rules appended to the refine prompt. Useful for:

- Custom output sections beyond the default Decisions / Actions / Debates / Topics
- Domain-specific formatting rules (e.g., "always render dollar amounts as $X,XXX")
- Project-specific corrections (e.g., "if you hear 'V-CPI', it's always 'V_CPI' in writing")

```markdown
## Additional output sections
After the Topics section, add:

**## Risks Surfaced**
For each risk mentioned: the risk, who raised it, mitigation if discussed.

**## Open Questions**
Anything raised but not answered, with the asker.

## Formatting rules
- Render code identifiers in `backticks`
- Render product names in **bold**
```

Leave this file empty if you don't need it.

## Versioning your pack

Your context pack should live in git. It's the most valuable artifact this tool produces — months of accumulated institutional memory, captured.

Recommended:

- **Public team pack:** in a shared internal repo, everyone contributes.
- **Personal pack:** in your dotfiles or a personal repo.
- **Project pack:** at the root of the project repo, alongside the code.

The engine doesn't care where the pack lives. It only cares that you point at it (or that the cwd contains a `transcribe.config.yaml`).
