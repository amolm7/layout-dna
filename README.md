# LayoutDNA

LayoutDNA adapts layered designs to new aspect ratios while measuring how well six structural
"design genes" survive the transformation. It is a standalone project: a browser web client and
a Python solver service, joined by one versioned scene contract — no host application required.

**Tech stack:** React, TypeScript, Webpack, Python, FastAPI, and Pydantic.

**Engine flow:** source scene → layout analysis and gene fingerprint → deterministic role-aware
reflow for the target canvas → before/after render plus a grounded explanation of the tradeoffs.

## Why it exists

Ordinary resize tools preserve pixels or apply generic reflow rules; they do not describe what
made the source composition feel like itself. LayoutDNA represents a page as a versioned scene,
measures a deterministic first-pass fingerprint, and asks a solver service for a constrained
target layout plus an explanation of the tradeoffs. The current solver is intentionally a
lightweight, deterministic geometric engine, not the planned differentiable optimizer.

The fingerprint has six genes:

1. Visual mass distribution
2. Hierarchy ratios
3. Reading path
4. Alignment axes
5. Negative-space topology
6. Gestalt grouping

## Architecture

A React/TypeScript web client loads example scenes locally, lets you pick a target format, calls
the solver over HTTP, and renders the result entirely in the browser as a before/after SVG —
alongside the gene fingerprint, per-gene drift, and the explanation trace. If the solver is
unreachable it shows a clear offline state rather than inventing a result.

The FastAPI service validates the shared scene model with Pydantic, computes deterministic proxy
gene scores, and performs a role-aware reflow with collision resolution and safe-margin
enforcement. See [the architecture](docs/architecture.md) and [optimization plan](docs/optimization.md).

## Repository map

- `add-on/` — React + TypeScript web client (scene gallery, target picker, SVG before/after, tests)
- `solver/` — FastAPI API, Pydantic contracts, gene modules, deterministic reflow, CLI, and tests
- `schemas/scene.schema.json` — language-neutral scene contract
- `examples/` — valid source-scene fixtures
- `docs/` — architecture, fingerprint, optimization, evaluation, and demo notes
- `study/` — future human-evaluation protocol
- `scripts/` — all-checks and two-process development helpers

## Prerequisites

- Node.js 20+ and npm
- Python 3.11+

## Install

From the repository root:

```bash
npm install
python3 -m venv .venv
.venv/bin/python -m pip install -e './solver[dev]'
cp .env.example .env
```

No secrets are required. PyTorch and GeomLoss are deferred until real differentiable losses exist.

## Run locally

Start the solver:

```bash
.venv/bin/python -m uvicorn app:app --app-dir solver --reload --host 127.0.0.1 --port 8000
```

In another terminal, start the web client:

```bash
npm run dev:add-on
```

Open `http://127.0.0.1:5241`, pick an example scene and a target format, and the client renders
the source and solved layouts side by side against the local solver. `./scripts/dev.sh` starts
both processes together.

## Command line

The solver runs standalone from a terminal, no browser needed, via the `layoutdna` CLI:

```bash
layoutdna fingerprint examples/retail-promo.json          # six gene proxy scores
layoutdna optimize    examples/retail-promo.json --target leaderboard
layoutdna optimize    examples/editorial-poster.json --width 1200 --height 628 --json
```

Named target presets mirror the evaluation matrix (`square`, `story`, `landscape`, `wide`,
`leaderboard`); `--width`/`--height` override them, and `--json` emits the raw API response.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Solver status and implementation label |
| `POST` | `/api/v1/fingerprint` | Six deterministic approximate gene scores |
| `POST` | `/api/v1/optimize` | Margin-safe target boxes, drift metrics, and explanation trace |

Interactive API docs are available at `http://127.0.0.1:8000/docs` while the solver runs.

Example request:

```bash
curl -sS http://127.0.0.1:8000/api/v1/optimize \
  -H 'Content-Type: application/json' \
  --data-binary @<(jq '{scene: ., targetWidth: 1200, targetHeight: 628, margin: 0.04}' examples/editorial-poster.json)
```

## Quality commands

```bash
npm run typecheck
npm run lint
npm test
.venv/bin/ruff check solver
.venv/bin/pytest solver/tests
.venv/bin/python -m evaluation   # solver eval harness over examples × target matrix
npm run build
./scripts/check.sh
```

The evaluation harness reports per-gene drift, hard-constraint violation counts, determinism,
and a runtime envelope across every example scene and a fixed target matrix; it exits non-zero
if a geometrically feasible case violates a hard constraint. See [evaluation](docs/evaluation.md).

## Current limitations

- Gene scores are transparent geometric proxies, not perceptually validated measures.
- Optimization is a deterministic, role-aware geometric reflow with collision resolution and
  margin clamping; it does not use gradients, optimal transport, or a differentiable path yet.
- Salience and some text metrics use fixture metadata rather than rendered measurement.
- No database, authentication, hosted VLM, GPU deployment, or heavy ML runtime is included.

## Roadmap

1. Complete loss implementations and a differentiable renderer behind the unchanged API.
2. Expand the example corpus and subtype-aware scene extraction.
3. Run fixture benchmarks and blinded human evaluation before making quality claims.

MIT licensed. No generated evaluation claims are included.
