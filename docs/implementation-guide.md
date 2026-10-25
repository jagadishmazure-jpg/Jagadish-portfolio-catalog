# Implementation guide (for adopters)

1. Fork or copy the repo and set `CATALOG_OWNER` in the pages workflow env (default is this owner).
2. Change `SKIP` in `catalog/fetch.py` to your own profile and helper repos.
3. Edit the keyword lists in `catalog/classify.py` for your domains and skills, and `DOMAINS` in `catalog/build.py`.
4. Replace the delivery text in `catalog/build.py` (`DELIVERY`) with your own method.
5. Settings → Pages → Source: GitHub Actions. Push to `main`.
6. Keep the disclaimer if your work is also synthetic.
