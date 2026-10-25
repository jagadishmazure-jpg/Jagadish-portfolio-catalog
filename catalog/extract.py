"""Pull sections and measured results out of a README."""

from __future__ import annotations

import re

SECTION_KEYS = {
    "purpose": r"recruiter summary|purpose|why|problem|overview|what (it|this) (is|does|shows)",
    "architecture": r"architecture",
    "approach": r"how it works|approach|design",
    "run": r"how to run|quick ?start|run it|getting started|usage|running",
    "status": r"built vs\.? planned|built and planned|status",
    "results": r"results|measured|numbers|proof|benchmark|evaluation",
    "guardrails": r"guardrail|security|governance|safety|controls",
    "limitations": r"limitation|known (failures|issues|misses)",
}
METRIC_WORDS = re.compile(
    r"recall|precision|auc|accuracy|p50|p95|%|blocked|reduced|saved|from [\d.]+ to [\d.]+|\bvs\b|score|rate|wape|f1", re.I
)


def sections(md: str) -> list[tuple[str, int, str]]:
    """Split markdown into (heading, level, body) tuples, ignoring fenced code."""
    out, head, lvl, buf, fence = [], "", 0, [], False
    for line in md.splitlines():
        if line.strip().startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            out.append((head, lvl, "\n".join(buf).strip()))
            head, lvl, buf = m.group(2).strip(), len(m.group(1)), []
        else:
            buf.append(line)
    out.append((head, lvl, "\n".join(buf).strip()))
    return out


def pick(md: str, key: str) -> str:
    pat = re.compile(SECTION_KEYS[key], re.I)
    for head, _, body in sections(md):
        if head and pat.search(head) and body:
            return body
    return ""


def intro(md: str) -> str:
    """First real paragraph under the title (skips badges and blank lines)."""
    for _, _, body in sections(md)[:3]:
        for para in re.split(r"\n\s*\n", body):
            p = para.strip()
            if p and not p.startswith(("![", "[![", "<", "|", "```")) and len(p) > 40:
                return p
    return ""


def results(md: str, limit: int = 5) -> list[str]:
    """Lines with a number and a metric word, from the results section first, then anywhere."""
    seen, out = set(), []
    for source in (pick(md, "results"), pick(md, "purpose"), md):
        for raw in source.splitlines():
            line = raw.strip().lstrip("-*0123456789. ").strip()
            if line.startswith(("|", "```", "!", "<", "#")) or len(line) < 25 or len(line) > 400:
                continue
            if re.search(r"\d", line) and METRIC_WORDS.search(line) and line not in seen:
                seen.add(line)
                out.append(line)
            if len(out) >= limit:
                return out
    return out


def evidence_board(paths: list[str]) -> str | None:
    imgs = [p for p in paths if p.lower().endswith((".png", ".jpg", ".svg")) and re.search(r"evidence|board", p.lower())]
    imgs.sort(key=lambda p: (0 if "evidence" in p.lower() else 1, len(p)))
    return imgs[0] if imgs else None
