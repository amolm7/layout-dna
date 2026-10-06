"""Pydantic contracts for the versioned LayoutDNA scene and API."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "1.0.0"
GeneName = Literal[
    "visualMass",
    "hierarchy",
    "readingPath",
    "alignment",
    "negativeSpace",
    "grouping",
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Color(StrictModel):
    r: float = Field(ge=0, le=1)
    g: float = Field(ge=0, le=1)
    b: float = Field(ge=0, le=1)
    a: float = Field(ge=0, le=1)


class Canvas(StrictModel):
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    backgroundColor: Color | None = None


class TextProperties(StrictModel):
    content: str
    fontSize: float | None = Field(default=None, gt=0)
    fontWeight: float | None = Field(default=None, ge=1)
    lineHeight: float | None = Field(default=None, gt=0)
    align: Literal["left", "center", "right", "justify"] | None = None


class VisualProperties(StrictModel):
    opacity: float = Field(ge=0, le=1)
    luminance: float = Field(ge=0, le=1)
    colorCoverage: float = Field(ge=0, le=1)
    fill: Color | None = None


class ElementConstraints(StrictModel):
    minWidth: float | None = Field(default=None, ge=0)
    minHeight: float | None = Field(default=None, ge=0)
    fixedAspectRatio: bool = False
    lockedPosition: bool = False
    logoClearSpace: float = Field(default=0, ge=0)
    mandatoryOnCanvas: bool = False


class SceneElement(StrictModel):
    id: str = Field(min_length=1)
    type: Literal["text", "image", "shape", "group", "unknown"]
    semanticRole: Literal[
        "headline",
        "subhead",
        "body",
        "cta",
        "logo",
        "hero",
        "decoration",
        "background",
        "unknown",
    ]
    parentId: str | None = None
    x: float
    y: float
    width: float = Field(ge=0)
    height: float = Field(ge=0)
    rotation: float
    zIndex: int
    visible: bool
    optional: bool
    text: TextProperties | None = None
    visual: VisualProperties
    constraints: ElementConstraints = Field(default_factory=ElementConstraints)
    readingOrder: int | None = Field(default=None, ge=0)
    groupAffinities: list[str] = Field(default_factory=list)


class Scene(StrictModel):
    schemaVersion: Literal["1.0.0"]
    canvas: Canvas
    elements: list[SceneElement]

    @model_validator(mode="after")
    def unique_ids_and_valid_parents(self) -> "Scene":
        ids = [element.id for element in self.elements]
        if len(ids) != len(set(ids)):
            raise ValueError("element ids must be unique")
        known = set(ids)
        for element in self.elements:
            if element.parentId is not None and element.parentId not in known:
                raise ValueError(f"unknown parentId {element.parentId!r}")
        return self


class FingerprintRequest(StrictModel):
    scene: Scene


class FingerprintResponse(StrictModel):
    schemaVersion: Literal["1.0.0"] = SCHEMA_VERSION
    approximation: Literal[True] = True
    scores: dict[GeneName, float]
    notes: list[str]


class OptimizeRequest(StrictModel):
    scene: Scene
    targetWidth: float = Field(gt=0)
    targetHeight: float = Field(gt=0)
    margin: float = Field(default=0.04, ge=0, lt=0.5)


class ElementBox(StrictModel):
    id: str
    x: float
    y: float
    width: float = Field(ge=0)
    height: float = Field(ge=0)
    rotation: float


class ExplanationStep(StrictModel):
    code: str
    message: str
    metrics: dict[str, float | str | bool]


class OptimizeResponse(StrictModel):
    schemaVersion: Literal["1.0.0"] = SCHEMA_VERSION
    solverKind: Literal["deterministic-placeholder"] = "deterministic-placeholder"
    target: Canvas
    boxes: list[ElementBox]
    geneDrift: dict[GeneName, float]
    explanation: list[ExplanationStep]
