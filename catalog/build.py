"""Build the static site from data/snapshot.json into site/. Offline and deterministic."""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
from pathlib import Path

import markdown

from . import classify as C
from . import extract as X

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "catalog" / "assets"
SYNTH = "Measured on synthetic data in the repo's own tests or demo runs."
DISCLAIMER = (
    "These are portfolio reference builds made with synthetic data and fictional companies. "
    "They are not client deliveries, and no client, revenue or production deployment is claimed."
)
DOMAINS = ["banking", "insurance", "healthcare", "retail", "manufacturing", "energy", "logistics", "legal", "security", "hr"]
DELIVERY = [
    (
        "Discovery",
        "Two to three weeks of mapping one workflow end to end: who does what, which systems hold the data, where errors cost the most, and which decisions must stay with a person. The output is a scored use-case shortlist, a data access plan and a written definition of done.",
    ),
    (
        "Pilot",
        "A narrow build on synthetic or masked data with a golden test set agreed with domain experts up front. Every result is reported with its sample size, and the pilot only moves on when the agreed thresholds are met in CI.",
    ),
    (
        "Production hardening",
        "Retries with budgets, idempotent writes, timeouts, circuit breakers, rate limits, crash-safe resume and load tests sized from token throughput rather than request counts. Infrastructure is written as code and the deploy pipeline stays switched off until it is reviewed.",
    ),
    (
        "Security and compliance",
        "Least-privilege tools, the caller's own permissions passed through, human approval before risky actions, input and output guards, prompt-injection tests, PII masking in logs and traces, a threat model and risk cards mapped to common AI risk frameworks.",
    ),
    (
        "Evaluation and monitoring",
        "Eval gates that block a merge, judges checked for position and length bias, calibrated confidence with abstention, drift monitors, cost per outcome and a feedback loop that turns reviewer corrections into new test cases.",
    ),
]


def esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def md_to_html(md: str, repo: dict) -> str:
    base_raw = f"https://raw.githubusercontent.com/{repo['owner']}/{repo['name']}/{repo['branch']}/"
    base_blob = f"{repo['url']}/blob/{repo['branch']}/"

    def fix(m):
        bang, text, link = m.group(1), m.group(2), m.group(3)
        if re.match(r"^(https?:|#|mailto:)", link):
            return m.group(0)
        link = link.lstrip("./")
        return f"{bang}[{text}]({(base_raw if bang else base_blob) + link})"

    md = re.sub(r"(!?)\[([^\]]*)\]\(([^)\s]+)\)", fix, md)
    md = re.sub(r"```mermaid\n(.*?)```", lambda m: f'<pre class="mermaid">{esc(m.group(1))}</pre>', md, flags=re.S)
    return markdown.markdown(md, extensions=["tables", "fenced_code"])


ACRONYMS = {"ai", "roi", "rag", "soc", "pii", "iam", "qa", "llm", "rl", "bi", "dspy", "lora", "sql"}


def title(name: str) -> str:
    words = name.removeprefix("Jagadish-").split("-")
    return " ".join(w.upper() if w.lower() in ACRONYMS else ("Text2SQL" if w == "text2sql" else w.capitalize()) for w in words)


def load_overrides(path: Path = ROOT / "data" / "overrides.json") -> dict:
    if not path.exists():
        return {}
    return {k: v for k, v in json.loads(path.read_text()).items() if not k.startswith("_")}


def model(snap: dict, overrides: dict | None = None) -> list[dict]:
    overrides = load_overrides() if overrides is None else overrides
    pc = C.featured_test_counts(snap.get("profile_readme", ""), [r["name"] for r in snap["repos"]])
    pc.update(C.profile_test_counts(snap.get("profile_readme", "")))
    items = []
    for r in snap["repos"]:
        r = dict(r, owner=snap["owner"])
        readme = r.get("readme", "")
        tests = C.test_count(r, pc)
        inds, sks = C.industries(r), C.skills(r)
        fw = C.framework(r)
        ov = overrides.get(r["name"], {})
        inds, fw = ov.get("industries", inds), ov.get("framework", fw)
        board = X.evidence_board(r.get("paths", []))
        arch = X.pick(readme, "architecture") or r.get("docs", {}).get("docs/architecture.md", "")
        items.append(
            {
                "repo": r,
                "name": r["name"],
                "title": title(r["name"]),
                "slug": r["name"].lower(),
                "description": r.get("description") or X.intro(readme)[:200],
                "industries": inds,
                "skills": sks[:4],
                "framework": fw,
                "tests": tests,
                "level": C.level(tests, readme),
                "tags": [C.INDUSTRY_LABELS[inds[0]], fw] + [C.SKILL_LABELS[s] for s in sks[:2]],
                "board": f"https://raw.githubusercontent.com/{snap['owner']}/{r['name']}/{r['branch']}/{board}" if board else None,
                "results": X.results(readme),
                "sections": {k: X.pick(readme, k) for k in X.SECTION_KEYS},
                "architecture": arch,
                "intro": X.intro(readme),
            }
        )
    return items


