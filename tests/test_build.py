import json
from pathlib import Path

from catalog import build as B

SNAP = json.loads((Path(__file__).parent / "fixtures" / "snapshot.json").read_text())


def built(tmp_path):
    items = B.build(SNAP, tmp_path / "site", {})
    return items, tmp_path / "site"


def test_one_page_per_repo_and_case_study(tmp_path):
    items, site = built(tmp_path)
    assert len(items) == 2
    for it in items:
        assert (site / "repos" / f"{it['slug']}.html").exists()
        assert (site / "case-studies" / f"{it['slug']}.html").exists()


def test_home_has_search_cards_and_chips(tmp_path):
    _, site = built(tmp_path)
    h = (site / "index.html").read_text()
    assert 'id="q"' in h and h.count('class="card"') == 2
    assert 'data-group="fw"' in h and 'data-group="ind"' in h and 'data-group="skill"' in h


def test_card_fields(tmp_path):
    items, site = built(tmp_path)
    big = next(i for i in items if i["name"] == "Demo-bank-fraud-agents")
    assert big["tests"] == 350 and big["level"] == "Advanced"
    assert big["industries"][0] == "banking"
    small = next(i for i in items if i["name"] == "Demo-small-lab")
    assert small["tests"] == 12 and small["level"] == "Beginner"
    assert small["description"].startswith("A short study")


def test_repo_page_content(tmp_path):
    _, site = built(tmp_path)
    p = (site / "repos" / "demo-bank-fraud-agents.html").read_text()
    for s in ("Purpose", "Architecture", "How to run it", "Built vs planned", "Evidence board", "Measured results", "Open the repo"):
        assert s in p
    assert '<pre class="mermaid">' in p
    assert "https://raw.githubusercontent.com/example-owner/Demo-bank-fraud-agents/main/docs/evidence_board.png" in p
    c = (site / "case-studies" / "demo-bank-fraud-agents.html").read_text()
    assert "https://github.com/example-owner/Demo-bank-fraud-agents/blob/main/docs/x.md" in c


def test_numbers_labelled_synthetic(tmp_path):
    _, site = built(tmp_path)
    for f in ["case-studies/demo-bank-fraud-agents.html", "industries/banking.html"]:
        assert B.SYNTH in (site / f).read_text()


def test_disclaimer_every_page(tmp_path):
    _, site = built(tmp_path)
    pages = list(site.rglob("*.html"))
    assert len(pages) >= 2 * 2 + 15
    for p in pages:
        assert "not client deliveries" in p.read_text()


def test_all_ten_domains_and_matrix(tmp_path):
    _, site = built(tmp_path)
    for d in B.DOMAINS:
        assert (site / "industries" / f"{d}.html").exists()
    m = (site / "capabilities.html").read_text()
    assert m.count("<tr><th><a") == len(B.DOMAINS)


def test_delivery_page_phases(tmp_path):
    _, site = built(tmp_path)
    d = (site / "delivery.html").read_text()
    for t, _ in B.DELIVERY:
        assert t in d
    assert "Reusable accelerators" in d


def test_rebuild_is_deterministic(tmp_path):
    B.build(SNAP, tmp_path / "a", {})
    B.build(SNAP, tmp_path / "b", {})
    for p in (tmp_path / "a").rglob("*.html"):
        assert p.read_text() == (tmp_path / "b" / p.relative_to(tmp_path / "a")).read_text()


def test_new_repo_appears_on_rerun(tmp_path):
    snap = json.loads(json.dumps(SNAP))
    snap["repos"].append(
        {
            "name": "Demo-recruiting-fairness-agents",
            "description": "Fair matching",
            "topics": [],
            "url": "https://github.com/example-owner/Demo-recruiting-fairness-agents",
            "branch": "main",
            "readme": "",
            "docs": {},
            "paths": [],
        }
    )
    items = B.build(snap, tmp_path / "s", {})
    new = next(i for i in items if i["name"] == "Demo-recruiting-fairness-agents")
    assert new["industries"][0] == "hr"
    assert (
        "Demo Recruiting" in (tmp_path / "s" / "industries" / "hr.html").read_text()
        or "Recruiting Fairness" in (tmp_path / "s" / "industries" / "hr.html").read_text()
    )


def test_override_wins(tmp_path):
    items = B.build(SNAP, tmp_path / "o", {"Demo-small-lab": {"industries": ["legal"], "framework": "NumPy"}})
    small = next(i for i in items if i["name"] == "Demo-small-lab")
    assert small["industries"] == ["legal"] and small["framework"] == "NumPy"


def test_overrides_file_is_valid():
    for name, ov in B.load_overrides().items():
        assert set(ov) <= {"industries", "framework", "why"} and ov.get("why")
        for d in ov.get("industries", []):
            assert d in B.C.INDUSTRY_LABELS


def test_title_acronyms():
    assert B.title("Jagadish-agent-roi-framework") == "Agent ROI Framework"
    assert B.title("Jagadish-text2sql-data-agent") == "Text2SQL Data Agent"


def test_card_pattern(tmp_path):
    _, site = built(tmp_path)
    h = (site / "index.html").read_text()
    card = h[h.index('<a class="card"') : h.index("</a>", h.index('<a class="card"'))]
    for part in ('class="badge fw-', 'class="lvl lvl-', "<h3>", "<p>", 'class="pills"', 'class="pill"'):
        assert part in card
