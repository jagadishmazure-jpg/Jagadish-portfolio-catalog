import json
from pathlib import Path

from catalog import agents as A
from catalog import build as B

REPO = {"name": "Demo-usecases", "url": "https://github.com/o/Demo-usecases"}


def doc(agents, schema="agent-card/v1"):
    return dict(REPO, agents_json=json.dumps({"schema": schema, "repo": REPO["url"], "agents": agents}))


GOOD = {
    "name": "resume-match",
    "title": "Resume matcher",
    "summary": "Matches synthetic resumes to roles.",
    "level": "Intermediate",
    "tech": "Rule parser",
    "industry": "HR and recruiting",
    "tags": ["fairness", "pii", "extra"],
    "page": "https://github.com/o/Demo-usecases/blob/main/docs/agents/resume-match.md",
    "task_score": 1.0,
    "task_cases": 12,
}


def test_parse_good_card():
    (a,) = A.parse(doc([GOOD]))
    assert a["title"] == "Resume matcher" and a["level"] == "Intermediate" and a["framework"] == "Python"
    assert a["industries"] == ["hr"] and a["tags"] == ["HR and recruiting", "Python", "fairness", "pii"]
    assert a["url"].endswith("resume-match.md") and a["result"] == "Task score 1.00 on 12 synthetic cases"


def test_missing_or_bad_file_is_ignored():
    assert A.parse(REPO) == []
    assert A.parse(dict(REPO, agents_json="{not json")) == []
    assert A.parse(doc([GOOD], schema="other/v9")) == []


def test_bad_entries_skipped_and_unsafe_link_replaced():
    bad = dict(GOOD, title="")
    evil = dict(GOOD, name="x", page="https://evil.example/phish")
    out = A.parse(doc([bad, evil, "nope"]))
    assert len(out) == 1 and out[0]["url"] == REPO["url"]


def test_unknown_level_and_industry_defaults():
    (a,) = A.parse(doc([dict(GOOD, level="Expert", industry="Productivity", task_score=None)]))
    assert a["level"] == "Beginner" and a["industries"] == ["cross"] and a["result"] is None


def test_domain_and_badge_maps():
    assert A.domain("Financial services") == "banking" and A.domain("Travel and hospitality") == "logistics"
    assert A.domain("Legal") == "legal" and A.domain("Retail") == "retail"
    assert A.badge("LangGraph supervisor") == "LangGraph" and A.badge("SQLite + template planner") == "Python"


def _site(tmp_path):
    snap = json.loads((Path(__file__).parent / "fixtures" / "snapshot.json").read_text())
    snap["repos"].append(
        dict(
            doc([GOOD, dict(GOOD, name="b", title="Clause checker", industry="Legal")]),
            branch="main",
            description="d",
            topics=[],
            readme="",
            docs={},
            paths=["catalog/agents.json"],
        )
    )
    B.build(snap, tmp_path / "s", {})
    return tmp_path / "s"


def test_home_has_agent_section_cards_filterable(tmp_path):
    h = (_site(tmp_path) / "index.html").read_text()
    sec = h[h.index('id="enterprise-agents"') :]
    assert "Enterprise use-case agents" in sec and sec.count('class="card agent"') == 2
    assert 'data-fw="Python"' in sec and 'data-ind="hr"' in sec and 'data-text="' in sec
    assert 'href="https://github.com/o/Demo-usecases/blob/main/docs/agents/resume-match.md"' in sec
    assert "2 agents" in h


def test_agents_on_matching_industry_pages_only(tmp_path):
    s = _site(tmp_path)
    assert "Resume matcher" in (s / "industries" / "hr.html").read_text()
    assert "Clause checker" in (s / "industries" / "legal.html").read_text()
    assert "Resume matcher" not in (s / "industries" / "legal.html").read_text()
    assert len(json.loads((s / "agents.json").read_text())) == 2


def test_filter_script_covers_agent_cards():
    js = (Path(B.ASSETS) / "filter.js").read_text()
    assert "#enterprise-agents .card" in js


def test_agents_page_has_search_chips_and_cards(tmp_path):
    p = (_site(tmp_path) / "agents.html").read_text()
    assert 'id="q"' in p and 'data-group="fw"' in p and 'data-group="ind"' in p and 'data-group="lvl"' in p
    assert p.count('class="card agent"') == 2 and 'data-lvl="Intermediate"' in p
