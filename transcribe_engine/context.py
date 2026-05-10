"""Context-pack discovery + loader.

A context pack is a folder containing:
  - transcribe.config.yaml  (required — the entry point)
  - glossary.md             (or glossary/ directory of *.md files)
  - participants.md         (optional — speaker bios)
  - meeting-prompt.md       (optional — extra prompt overlay)

Discovery order:
  1. --context-pack <path>
  2. TRANSCRIBE_CONTEXT_PACK env var
  3. ./transcribe.config.yaml in cwd
  4. None (zero-context fallback — engine still runs, no biasing)
"""
import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class Context:
    glossary: str = ""
    participants: str = ""
    domain_description: str = ""
    language_note: str = ""
    prompt_overlay: str = ""
    model: str = "gemini-3-flash-preview"
    chunk_minutes: int = 10
    preprocess: bool = True
    refine: bool = True
    pack_root: Path | None = None

    @property
    def glossary_block(self) -> str:
        if not self.glossary.strip():
            return ""
        return f"Domain terms — spell exactly as listed:\n{self.glossary}"

    @property
    def participants_block(self) -> str:
        if not self.participants.strip():
            return "No participant list provided. Identify speakers from voice cues and content."
        return self.participants


def discover_pack_path(cli_path: str | None) -> Path | None:
    """Return the path to a context-pack config file, or None."""
    if cli_path:
        p = Path(cli_path).expanduser().resolve()
        if p.is_file():
            return p
        if p.is_dir():
            cfg = p / "transcribe.config.yaml"
            if cfg.is_file():
                return cfg
        raise FileNotFoundError(f"Context pack not found at: {cli_path}")

    env_path = os.environ.get("TRANSCRIBE_CONTEXT_PACK")
    if env_path:
        return discover_pack_path(env_path)

    cwd_cfg = Path.cwd() / "transcribe.config.yaml"
    if cwd_cfg.is_file():
        return cwd_cfg

    return None


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def _read_glossary(pack_root: Path, glossary_field: str) -> str:
    """Glossary can be a single file or a directory of *.md files (concatenated)."""
    target = (pack_root / glossary_field).resolve()
    if target.is_file():
        return _read(target)
    if target.is_dir():
        parts = []
        for md in sorted(target.glob("*.md")):
            parts.append(f"<!-- {md.name} -->\n{_read(md)}")
        return "\n\n".join(parts)
    return ""


def load_context(cli_path: str | None) -> Context:
    """Load a Context object from disk. Falls back to defaults if no pack found."""
    cfg_path = discover_pack_path(cli_path)
    if cfg_path is None:
        return Context()

    if yaml is None:
        raise RuntimeError(
            "PyYAML is required to load context packs. "
            "Install with: pip install pyyaml"
        )

    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    pack_root = cfg_path.parent

    glossary_field = cfg.get("glossary", "glossary.md")
    participants_field = cfg.get("participants", "participants.md")
    overlay_field = cfg.get("prompt_overlay", "")

    return Context(
        glossary=_read_glossary(pack_root, glossary_field),
        participants=_read(pack_root / participants_field) if participants_field else "",
        prompt_overlay=_read(pack_root / overlay_field) if overlay_field else "",
        domain_description=(cfg.get("domain_description") or "").strip(),
        language_note=(cfg.get("language_note") or "").strip(),
        model=cfg.get("model", "gemini-3-flash-preview"),
        chunk_minutes=int(cfg.get("chunk_minutes", 10)),
        preprocess=bool(cfg.get("preprocess", True)),
        refine=bool(cfg.get("refine", True)),
        pack_root=pack_root,
    )
