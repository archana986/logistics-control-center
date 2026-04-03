/**
 * Vite Configuration
 * 
 * Purpose: Build tool configuration for the React frontend.
 * - Uses @vitejs/plugin-react for React Fast Refresh and JSX transform
 * - Configures path alias "@" -> "./src" for cleaner imports
 * - Handles development server and production builds
 * 
 * Commands:
 *   npm run dev   - Start development server (http://localhost:5173)
 *   npm run build - Build for production (outputs to dist/)
 */
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
})
