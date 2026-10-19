# post.cold.fyi

Public site for Post, the Third Polar Arch mail archive. GitHub Pages, served from `main` at the repo root.

- `cards/<ID>/card.json` + `front.webp` (+ `back.webp` only for blank unused cards) - one folder per published piece
- `build.py` - regenerates every HTML page from `cards/`. No dependencies.
- Nothing here is edited by hand. Cards arrive through the private `richerd22/post-inbox` repo, which holds raw scans, the queue and the agent map (`AGENTS.md`).

Takedown: delete `cards/<ID>/`, run `python3 build.py`, commit.
