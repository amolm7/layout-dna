import type { DocumentSandboxApi } from "../types/scene";
import { mockDocumentApi } from "./mockScene";

export interface DocumentConnection {
  api: DocumentSandboxApi;
  mode: "adobe" | "mock";
}

export async function connectDocument(): Promise<DocumentConnection> {
  try {
    const module = await import(
      /* webpackIgnore: true */ "https://new.express.adobe.com/static/add-on-sdk/sdk.js"
    );
    const sdk = module.default;
    await sdk.ready;
    const proxy = (await sdk.instance.runtime.apiProxy("documentSandbox")) as DocumentSandboxApi;
    return { api: proxy, mode: "adobe" };
  } catch {
    return { api: mockDocumentApi, mode: "mock" };
  }
}
