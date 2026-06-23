import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'

export default defineConfig({
  plugins: [tailwindcss(), react()],
  base: './',
  resolve: { alias: { '@': resolve(__dirname, 'src') } },
  clearScreen: false,
  server: { port: 5173, strictPort: true },
})
