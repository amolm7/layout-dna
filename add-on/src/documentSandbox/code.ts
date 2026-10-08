import addOnSandboxSdk from "add-on-sdk-document-sandbox";
import { editor } from "express-document-sdk";

import type { DocumentSandboxApi } from "../types/scene";
import { applyLayout, createOrSelectTargetPage } from "./applyLayout";
import { makeCloneInto } from "./cloningAdapter";
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
      // Real reconstruct-via-factories cloning (the Document Sandbox has no node clone API, verified
      // Oct 2026): builds NodeFactories from the live editor and delegates to cloneNode. This path is
      // IMPLEMENTED-BUT-UNVERIFIED against live Adobe Express — only exercised with fakes in tests.
      // applyLayout already degrades any throwing live geometry write to missing[].
      cloneInto: makeCloneInto(editor as any, sandboxSession.targetPage as any)
    };
    return applyLayout(cloningEditor as any, boxes, targetWidth, targetHeight);
  }
};

runtime.exposeApi(sandboxApi);
