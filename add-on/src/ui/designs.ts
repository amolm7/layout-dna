import type { Scene } from "../types/scene";
import { mockScene } from "./mockScene";
import editorialPoster from "../../../examples/editorial-poster.json";
import eventFlyer from "../../../examples/event-flyer.json";
import retailPromo from "../../../examples/retail-promo.json";

export interface Design {
  id: string;
  name: string;
  /** One-line description of the source composition. */
  note: string;
  scene: Scene;
}

/**
 * Curated source designs the demo can re-lay-out. These are the same scene
 * fixtures the solver is evaluated against, so the demo and the test corpus
 * stay honest about what the engine actually handles. Fixtures that exist only
 * to exercise solver edge cases (degenerate group nesting) are intentionally
 * left out of the gallery.
 */
export const DESIGNS: Design[] = [
  {
    id: "editorial-poster",
    name: "Editorial poster",
    note: "Hero image with a stacked headline, body, and corner logo.",
    scene: editorialPoster as unknown as Scene
  },
  {
    id: "retail-promo",
    name: "Retail promo",
    note: "Dark promo tile: full-bleed hero, bold offer, pill CTA.",
    scene: retailPromo as unknown as Scene
  },
  {
    id: "event-flyer",
    name: "Event flyer",
    note: "Condensed type lockup with a decorative accent and detail line.",
    scene: eventFlyer as unknown as Scene
  },
  {
    id: "city-in-motion",
    name: "City in motion",
    note: "Reference fixture: hero, headline, and logo in reading order.",
    scene: mockScene
  }
];

export function findDesign(id: string): Design {
  return DESIGNS.find((design) => design.id === id) ?? DESIGNS[0]!;
}
