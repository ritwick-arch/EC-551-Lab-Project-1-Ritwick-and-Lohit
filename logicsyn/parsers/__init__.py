"""Input formats: one expression, Espresso PLA, or combinational BLIF."""
from pathlib import Path

from .blif import parse_blif
from .expr import parse_expr
from .pla import parse_pla

PARSERS = {"expr": parse_expr, "pla": parse_pla, "blif": parse_blif}


def load_file(path, fmt=None):
    path = Path(path)
    fmt = fmt or {".pla": "pla", ".blif": "blif"}.get(path.suffix.lower(), "expr")
    return PARSERS[fmt](path.read_text(encoding="utf-8"), path.stem)
