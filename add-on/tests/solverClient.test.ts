import { afterEach, describe, expect, it, vi } from "vitest";

import { SolverClient } from "../src/api/solverClient";

describe("SolverClient", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("reports a healthy solver", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "ok" }) })
    );
    await expect(new SolverClient("http://solver").health()).resolves.toBe(true);
  });

  it("reports offline when fetch fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    await expect(new SolverClient("http://solver").health()).resolves.toBe(false);
  });
});
