import type { FingerprintResponse, OptimizeResponse, Scene } from "../types/scene";

export class SolverClient {
  constructor(private readonly baseUrl = __SOLVER_URL__) {}

  async health(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return response.ok && (await response.json()).status === "ok";
    } catch {
      return false;
    }
  }

  async fingerprint(scene: Scene): Promise<FingerprintResponse> {
    return this.post<FingerprintResponse>("/api/v1/fingerprint", { scene });
  }

  async optimize(
    scene: Scene,
    targetWidth: number,
    targetHeight: number
  ): Promise<OptimizeResponse> {
    return this.post<OptimizeResponse>("/api/v1/optimize", {
      scene,
      targetWidth,
      targetHeight,
      margin: 0.04
    });
  }

  private async post<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    if (!response.ok) {
      throw new Error(`Solver request failed (${response.status})`);
    }
    return (await response.json()) as T;
  }
}
