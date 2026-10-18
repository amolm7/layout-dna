import { afterEach, describe, expect, it, vi } from "vitest";

import type { Scene } from "../src/types/scene";
import { SolverClient } from "../src/api/solverClient";

const scene: Scene = {
  schemaVersion: "1.0.0",
  canvas: { width: 1000, height: 1000 },
  elements: []
};

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

  it("treats a reachable-but-not-ok status as unhealthy", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: "degraded" }) })
    );
    await expect(new SolverClient("http://solver").health()).resolves.toBe(false);
  });

  it("posts the scene to the fingerprint endpoint and returns the body", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({ approximation: true }) });
    vi.stubGlobal("fetch", fetchMock);

    const body = await new SolverClient("http://solver").fingerprint(scene);

    expect(body).toEqual({ approximation: true });
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://solver/api/v1/fingerprint");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ scene });
  });

  it("sends target dimensions and the fixed margin to the optimize endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ boxes: [] }) });
    vi.stubGlobal("fetch", fetchMock);

    await new SolverClient("http://solver").optimize(scene, 1200, 628);

    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("http://solver/api/v1/optimize");
    expect(JSON.parse(init.body)).toEqual({
      scene,
      targetWidth: 1200,
      targetHeight: 628,
      margin: 0.04
    });
  });

  it("throws with the status code when a request is not ok", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 500 }));
    await expect(new SolverClient("http://solver").fingerprint(scene)).rejects.toThrow(
      "Solver request failed (500)"
    );
  });
});
