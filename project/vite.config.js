import {defineConfig} from 'vite';
import {fileURLToPath} from 'node:url';
import {dirname, resolve} from 'node:path';

const projectRoot = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  build: {
    outDir: resolve(projectRoot, 'core/static/core/maze/dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(projectRoot, 'core/static/core/maze/maze_app.js'),
      output: {
        entryFileNames: 'maze_app.js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]'
      }
    }
  }
});
