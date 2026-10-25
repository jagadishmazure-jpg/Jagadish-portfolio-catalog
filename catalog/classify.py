"""Rules that turn a repo snapshot into catalog fields. Every rule is documented in docs/how-it-works.md."""

from __future__ import annotations

import re

INDUSTRIES = {
    "banking": ["bank", "lender", "mortgage", "credit", "fraud", "loan", "payment", "fintech"],
    "insurance": ["insur", "claim", "underwrit", "fnol", "policyholder"],
    "healthcare": ["health", "clinical", "hospital", "patient", "pharma", "medical"],
    "retail": ["retail", "grocer", "shop", "marketplace", "seller", "commerce", "checkout", "food-delivery"],
    "manufacturing": ["manufactur", "maintenance", "factory", "food-ingredients", "turbine", "batch release"],
    "energy": ["energy", "grid", "utility", "utilities", "outage", "wind turbine"],
    "logistics": ["logistic", "warehouse", "coldchain", "cold chain", "supply chain", "airline", "fleet", "shipment"],
    "legal": ["legal", "contract", "clause", "compliance", "e-signature"],
    "security": ["security", "soc", "redteam", "red team", "identity", "iam", "auth", "pii", "threat", "attack"],
    "hr": ["recruit", "hiring", "hr", "talent acquisition", "payroll", "job applicant"],
}
INDUSTRY_LABELS = {
    "banking": "Banking & lending",
    "insurance": "Insurance",
    "healthcare": "Healthcare & life sciences",
    "retail": "Retail & commerce",
    "manufacturing": "Manufacturing",
    "energy": "Energy & utilities",
    "logistics": "Logistics & travel",
    "legal": "Legal & contracts",
    "security": "Security operations",
    "hr": "HR & recruiting",
    "cross": "Cross-industry",
}
SKILLS = {
    "agents": ["agent", "multi-agent", "orchestrat", "tool call", "human approval"],
    "retrieval": ["rag", "retriev", "search", "rerank", "vector", "graphrag", "text-to-sql", "text2sql"],
    "security": ["security", "guard", "injection", "pii", "auth", "identity", "threat", "redteam"],
    "evaluation": ["eval", "judge", "benchmark", "calibrat", "golden set", "observab", "trace"],
    "data": ["data", "lakehouse", "lineage", "dataset", "etl", "medallion", "forecast"],
    "cloud": ["azure", "terraform", "bicep", "cloud", "container apps", "finops", "deploy"],
    "system design": ["system design", "latency", "capacity", "scale", "throughput", "cache", "streaming", "inference"],
}
SKILL_LABELS = {k: k.title() if k != "system design" else "System design" for k in SKILLS}

TEST_RE = re.compile(r"\*{0,2}(\d[\d,]*)\s+(?:automated\s+|offline\s+)?tests\b", re.I)


def _blob(repo: dict) -> str:
    return " ".join([repo["name"].replace("-", " "), repo.get("description", ""), " ".join(repo.get("topics", []))]).lower()


def _has(text: str, word: str) -> bool:
    """Match at a word start, so 'soc' does not match 'social' but 'insur' matches 'insurer'."""
    tail = r"\b" if len(word) <= 4 else ""
    return re.search(r"\b" + re.escape(word) + tail, text) is not None


def industries(repo: dict) -> list[str]:
    from .extract import intro

    name = repo["name"].lower()
    hits = [k for k, words in INDUSTRIES.items() if any(_has(_blob(repo), w) for w in words)]
    if not hits:
        # Only when name, description and topics say nothing: look at the README's first paragraph.
        text = intro(repo.get("readme", "")).lower().replace("recruiter summary", "")[:400]
        hits = [k for k, words in INDUSTRIES.items() if any(_has(text, w) for w in words)]
    # Name hits first so the primary industry follows the repo name.
    hits.sort(key=lambda k: 0 if any(_has(name.replace("-", " "), w) for w in INDUSTRIES[k]) else 1)
    return hits or ["cross"]


def skills(repo: dict) -> list[str]:
    text = _blob(repo) + " " + repo.get("readme", "")[:4000].lower()
    scored = [(sum(text.count(w) for w in words), k) for k, words in SKILLS.items()]
    return [k for n, k in sorted(scored, key=lambda x: -x[0]) if n > 0]


def framework(repo: dict) -> str:
    """Badge = the main framework, decided by the first rule that matches."""
    name, readme = repo["name"].lower(), repo.get("readme", "").lower()
    if "langchain" in name or "langgraph" in name:
        return "LangGraph"
    if "playwright" in name:
        return "Playwright"
    if readme.count("agent framework") >= 2:
        return "Agent Framework"
    if readme.count("langgraph") >= 2:
        return "LangGraph"
    if "numpy" in readme and ("from scratch" in readme or "scratch" in name):
        return "NumPy"
    if "azure" in name or "fabric" in name or readme.count("azure") >= 20:
        return "Azure"
    return "Python"


def test_count(repo: dict, profile_counts: dict[str, int]) -> int | None:
    """The profile README is reconciled against real runs, so it wins; the repo README is the fallback."""
    if repo["name"] in profile_counts:
        return profile_counts[repo["name"]]
    m = TEST_RE.search(repo.get("readme", ""))
    if m:
        return int(m.group(1).replace(",", ""))
    return None


def featured_test_counts(profile_md: str, names: list[str]) -> dict[str, int]:
    """Parse '554 agentic-ai + 116 agent platform + ...' and match each label to the shortest repo name holding its words."""
    m = re.search(r"featured repositories \((.*?)\)\s+and", profile_md, re.S)
    if not m:
        return {}
    out = {}
    flat = re.sub(r"\([^()]*\)", "", m.group(1))
    for num, label in re.findall(r"(\d[\d,]*)\s+([A-Za-z][A-Za-z -]*?)(?=\s*(?:\+|,|$))", flat):
        words = set(re.split(r"[\s-]+", label.lower().strip()))
        hits = [n for n in names if words <= set(n.lower().split("-"))]
        if hits:
            out[min(hits, key=len)] = int(num.replace(",", ""))
    return out


def profile_test_counts(profile_md: str) -> dict[str, int]:
    """Read the Tests column of the profile README table as a fallback."""
    out = {}
    for line in profile_md.splitlines():
        m = re.match(r"\|\s*\[\*\*([\w.-]+)\*\*\].*\|\s*(\d[\d,]*)[^|]*\|\s*$", line)
        if m:
            out[m.group(1)] = int(m.group(2).replace(",", ""))
    return out


def level(tests: int | None, readme: str) -> str:
    """Advanced: 300+ tests, or 150+ with multi-agent. Intermediate: 80+. Otherwise Beginner."""
    t = tests or 0
    multi = "multi-agent" in readme.lower()
    if t >= 300 or (multi and t >= 150):
        return "Advanced"
    if t >= 80:
        return "Intermediate"
    return "Beginner"
