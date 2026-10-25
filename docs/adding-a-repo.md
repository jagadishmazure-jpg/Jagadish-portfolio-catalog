# Adding a repo

Nothing to edit in this repo. A new public repo appears on the next `pages` run (daily, or run it by hand).

To make it look right:

1. Put a clear one-line description on the repo; it becomes the card text and the case-study problem.
2. Use headings the extractor knows: `Recruiter summary` or `Purpose`, `Architecture`, `How it works`, `How to run`, `Built vs planned`, `Results`, `Guardrails`, `Limitations`.
3. State the test count as `N tests` in the README, and add the repo to the profile README table (that count wins).
4. Name the evidence image with `evidence` in the path, for example `docs/evidence_board.png`.
5. Put the industry word in the repo name (for example `recruiting` → HR & recruiting).
6. If a tag is still wrong, add an entry with a `why` to `data/overrides.json`.
7. To show single agents as their own cards, publish `catalog/agents.json` in the agent-card/v1 format (see [how-it-works.md](how-it-works.md#agent-cards-catalogagentsjson)).
