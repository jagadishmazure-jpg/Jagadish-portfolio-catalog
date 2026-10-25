# Interview points

- Why a generator and not a hand-written site: the numbers stay true because they are copied from the repos on every run, and new repos need no edit.
- Why plain HTML: no framework to update, no build tool, fast on any device, nothing to break on a free host.
- Single source for test counts: the profile README is reconciled against real runs, so it wins over README text; the total on the site (11,936 at first build) matches it.
- Tagging trade-off: keyword rules are explainable and testable; misses are fixed by overrides that must carry a reason.
- Honesty by construction: tests fail the build if a page lacks the disclaimer or a results list lacks the synthetic-data label.
