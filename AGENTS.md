# designs

Visual designs for t-shirts and posters. Personal repo (witchel/designs).

## Architecture as-is

- One directory per design, each with `README.md`, an SVG source, and a
  print-ready PNG rendered from that SVG.
- The top-level `README.md` holds the gallery table; add a row for every new
  design.

## Landmines / gotchas

- The SVG is the source of truth. Regenerate the PNG after editing the SVG so
  the two never drift.
- Keep printed strokes at or above ~0.012" at final print size (see
  `collatz/README.md`, Print safety).
