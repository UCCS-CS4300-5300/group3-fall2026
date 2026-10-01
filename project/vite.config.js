import {defineConfig} from 'vite';
import {fileURLToPath} from 'node:url';
import {dirname, resolve} from 'node:path';

const projectRoot = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  build: {
    outDir: resolve(projectRoot, 'core/static/core'),
    emptyOutDir: false,
    rollupOptions: {
      input: {
        map_app: resolve(projectRoot, 'core/static/core/map/map_app.js'),
        practice_app: resolve(projectRoot, 'core/static/core/practice/practice_app.js')
      },
      output: {
        entryFileNames: (chunk) => chunk.name === 'map_app'
          ? 'map/dist/map_app.js'
          : 'practice/dist/practice_app.js',
        chunkFileNames: 'shared/chunks/[name]-[hash].js',
        assetFileNames: 'shared/assets/[name]-[hash][extname]'
      }
    }
  }
});