def page(title: str, body: str, depth: int = 0, active: str = "") -> str:
    up = "../" * depth
    nav = [
        ("index.html", "Catalog"),
        ("industries/index.html", "Industries"),
        ("capabilities.html", "Capabilities"),
        ("delivery.html", "How we deliver"),
        ("about.html", "About"),
    ]
    links = "".join(f'<a href="{up}{h}"{" class=on" if t == active else ""}>{t}</a>' for h, t in nav)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · Jagadish Meduri portfolio</title><link rel="stylesheet" href="{up}assets/style.css"></head>
<body><header class="top"><a class="brand" href="{up}index.html">JM · reference builds</a><nav>{links}</nav></header>
<main>{body}</main>
<footer><p>{esc(DISCLAIMER)}</p><p>Generated by the catalog builder from each repo's README and docs.</p></footer>
<script type="module">import m from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";m.initialize({{startOnLoad:true,theme:"dark"}});</script>
</body></html>"""


def fwclass(fw: str) -> str:
    return re.sub(r"\W", "", fw.lower())


def card(it: dict, up: str = "") -> str:
    pills = "".join(f'<span class="pill">{esc(t)}</span>' for t in it["tags"])
    fwc = fwclass(it["framework"])
    t = f"{it['tests']:,} tests" if it["tests"] else "tests not stated"
    return (
        f'<a class="card" href="{up}repos/{it["slug"]}.html" data-ind="{" ".join(it["industries"])}" '
        f'data-skill="{"|".join(it["skills"])}" data-fw="{esc(it["framework"])}" '
        f'data-text="{esc((it["name"] + " " + it["description"] + " " + " ".join(it["tags"])).lower())}">'
        f'<div class="row"><span class="badge fw-{fwc}">{esc(it["framework"])}</span><span class="lvl lvl-{it["level"].lower()}">{it["level"]}</span></div>'
        f'<h3>{esc(it["title"])}</h3><p>{esc(it["description"])}</p><div class="meta">{t}</div><div class="pills">{pills}</div></a>'
    )


def chips(group: str, values: list[tuple[str, str]]) -> str:
    c = f'<button class="chip on" data-group="{group}" data-val="">All</button>'
    return c + "".join(f'<button class="chip" data-group="{group}" data-val="{esc(v)}">{esc(lbl)}</button>' for v, lbl in values)


def home(items: list[dict]) -> str:
    total = sum(i["tests"] or 0 for i in items)
    fws = sorted({i["framework"] for i in items})
    inds = [(k, v) for k, v in C.INDUSTRY_LABELS.items() if any(k in i["industries"] for i in items)]
    body = f"""<section class="hero"><h1>Applied AI reference builds</h1>
<p>{len(items)} working projects across {len(inds)} industries, each with its own tests ({total:,} in total) and an honest list of what is built and what is still planned.</p>
<p class="note">{esc(DISCLAIMER)}</p>
<input id="q" type="search" placeholder="Search by problem, industry or technique, for example fraud, retrieval or approval" aria-label="Search projects"></section>
<section class="filters"><div><span class="flabel">Framework</span>{chips("fw", [(f, f) for f in fws])}</div>
<div><span class="flabel">Industry</span>{chips("ind", inds)}</div>
<div><span class="flabel">Skill</span>{chips("skill", list(C.SKILL_LABELS.items()))}</div></section>
<p id="count" class="count">{len(items)} projects</p>
<section id="grid" class="grid">{"".join(card(i) for i in items)}</section>
<script src="assets/filter.js"></script>"""
    return page("Catalog", body, 0, "Catalog")


def block(title: str, md: str, it: dict) -> str:
    return f"<section><h2>{esc(title)}</h2>{md_to_html(md, it['repo'])}</section>" if md.strip() else ""


def results_list(it: dict) -> str:
    if not it["results"]:
        return "<p>No measured result lines were found in this README.</p>"
    lis = "".join(f"<li>{md_to_html(r, it['repo'])}</li>" for r in it["results"])
    return f'<ul class="results">{lis}</ul><p class="note">{SYNTH}</p>'


def repo_page(it: dict) -> str:
    s = it["sections"]
    board = (
        f'<section><h2>Evidence board</h2><img class="board" src="{it["board"]}" alt="Evidence board for {esc(it["title"])}"></section>'
        if it["board"]
        else ""
    )
    tests = f"{it['tests']:,}" if it["tests"] else "not stated in the README"
    body = f"""<p class="crumb"><a href="../index.html">Catalog</a> / {esc(it["title"])}</p>
