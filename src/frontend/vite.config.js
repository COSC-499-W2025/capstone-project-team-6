import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: true,
    hmr: {
      port: 5173,
      host: "localhost",
    },
    watch: {
      usePolling: true,
      interval: 100, 
    },
  },
  build: {
    outDir: "dist",
  },
});
