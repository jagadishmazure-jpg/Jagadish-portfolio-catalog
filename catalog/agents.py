"""Read a repo's catalog/agents.json (agent-card/v1) into agent cards.

Invalid files or entries are skipped, never fatal. Links must point inside the publishing repo.
"""

from __future__ import annotations

import json
import re

from . import classify as C

SCHEMA = "agent-card/v1"
LEVELS = {"Beginner", "Intermediate", "Advanced"}
REQUIRED = ("name", "title", "summary")
# Card industry text -> catalog domain. First match wins; no match -> cross-industry.
INDUSTRY_MAP = [
    ("hr", r"\bhr\b|recruit|hiring|talent"),
    ("banking", r"bank|financ|lend|credit|payment"),
    ("insurance", r"insur"),
    ("healthcare", r"health|clinic|pharma|medical"),
    ("retail", r"retail|commerce|consumer"),
    ("manufacturing", r"manufactur"),
    ("energy", r"energy|utilit"),
    ("logistics", r"logistic|travel|supply chain|transport"),
    ("legal", r"legal|contract"),
    ("security", r"security|cyber"),
]


def domain(industry: str) -> str:
    text = industry.lower()
    for key, pat in INDUSTRY_MAP:
        if re.search(pat, text):
            return key
    return "cross"


def badge(tech: str) -> str:
    t = tech.lower()
    for name in ("LangGraph", "LangChain", "Playwright", "Azure"):
        if name.lower() in t:
            return "LangGraph" if name == "LangChain" else name
    if "agent framework" in t:
        return "Agent Framework"
    return "Python"


def parse(repo: dict) -> list[dict]:
    raw = repo.get("agents_json")
    if not raw:
        return []
    try:
        doc = json.loads(raw)
    except ValueError:
        return []
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA or not isinstance(doc.get("agents"), list):
        return []
    base = repo["url"].rstrip("/") + "/"
    out = []
    for a in doc["agents"]:
        if not isinstance(a, dict) or not all(isinstance(a.get(k), str) and a[k].strip() for k in REQUIRED):
            continue
        page = a.get("page") if isinstance(a.get("page"), str) else ""
        if not page.startswith(base):
            page = repo["url"]
        industry = a.get("industry") if isinstance(a.get("industry"), str) else ""
        dom = domain(industry)
        fw = badge(a.get("tech") or "")
        level = a.get("level") if a.get("level") in LEVELS else "Beginner"
        tags = [t for t in a.get("tags", []) if isinstance(t, str)][:2]
        score, cases = a.get("task_score"), a.get("task_cases")
        result = None
        if isinstance(score, (int, float)) and isinstance(cases, int) and cases > 0:
            result = f"Task score {score:.2f} on {cases} synthetic cases"
        out.append(
            {
                "name": a["name"],
                "title": a["title"],
                "description": a["summary"],
                "url": page,
                "repo": repo["name"],
                "framework": fw,
                "level": level,
                "industries": [dom],
                "industry_label": industry or C.INDUSTRY_LABELS[dom],
                "tags": [industry or C.INDUSTRY_LABELS[dom], fw] + tags,
                "skills": ["agents"],
                "tech": a.get("tech") or "",
                "result": result,
            }
        )
    return out
