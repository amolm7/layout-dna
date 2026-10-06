# LayoutDNA

LayoutDNA is an Adobe Express add-on prototype that adapts layered designs to new aspect ratios while measuring how well six structural design genes survive the transformation.

## Why it exists

Ordinary resize tools preserve pixels or apply generic reflow rules; they do not describe what made the source composition feel like itself. LayoutDNA represents a page as a versioned scene, measures a deterministic first-pass fingerprint, and asks a solver service for a constrained target layout plus an explanation of the tradeoffs. The current solver is intentionally a lightweight geometric placeholder, not the planned differentiable optimizer.

The fingerprint has six genes:

1. Visual mass distribution
2. Hierarchy ratios
3. Reading path
4. Alignment axes
5. Negative-space topology
6. Gestalt grouping

## Architecture

The React/TypeScript panel runs in Adobe Express's iframe runtime, where browser APIs and solver network calls are available. Document reads and writes run in Adobe's separate document-sandbox runtime. A typed proxy is the only boundary between them. Outside Express, the UI falls back visibly to a fixture-backed mock document adapter.

The FastAPI service validates the shared scene model with Pydantic, computes deterministic proxy scores, and performs a centered contain-scale with safe-margin enforcement. See [the architecture](docs/architecture.md) and [optimization plan](docs/optimization.md).

## Repository map

- `add-on/` — React UI, Adobe manifest v2, document-sandbox adapter, and frontend tests
- `solver/` — FastAPI API, Pydantic contracts, gene modules, placeholder optimizer, and tests
- `schemas/scene.schema.json` — language-neutral scene contract
- `examples/` — valid source-scene fixtures
- `docs/` — architecture, fingerprint, optimization, evaluation, and demo notes
- `study/` — future human-evaluation protocol
- `scripts/` — all-checks and two-process development helpers

## Prerequisites

- Node.js 20+ and npm (Adobe's current docs require Node 18+; this repository targets 20+)
- Python 3.11+
- An Adobe Express account for in-host testing

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

In another terminal, run the panel in standalone mock mode:

```bash
npm run dev:mock --workspace add-on
```

Open `http://127.0.0.1:5241`. The panel clearly reports **Mock mode**, reads its fixture scene, and calls the real local solver. `./scripts/dev.sh` starts both processes together.

## Test in Adobe Express

This repository follows Adobe's current React/TypeScript build-template layout: manifest v2, bundled `index.html`, bundled `code.js`, and a `documentSandbox` panel entry point.

1. Start the solver on port 8000.
2. Run `npm run start --workspace add-on`. On first use, Adobe's CLI may guide you through creating the trusted localhost certificate.
3. Open the CLI-provided `https://www.adobe.com/go/addon-cli` link, or open Adobe Express and enable **Add-on Development** in Settings.
4. In Express, open **Add-ons**, enable add-on testing/development, choose **Test your local add-on**, and connect to `https://localhost:5241`.
5. Open LayoutDNA in a layered document. The mode badge should change from Mock mode to Adobe document.

These steps follow Adobe's [current local development and sideloading guide](https://developer.adobe.com/express/add-ons/docs/guides/getting-started/local-development/dev-tooling). The runtime split follows Adobe's [add-on architecture guide](https://developer.adobe.com/express/add-ons/docs/guides/learn/platform-concepts/architecture), and the manifest follows the [manifest v2 reference](https://developer.adobe.com/express/add-ons/docs/references/manifest/).

The adapter currently extracts public node bounds and creates a new target page using `editor.documentRoot.pages.addPage()`. Source-page cloning is an explicit next integration step; until then, the generated target page reports which source IDs are not yet present instead of modifying the source page.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Solver status and placeholder implementation label |
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
npm run build
./scripts/check.sh
```

## Current limitations

- Gene scores are transparent geometric proxies, not perceptually validated measures.
- Optimization is uniform contain-scaling and margin clamping; it does not use gradients, optimal transport, continuation, or collision resolution yet.
- Adobe extraction uses conservative common node properties and placeholder salience values.
- Creating a target page is supported, but cloning heterogeneous source nodes into it is not implemented yet.
- No database, authentication, hosted VLM, Firefly integration, GPU deployment, or heavy ML runtime is included.

## Roadmap

1. Complete loss implementations and a differentiable renderer behind the unchanged API.
2. Add robust Adobe node cloning, subtype-aware extraction, and non-destructive application tests.
3. Run fixture benchmarks and blinded human evaluation before making quality claims.

MIT licensed. No generated evaluation claims are included.

