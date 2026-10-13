# Demo script

A five-minute walkthrough of the standalone demo. No host application required — just the
solver service and the web client (see the README for exact start commands).

1. Start the solver and the web client. Open the client; it connects to the local solver.
2. Pick an example scene from the gallery. Show the six proxy gene values and the detected
   semantic roles in the fingerprint panel.
3. Choose a target format (e.g. **Story**, 1080×1920). The before/after SVG renders the source
   layout and the solved re-layout side by side.
4. Switch to **Leaderboard** (728×90) to expose a severe aspect-ratio change: point out the
   larger negative-space and reading-path drift, and the explanation trace noting any relaxed
   constraints. The solver surfaces the limit honestly rather than hiding it.
5. Walk through the explanation trace: every step (reflow, constraints, optional-removed,
   collisions-resolved, text-overflow, gene-drift) is grounded in a recorded solver metric.
6. Drop to the terminal and run the same scene through the CLI — `layoutdna optimize
   examples/<scene>.json --target leaderboard` — and the evaluation harness (`python -m
   evaluation`), showing the engine stands alone without the browser.
7. State the limitation clearly: the output is a deterministic role-aware reflow. A
   differentiable (gradient / optimal-transport) optimizer is future work, and drift is a
   geometric proxy, not a perceptual quality score.
