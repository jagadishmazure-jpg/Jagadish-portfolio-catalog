import base64
import json

from catalog import fetch as F


def fake_api(path):
    if path.startswith("users/"):
        return (
            []
            if "page=2" in path
            else [
                {
                    "name": "R-one",
                    "private": False,
                    "fork": False,
                    "archived": False,
                    "default_branch": "main",
                    "html_url": "https://github.com/o/R-one",
                    "description": "d",
                    "topics": [],
                },
                {
                    "name": "R-private",
                    "private": True,
                    "fork": False,
                    "archived": False,
                    "default_branch": "main",
                    "html_url": "u",
                    "description": "",
                    "topics": [],
                },
            ]
        )
    if "/git/trees/" in path:
        return {"tree": [{"path": "README.md", "type": "blob"}, {"path": "catalog/agents.json", "type": "blob"}]}
    if path.endswith("/contents/catalog/agents.json"):
        return {"content": base64.b64encode(json.dumps({"schema": "agent-card/v1", "agents": []}).encode()).decode()}
    if "/contents/" in path:
        return {"content": base64.b64encode(b"# readme").decode()}
    return None


def test_fetch_reads_agents_json_and_skips_private(monkeypatch):
    monkeypatch.setattr(F, "_api", fake_api)
    snap = F.fetch()
    assert [r["name"] for r in snap["repos"]] == ["R-one"]
    r = snap["repos"][0]
    assert r["readme"] == "# readme" and json.loads(r["agents_json"])["schema"] == "agent-card/v1"
