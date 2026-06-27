import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev, proxy the API + SSE stream to the FastAPI backend on :8765.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8765",
        changeOrigin: true,
      },
    },
  },
  build: {
    // Build straight into the Python package so the wheel ships the dashboard
    // and `pip install "looplens[server]"` needs no Node/npm at runtime.
    outDir: "../looplens/server/_ui",
    emptyOutDir: true,
  },
});
