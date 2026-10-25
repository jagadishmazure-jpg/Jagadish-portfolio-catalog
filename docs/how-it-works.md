# How it works

## Data flow

1. **Fetch** (`catalog/fetch.py`). Lists public repos of the owner through the read-only API, skips forks, archived repos, the profile, the coordination repo and this repo, and stores per repo: description, topics, default branch, README, `docs/architecture.md`, `docs/how-it-works.md`, `docs/how-to-run.md` when present, and every file path. The profile README is stored too, because its test counts are reconciled against real runs.
2. **Classify** (`catalog/classify.py`).
   - *Industries*: keyword lists per domain, matched at word starts (short words need a full-word match, so "soc" never matches "social"). Name, description and topics are checked first; the README's first paragraph is used only when those say nothing. Industries found in the repo name come first, so the main industry follows the name. No match → Cross-industry.
   - *Skills*: keyword hit counts over name, description, topics and the first 4,000 README characters; top four kept.
   - *Framework badge* and *level*: rules in the README table.
   - *Tests*: profile README first (featured paragraph plus the learning-repo table), then the repo README, else "not stated".
3. **Overrides** (`data/overrides.json`). Manual fixes, each with a `why`. A test rejects entries without one.
4. **Extract** (`catalog/extract.py`). Splits markdown by headings (ignoring `#` inside code fences) and picks the first section whose heading matches each key. Result lines need a digit and a metric word (recall, AUC, %, p50, blocked, "from x to y"...). The evidence board is the shortest image path containing "evidence", else "board".
5. **Build** (`catalog/build.py`). Writes `site/` from scratch: home, `repos/`, `case-studies/`, `industries/`, `capabilities.html`, `delivery.html`, `about.html`, `catalog.json`. Relative links and images in README text are rewritten to the repo on GitHub. Mermaid blocks are drawn in the browser.

## Pages

| Page | Content |
|---|---|
| Home | Search box, framework / industry / skill chips, one card per repo |
| Project page | Purpose, architecture, how it works, how to run, built vs planned, evidence board, measured results, repo link |
| Case study | Problem, approach, measured results, guardrails and governance, limitations |
| Industry page | Problems worked on, one measured result per repo, the repo cards; an empty domain says so |
| Capabilities | Industry × skill counts |
| How we deliver | Discovery, pilot, production hardening, security and compliance, evaluation and monitoring, accelerators |

## Current overrides

| Repo | Fix | Why |
|---|---|---|
| media-ops-agents | Cross-industry | Its description lists the domains it follows |
| llm-capacity-planning | Cross-industry | Planning study, no industry |
| inference-optimization | Cross-industry | "energy" there means compute cost |
| telecom-incident-agents | Cross-industry | Telecom is not one of the ten domains |

## Agent cards (`catalog/agents.json`)

Any repo can publish single-agent cards in a file named `catalog/agents.json` with `"schema": "agent-card/v1"` and an `agents` list. `catalog/agents.py` turns each entry into a card:

| Card field | From |
|---|---|
| Title, description | `title`, `summary` (both required, with `name`) |
| Badge | `tech`: LangGraph/LangChain, Playwright, Azure or Agent Framework when named, otherwise Python |
| Level | `level` if it is Beginner, Intermediate or Advanced, otherwise Beginner |
| Industry | `industry` mapped to one of the ten domains by keyword (for example "Financial services" → banking, "Travel" → logistics), else Cross-industry |
| Tags | the card's own industry text, the badge, the first two `tags` |
| Result line | `task_score` on `task_cases`, labelled synthetic |
| Link | `page`, only if it points inside the publishing repo; otherwise the repo itself |

A file that is missing, not JSON or on another schema is ignored, and so is any entry without the required fields. Cards appear on the home page under **Enterprise use-case agents**, on `agents.html` (with a level filter) and on the matching industry pages.
