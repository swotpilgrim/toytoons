import { defineConfig } from 'astro/config';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';

// https://astro.build/config
export default defineConfig({
  integrations: [
    react(),
    tailwind({
      applyBaseStyles: false,
    })
  ],
  output: 'static',
  build: {
    format: 'file'
  },
  site: 'https://toytoons.netlify.app',
  base: '/',
  trailingSlash: 'ignore'
});