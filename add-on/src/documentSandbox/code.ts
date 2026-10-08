import addOnSandboxSdk from "add-on-sdk-document-sandbox";
import { editor } from "express-document-sdk";

import type { DocumentSandboxApi } from "../types/scene";
import { applyLayout, createOrSelectTargetPage } from "./applyLayout";
import { extractScene } from "./extractScene";

const { runtime } = addOnSandboxSdk.instance;

// The Document Sandbox runtime persists between proxy calls, so we remember the page that was
// current when the target was created (the source) and the newly created target page. This hands
// both to `applyLayout` without widening the UI<->sandbox proxy contract (DocumentSandboxApi).
let sandboxSession: { sourcePage: unknown; targetPage: unknown } | null = null;

const sandboxApi: DocumentSandboxApi = {
  extractScene: () => extractScene(editor as any),
  createOrSelectTargetPage: (width, height) => {
    const sourcePage = (editor as any).context.currentPage;
    const result = createOrSelectTargetPage(editor as any, width, height);
    // addPage activates the new page, so currentPage is now the target.
    const targetPage = (editor as any).context.currentPage;
    sandboxSession = { sourcePage, targetPage };
    return result;
  },
  applyLayout: (boxes, targetWidth, targetHeight) => {
    if (!sandboxSession) {
      // No target prepared (createOrSelectTargetPage was not called first); nothing can be placed.
      return { applied: [], missing: boxes.map((box) => box.id) };
    }
    const cloningEditor = {
      sourcePage: sandboxSession.sourcePage,
      targetPage: sandboxSession.targetPage,
      // PLACEHOLDER adapter: the Adobe Express Document Sandbox exposes no node clone/duplicate
      // API (verified Oct 2026), so cloning is not yet implemented on the real path. Until the
      // reconstruct-via-factories adapter lands, every id is reported in missing[] rather than
      // silently dropped or faked (AGENTS.md: label placeholders, never fabricate behavior).
      cloneInto: () => null
    };
    return applyLayout(cloningEditor as any, boxes, targetWidth, targetHeight);
  }
};

runtime.exposeApi(sandboxApi);
