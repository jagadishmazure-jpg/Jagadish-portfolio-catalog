import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_actions_pinned_to_full_sha():
    for wf in (ROOT / ".github" / "workflows").glob("*.yml"):
        for ref in re.findall(r"uses:\s*([^\s#]+)", wf.read_text()):
            assert re.search(r"@[0-9a-f]{40}$", ref), f"{wf.name}: {ref}"


def test_pages_workflow_is_free_and_read_only():
    wf = (ROOT / ".github" / "workflows" / "pages.yml").read_text()
    assert "permissions:\n  contents: read" in wf
    assert "runs-on: ubuntu-latest" in wf and "self-hosted" not in wf


def test_required_docs_exist():
    for f in [
        "README.md",
        "LICENSE",
        "SECURITY.md",
        "docs/how-it-works.md",
        "docs/how-to-run.md",
        "docs/adding-a-repo.md",
        "docs/limitations.md",
        "docs/threat-model.md",
        "docs/interview-points.md",
        "docs/implementation-guide.md",
    ]:
        assert (ROOT / f).exists(), f
    assert "Built vs planned" in (ROOT / "README.md").read_text()
