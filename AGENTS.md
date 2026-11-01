# designs

Visual designs for t-shirts and posters. Personal repo (witchel/designs).

## Architecture as-is

- One directory per design, each with `README.md`, an SVG source, and a
  print-ready PNG rendered from that SVG.
- The top-level `README.md` holds the gallery table; add a row for every new
  design.
- `collatz/` is a hand-finished SVG. `gaussian-primes/` is computed: its own uv
  project (`generate.py`, `gprimes.py`, `svg.py`), with SVG, PNG, and
  `previews/*.jpg` all written by `uv run generate.py` (needs Inkscape and
  ImageMagick).

## Landmines / gotchas

- Source of truth: the SVG for hand-made designs, the generator for computed
  ones. Never hand-edit a generated SVG; change the code and regenerate so the
  SVG, PNG, and preview never drift.
- Keep printed strokes at or above ~0.012" at final print size for shirts (see
  `collatz/README.md`, Print safety). Poster hairlines are for giclée/offset only.
- The Gaussian poster PNGs are 15-30 MB. Every regeneration adds that much to
  git history, so commit them only when the design actually changes. GitHub
  rejects files over 100 MB.
- `gaussian-primes/.cache/` holds pickled trees. Delete it after changing the
  tree construction in `gprimes.py`, or stale trees are reused.
