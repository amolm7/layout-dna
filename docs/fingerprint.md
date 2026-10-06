# Design fingerprint

The fingerprint is a six-dimensional description of relationships that should survive format changes better than literal coordinates.

| Gene | Intended measure | Current deterministic proxy |
| --- | --- | --- |
| Visual mass | Where perceived weight sits | Visible normalized area × opacity × color coverage |
| Hierarchy | Relative prominence of roles | Ratio between the two largest visible areas |
| Reading path | Intended attention sequence | Mean Manhattan distance through declared reading order |
| Alignment | Shared visual axes | Fraction of pairs sharing left, center, or right x-axes within tolerance |
| Negative space | Shape and distribution of emptiness | One minus summed visible area, bounded to `[0,1]` |
| Grouping | Perceptual association | Fraction of visible elements with parent or affinity metadata |

These values are approximations. They are deterministic for regression testing but are not calibrated perceptual metrics and must not be presented as evaluation results.

Scene coordinates are normalized to the source canvas. Original pixel width and height remain available for font, raster, export, and aspect-ratio reasoning. Semantic role, reading order, and affinities may initially come from layer-name rules; later VLM labeling belongs behind the interface in `solver/labeling/vlm.py`.

