import type { Color } from "../types/scene";
import { colorToCss, isDarkBackground, type PlacedElement } from "./scenePlacement";

interface ScenePreviewProps {
  /** Canvas dimensions in source units, used for the SVG aspect ratio. */
  canvas: { width: number; height: number; backgroundColor?: Color };
  placed: PlacedElement[];
  /** Short label rendered in the corner of the frame (e.g. "Source", "1200 x 628"). */
  badge?: string;
  className?: string;
}

const TEXT_ROLES = new Set(["headline", "subhead", "body", "cta"]);

function foreground(dark: boolean): string {
  return dark ? "#F3F1EC" : "#15171B";
}

function anchorFor(align: string | undefined) {
  if (align === "center") return "middle" as const;
  if (align === "right") return "end" as const;
  return "start" as const;
}

function ElementShape({ placed, dark }: { placed: PlacedElement; dark: boolean }) {
  const { element, x, y, width, height } = placed;
  const fillVar =
    element.semanticRole === "cta" || element.semanticRole === "decoration"
      ? "var(--ld-accent, #E8613C)"
      : undefined;

  if (TEXT_ROLES.has(element.semanticRole) && element.text) {
    const fontSize = Math.max(1.4, height * 0.66);
    const align = element.text.align ?? "left";
    const anchor = anchorFor(align);
    const tx = align === "center" ? x + width / 2 : align === "right" ? x + width : x;
    const isCta = element.semanticRole === "cta";

    return (
      <g>
        {isCta && (
          <rect
            x={x}
            y={y}
            width={width}
            height={height}
            rx={Math.min(width, height) * 0.22}
            style={{ fill: "var(--ld-accent, #E8613C)" }}
          />
        )}
        <text
          x={isCta ? x + width / 2 : tx}
          y={y + height / 2}
          dominantBaseline="central"
          textAnchor={isCta ? "middle" : anchor}
          fontSize={isCta ? Math.max(1.4, height * 0.4) : fontSize}
          fontWeight={element.text.fontWeight ?? (element.semanticRole === "body" ? 400 : 600)}
          fill={isCta ? "#FFFFFF" : foreground(dark)}
          opacity={element.semanticRole === "body" ? 0.82 : 1}
        >
          {element.text.content}
        </text>
      </g>
    );
  }

  // Non-text roles render as tinted blocks: hero/image placeholders, logos, shapes.
  const neutral = dark ? "rgba(243,241,236,0.14)" : "rgba(21,23,27,0.10)";
  return (
    <rect
      x={x}
      y={y}
      width={width}
      height={height}
      rx={Math.min(width, height) * 0.08}
      style={{ fill: fillVar ?? neutral }}
      opacity={element.semanticRole === "decoration" ? 0.75 : 1}
    />
  );
}

/**
 * Schematic SVG render of a scene (source geometry) or a re-laid-out target
 * (solver boxes mapped back onto their elements). Coordinates are normalized to
 * the canvas, so the same component draws before and after at different aspect
 * ratios without distortion.
 */
export function ScenePreview({ canvas, placed, badge, className }: ScenePreviewProps) {
  const { width: w, height: h, backgroundColor } = canvas;
  const dark = isDarkBackground(backgroundColor);
  const bg = colorToCss(backgroundColor, "var(--ld-surface, #FBFAF7)");

  return (
    <figure className={className ? `ld-preview ${className}` : "ld-preview"}>
      <svg
        viewBox={`0 0 ${w} ${h}`}
        role="img"
        aria-label={badge ? `${badge} layout preview` : "Layout preview"}
        preserveAspectRatio="xMidYMid meet"
      >
        <rect x={0} y={0} width={w} height={h} fill={bg} />
        {placed.map((item) => {
          // Project normalized coordinates into canvas units for this element.
          const p: PlacedElement = {
            element: item.element,
            x: item.x * w,
            y: item.y * h,
            width: item.width * w,
            height: item.height * h
          };
          return <ElementShape key={item.element.id} placed={p} dark={dark} />;
        })}
      </svg>
      {badge && <figcaption>{badge}</figcaption>}
    </figure>
  );
}