<div class="row"><span class="badge fw-{fwclass(it["framework"])}">{esc(it["framework"])}</span><span class="lvl lvl-{it["level"].lower()}">{it["level"]}</span></div>
<h1>{esc(it["title"])}</h1><p class="lead">{esc(it["description"])}</p>
<div class="facts"><div><b>{tests}</b><span>tests (from the README)</span></div><div><b>{esc(C.INDUSTRY_LABELS[it["industries"][0]])}</b><span>main industry</span></div>
<div><a class="btn" href="{it["repo"]["url"]}">Open the repo</a> <a class="btn ghost" href="../case-studies/{it["slug"]}.html">Case study</a></div></div>
{block("Purpose", s["purpose"] or it["intro"], it)}{block("Architecture", it["architecture"], it)}{block("How it works", s["approach"], it)}
{block("How to run it", s["run"], it)}{block("Built vs planned", s["status"], it)}{board}
<section><h2>Measured results</h2>{results_list(it)}</section>"""
    return page(it["title"], body, 1)


def case_page(it: dict) -> str:
    s = it["sections"]
    body = f"""<p class="crumb"><a href="../index.html">Catalog</a> / case study</p><h1>{esc(it["title"])}: case study</h1>
<p class="note">{esc(DISCLAIMER)}</p>
<section><h2>The problem</h2><p>{esc(it["description"])}</p></section>
{block("The approach", s["approach"] or s["purpose"] or it["intro"], it)}
<section><h2>Measured results</h2>{results_list(it)}</section>
{block("Guardrails and governance", s["guardrails"], it) or "<section><h2>Guardrails and governance</h2><p>See the repo README for the controls this build uses.</p></section>"}
{block("Limitations", s["limitations"], it)}
<p><a class="btn" href="{it["repo"]["url"]}">Open the repo</a> <a class="btn ghost" href="../repos/{it["slug"]}.html">Project page</a></p>"""
    return page(it["title"] + " case study", body, 1)


def industry_page(d: str, items: list[dict]) -> str:
    mine = [i for i in items if d in i["industries"]]
    probs = "".join(f"<li><b>{esc(i['title'])}</b>: {esc(i['description'])}</li>" for i in mine)
    res = "".join(
        f'<li><a href="../case-studies/{i["slug"]}.html">{esc(i["title"])}</a>: {md_to_html(i["results"][0], i["repo"])}</li>'
        for i in mine
        if i["results"]
    )
    grid = "".join(card(i, "../") for i in mine)
    empty = "<p>No repo covers this domain yet. It is listed so the gap stays visible.</p>" if not mine else ""
    body = f"""<p class="crumb"><a href="index.html">Industries</a> / {esc(C.INDUSTRY_LABELS[d])}</p><h1>{esc(C.INDUSTRY_LABELS[d])}</h1>
<p class="note">{esc(DISCLAIMER)}</p>{empty}
<section><h2>Business problems worked on</h2><ul>{probs}</ul></section>
<section><h2>Measured results</h2><ul class="results">{res or "<li>None stated yet.</li>"}</ul><p class="note">{SYNTH}</p></section>
<section><h2>Repos that show it</h2><div class="grid">{grid}</div></section>"""
    return page(C.INDUSTRY_LABELS[d], body, 1, "Industries")


def industries_index(items: list[dict]) -> str:
    rows = "".join(
        f'<a class="card" href="{d}.html"><h3>{esc(C.INDUSTRY_LABELS[d])}</h3><p>{sum(d in i["industries"] for i in items)} repos</p></a>'
        for d in DOMAINS
    )
    return page(
        "Industries", f"<h1>Industry solutions</h1><p class='note'>{esc(DISCLAIMER)}</p><div class='grid'>{rows}</div>", 1, "Industries"
    )


def capabilities(items: list[dict]) -> str:
    head = "".join(f"<th>{esc(C.SKILL_LABELS[s])}</th>" for s in C.SKILLS)
    rows = ""
    for d in DOMAINS:
        cells = ""
        for s in C.SKILLS:
            n = sum(d in i["industries"] and s in i["skills"] for i in items)
            cells += f'<td class="h{min(n, 4)}">{n or ""}</td>'
        rows += f'<tr><th><a href="industries/{d}.html">{esc(C.INDUSTRY_LABELS[d])}</a></th>{cells}</tr>'
    body = f"""<h1>Capabilities matrix</h1><p>Each cell counts the repos that are tagged with that industry and that skill. Tags come from the documented rules in the generator, so a repo can count in several cells.</p>
