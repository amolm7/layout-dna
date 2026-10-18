import { defineConfig } from "vitest/config";

// Component tests opt into jsdom with a `// @vitest-environment jsdom` docblock
// (see tests/*.dom.test.tsx); the pure-logic suites stay on the default node
// environment. The shared setup only touches the DOM when one is present.
export default defineConfig({
  test: {
    setupFiles: ["tests/setup.ts"]
  }
});
