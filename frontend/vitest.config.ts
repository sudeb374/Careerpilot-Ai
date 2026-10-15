import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./"),
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    include: [
      "components/**/__tests__/**/*.test.{ts,tsx}",
      "components/**/*.test.{ts,tsx}",
      "lib/**/__tests__/**/*.test.{ts,tsx}",
      "tests/**/*.spec.{ts,tsx}",
    ],
  },
});
