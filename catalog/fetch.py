"""Fetch a snapshot of every public portfolio repo into data/snapshot.json.

Backends: GITHUB_TOKEN env (used in CI) or the `gh` CLI (local).
Only public metadata, READMEs, selected docs and file paths are read.
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

OWNER = os.environ.get("CATALOG_OWNER", "jagadishmazure-jpg")
SKIP = {OWNER, "Jagadish-portfolio-coordination", "Jagadish-portfolio-catalog"}
AGENTS_FILE = "catalog/agents.json"
DOC_NAMES = ("docs/architecture.md", "docs/how-it-works.md", "docs/how-to-run.md")


def _api(path: str):
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req = urllib.request.Request(
            "https://api.github.com/" + path.lstrip("/"),
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise
    out = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return json.loads(out.stdout)


def _file(repo: str, path: str) -> str | None:
    data = _api(f"repos/{OWNER}/{repo}/contents/{path}")
    if not data or "content" not in data:
        return None
    return base64.b64decode(data["content"]).decode("utf-8", "replace")


def fetch() -> dict:
    repos, page = [], 1
    while True:
        batch = _api(f"users/{OWNER}/repos?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos += batch
        page += 1
    out = []
    for r in sorted(repos, key=lambda x: x["name"].lower()):
        if r["private"] or r["fork"] or r["archived"] or r["name"] in SKIP:
            continue
        name, branch = r["name"], r["default_branch"]
        tree = _api(f"repos/{OWNER}/{name}/git/trees/{branch}?recursive=1") or {}
        paths = [t["path"] for t in tree.get("tree", []) if t["type"] == "blob"]
        docs = {p: _file(name, p) for p in DOC_NAMES if p in paths}
        out.append(
            {
                "name": name,
                "description": r.get("description") or "",
                "topics": r.get("topics") or [],
                "url": r["html_url"],
                "branch": branch,
                "pushed_at": r.get("pushed_at"),
                "readme": _file(name, "README.md") or "",
                "docs": {k: v for k, v in docs.items() if v},
                "paths": paths,
                "agents_json": _file(name, AGENTS_FILE) if AGENTS_FILE in paths else None,
            }
        )
        print(f"fetched {name}", file=sys.stderr)
    profile = _file(OWNER, "README.md") or ""
    return {"owner": OWNER, "repos": out, "profile_readme": profile}


if __name__ == "__main__":
    snap = fetch()
    Path("data").mkdir(exist_ok=True)
    Path("data/snapshot.json").write_text(json.dumps(snap, indent=1))
    print(f"{len(snap['repos'])} repos")
