# Collatz Conjecture T-Shirt Design

A visualization of four Collatz sequences, each showing a different
behavioral "personality" of the conjecture. The design uses smooth
envelope curves (connecting local maxima of the raw zigzag sequence)
with labeled number circles tangent to their curves, on a dark
background suitable for printing on a black shirt.

## The Collatz Conjecture

Start with any positive integer n. If even, divide by 2. If odd,
multiply by 3 and add 1. The conjecture states that every starting
number eventually reaches 1. Despite its simplicity, this remains
one of the most famous unsolved problems in mathematics.

## The Four Sequences

Each sequence was chosen for a distinct visual shape. Rather than
showing the full path to 1, each curve shows only the most
interesting portion — the dramatic rise, peak, and the beginning
of the descent. Curves are smoothed through the envelope (local
maxima only), removing the raw odd/even zigzag to reveal the
underlying shape.

### 127 (purple, #b44aff) — Pure staircase

Full sequence: 46 steps to reach 1, peak 4,372 at step 13.
Window shown: steps 0–17 (18 values). The envelope is a pure
exponential climb — each 3n+1 step pushes higher than the last,
with no dips or hesitation. The curve shows the full ascent from
127 through 862, 1,942 to the peak at 4,372, then the beginning
of the descent with a bounce to 3,280 (where 1,093 hits 3n+1).

Envelope: 127 → 382 → 574 → 862 → 1,294 → 1,942 → 2,914
→ 4,372 → 3,280

### 27 (hot pink, #ff2d78) — Symmetric mountain

Full sequence: 111 steps to reach 1, peak 9,232 at step 77.
Window shown: steps 70–85 (16 values). The number 27 is the
most famous "surprisingly long" Collatz sequence — such a small
starting value shouldn't need 111 steps, yet it climbs all the
way to 9,232. The window captures the climb to the peak and the
symmetric descent on the other side, passing through 4,102 on the
way up and 577 on the way down.

Envelope: 911 → 2,734 → 4,102 → 6,154 → 9,232 → 1,732 → 1,300

### 871 (deep orange, #e85500) — V-dip then explosion

Full sequence: 178 steps to reach 1, peak 190,996 at step 31.
Window shown: steps 15–34 (20 values). The envelope climbs from
7,451 through 22,354 to 33,532, then dips unexpectedly to 25,150
(where a cascade of halvings drops the value) before resuming a
steeper climb through 84,886 to the peak at 190,996. The dip in
the middle is the signature feature — a false valley that makes
the eventual explosion to nearly 200,000 more dramatic.

Envelope: 7,451 → 22,354 → 33,532 → 25,150 → 37,726 → 56,590
→ 84,886 → 127,330 → 190,996 → 143,248

### 927 (emerald green, #00b358) — Double peak

Full sequence: 116 steps to reach 1, peak 15,856 at step 14.
Window shown: steps 4–15 (12 values). The curve climbs to a
sub-peak at 14,092, drops into a valley at 3,523, then surges
past the false summit to the true peak at 15,856. This
double-peak pattern — where the sequence appears to have peaked
but hasn't — is one of the characteristic surprises of the
Collatz conjecture.

Envelope: 2,087 → 6,262 → 9,394 → 14,092 → 10,570 → 15,856

## Design Process

The design was generated through an iterative process:

1. **Sequence search**: Computed Collatz sequences for starting
   numbers 3–2000, classified envelope shapes by peak position,
   dip count, and overall profile. Selected four with maximally
   diverse silhouettes using a greedy shape-distance algorithm.

2. **Windowing**: Each sequence was truncated to its most
   interesting portion. The full path to 1 is not shown — the
   boring tail of halving down through small numbers is omitted.
   Similarly, the starting number's initial value is only shown
   when it falls within the window.

3. **Envelope smoothing**: Raw Collatz sequences zigzag because
   every 3n+1 step is followed by one or more n/2 steps. The
   curves show only the local maxima, connected by Catmull-Rom
   splines (rendered as SVG cubic Bézier paths), revealing the
   underlying shape.

4. **Label placement**: Number circles are tangent to their
   curves, positioned on the convex side (above peaks, below
   valleys, to the side on descents). Tangent offsets computed as:
   `center = curve_point ± (radius + line_stroke/2 + circle_stroke/2)`

5. **Print safety**: Line widths and circle strokes were checked
   against screen printing and DTG minimum thickness guidelines
   (~0.012" minimum for printed lines). At 4000px render width
   for a ~12" print area, the thinnest element (2.0 SVG units
   circle stroke) renders at ~0.032", safely above minimums.

## Files

- `collatz-shirt.svg` — vector source (editable)
- `collatz-shirt.png` — high-resolution raster (4000px wide)

## Color Palette

| Sequence | Color | Hex | Text |
|----------|-------|-----|------|
| 127 | Bright purple | #b44aff | White |
| 27 | Hot pink | #ff2d78 | White |
| 871 | Deep orange | #e85500 | White |
| 927 | Emerald green | #00b358 | White |
| Background | Near-black | #08080f | — |
