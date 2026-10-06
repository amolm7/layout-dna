# Optimization plan

The planned objective is:

\[
L = w_m L_{mass} + w_h L_{hierarchy} + w_r L_{reading} + w_a L_{alignment} + w_n L_{negative-space} + w_g L_{grouping} + L_{constraints}
\]

Each soft loss compares a target rendering or geometry graph with the source fingerprint. `Lconstraints` records penalties during early continuation stages, but feasibility-critical rules should become projections or hard constraints in the final stage.

Future hard constraints include:

- margins and safe areas;
- no overlap for incompatible element pairs;
- minimum readable font size;
- logo clear space;
- crop safety for protected image regions; and
- mandatory on-canvas elements.

The intended solver progresses through nearby aspect ratios before the final target (continuation), uses differentiable rendering for image-space losses, and uses optimal transport for spatial mass comparison. A sacrifice policy may relax weighted soft genes when no fully faithful solution exists. Every relaxation must be recorded with measured before/after drift; it may never silently hide a mandatory element.

The current implementation is deliberately smaller: it uniformly contain-scales the source composition into a safe target rectangle, clamps boxes to margins and logo clear space, and returns deterministic proxy drift. `renderer.py` and `sacrifice.py` mark stable seams for later implementation. PyTorch and GeomLoss are not default dependencies yet.