<table class="matrix"><thead><tr><th>Industry</th>{head}</tr></thead><tbody>{rows}</tbody></table>"""
    return page("Capabilities", body, 0, "Capabilities")


def delivery(items: list[dict]) -> str:
    steps = "".join(f"<section class='step'><h2>{i + 1}. {esc(t)}</h2><p>{esc(d)}</p></section>" for i, (t, d) in enumerate(DELIVERY))
    acc = [
        ("Eval gate and judge checks", "llm-evals-observability"),
        ("Prompt-injection and red-team suite", "agent-security-redteam"),
        ("PII detection with keyed pseudonyms", "pii-guard"),
        ("Governed data layer with contracts and lineage", "agentic-data-layer"),
        ("Agent auth with delegated scopes", "agent-auth-security"),
        ("Capacity and cost planner", "llm-capacity-planning"),
        ("Model risk cards and approval gates", "agentic-ai-model-risk"),
        ("Retrieval tuning harness", "rag-optimization"),
    ]
    names = {i["slug"]: i for i in items}
    lis = "".join(f'<li><a href="repos/jagadish-{s}.html">{esc(t)}</a></li>' for t, s in acc if f"jagadish-{s}" in names)
    body = f"""<h1>How we deliver</h1><p>The method below is the one these reference builds follow. It is written as the plan for a real engagement, but nothing here has yet been delivered to a client.</p>
<p class="note">{esc(DISCLAIMER)}</p>{steps}<section><h2>Reusable accelerators</h2><p>Parts already built and tested in the portfolio that a new engagement can start from:</p><ul>{lis}</ul></section>"""
    return page("How we deliver", body, 0, "How we deliver")


def about(items: list[dict]) -> str:
    body = f"""<h1>About this catalog</h1><p>{esc(DISCLAIMER)}</p>
<p>Every number on this site is copied from a repo README by the generator, and every README number comes from a run inside that repo. Results are measured on synthetic data, often with small test sets, so they are regression checks rather than quality claims about real deployments.</p>
<h2>How levels are set</h2><ul><li><b>Advanced</b>: 300 or more tests, or 150 or more for a multi-agent build.</li><li><b>Intermediate</b>: 80 or more tests.</li><li><b>Beginner</b>: fewer than 80 tests, usually a focused study of one technique.</li></ul>
<p>The source of this site is in the <a href="https://github.com/{items[0]["repo"]["owner"] if items else ""}/Jagadish-portfolio-catalog">catalog repo</a>.</p>"""
    return page("About", body, 0, "About")


def build(snap: dict, out: Path, overrides: dict | None = None) -> list[dict]:
    items = model(snap, overrides)
    if out.exists():
        shutil.rmtree(out)
    for sub in ("repos", "case-studies", "industries", "assets"):
        (out / sub).mkdir(parents=True)
    for f in ASSETS.iterdir():
        shutil.copy(f, out / "assets" / f.name)
    (out / "index.html").write_text(home(items))
    (out / "capabilities.html").write_text(capabilities(items))
    (out / "delivery.html").write_text(delivery(items))
    (out / "about.html").write_text(about(items))
    (out / "industries" / "index.html").write_text(industries_index(items))
    for d in DOMAINS:
        (out / "industries" / f"{d}.html").write_text(industry_page(d, items))
    for it in items:
        (out / "repos" / f"{it['slug']}.html").write_text(repo_page(it))
        (out / "case-studies" / f"{it['slug']}.html").write_text(case_page(it))
    summary = [{k: it[k] for k in ("name", "framework", "level", "tests", "industries", "skills")} for it in items]
    (out / "catalog.json").write_text(json.dumps(summary, indent=1))
    (out / ".nojekyll").write_text("")
    return items


if __name__ == "__main__":
    snap_path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/snapshot.json")
    items = build(json.loads(snap_path.read_text()), ROOT / "site")
    print(f"built {len(items)} repo pages, {sum(i['tests'] or 0 for i in items)} tests listed")
