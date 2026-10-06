import addOnSandboxSdk from "add-on-sdk-document-sandbox";
import { editor } from "express-document-sdk";

import type { DocumentSandboxApi } from "../types/scene";
import { applyLayout, createOrSelectTargetPage } from "./applyLayout";
import { extractScene } from "./extractScene";

const { runtime } = addOnSandboxSdk.instance;

const sandboxApi: DocumentSandboxApi = {
  extractScene: () => extractScene(editor as any),
  createOrSelectTargetPage: (width, height) =>
    createOrSelectTargetPage(editor as any, width, height),
  applyLayout: (boxes, targetWidth, targetHeight) =>
    applyLayout(editor as any, boxes, targetWidth, targetHeight)
};

runtime.exposeApi(sandboxApi);
