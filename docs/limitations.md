# Limitations

- **Keyword tagging is approximate.** A repo that mentions banking once in its description gets a banking tag. Overrides fix the worst cases; the matrix counts tags, not depth of work.
- **Results are picked by pattern.** Any line with a number and a metric word qualifies, so a line can be a target or a caveat rather than a result. The repo is the source of truth.
- **Extraction depends on headings.** A README without the usual headings gives a thin page.
- **Case studies reuse README text.** They are not separately written summaries.
- **No browser tests yet** for the filter script; it was checked by hand in a headless browser.
- **Daily refresh.** A repo pushed today shows up at the next run unless the workflow is started by hand.
- **README HTML is passed through.** Safe only because the source is the owner's own repos (see the threat model).
