import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
  },
  build: {
    outDir: "dist",
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/tests/setup.js"],
    globals: true,
    include: ['src/**/*.{test,spec}.{js,jsx,ts,tsx}'],
  },
});
