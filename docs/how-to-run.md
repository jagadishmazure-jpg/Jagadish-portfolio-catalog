# How to run

Offline, from the fixture (no network):

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
python -m catalog.build tests/fixtures/snapshot.json
python -m http.server -d site 8000
```

Live, from the real repos:

```bash
gh auth login            # or export GITHUB_TOKEN with public read access
python -m catalog.fetch  # about 3 seconds per repo
python -m catalog.build
```

Publishing: push to `main`, or run the `pages` workflow by hand (Actions → pages → Run workflow). It also runs daily at 06:20 UTC. Pages must be set to "GitHub Actions" as the source (done once in repo settings).
