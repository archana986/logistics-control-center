/**
 * PostCSS Configuration
 * 
 * Purpose: CSS post-processing pipeline for the frontend build.
 * - tailwindcss: Processes Tailwind utility classes into CSS
 * - autoprefixer: Adds vendor prefixes for browser compatibility
 * 
 * This file is required by Vite to integrate Tailwind CSS.
 */
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}

