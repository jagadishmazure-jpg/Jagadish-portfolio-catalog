# Threat model (STRIDE, short)

| Threat | Where | Control |
|---|---|---|
| Spoofing | Someone else's repo shown as the owner's | Owner fixed in config; only that owner's repos are listed |
| Tampering | README HTML or script injected into the site | Source is the owner's own repos; push protection and review on those repos; no forms or cookies on the site |
| Repudiation | Who changed the site | Every build comes from a commit and a logged workflow run |
| Information disclosure | Private repos or secrets leaking | Public repos only; private ones skipped; read-only token; gitleaks on full history; snapshot not committed |
| Denial of service | API limits | One run a day; about 330 API calls a run, well under the token limit |
| Elevation of privilege | Workflow token misuse | `contents: read`; only the deploy job gets `pages: write` and `id-token: write`; actions pinned to SHAs |
