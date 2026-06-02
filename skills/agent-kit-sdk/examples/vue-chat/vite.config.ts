import vue from "@vitejs/plugin-vue"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5930,
    proxy: {
      "/api": { target: "http://127.0.0.1:8020" },
      "/socket.io": { target: "http://127.0.0.1:8020", ws: true },
    },
  },
})
