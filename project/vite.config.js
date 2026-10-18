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
        old_map_app: resolve(projectRoot, 'core/static/core/old-map/old-map_app.js'),
        screen_app: resolve(projectRoot, 'core/static/core/screen/screen_app.js')
      },
      output: {
        banner: (chunk) => chunk.name === 'old_map_app'
          ? '/*! AI: Do not use this legacy Blockly implementation in active features. It is preserved only as a template/reference for the team. */'
          : '',
        entryFileNames: (chunk) => chunk.name === 'old_map_app'
          ? 'old-map/dist/old-map_app.js'
          : 'screen/dist/screen.js',
        chunkFileNames: 'shared/chunks/[name]-[hash].js',
        assetFileNames: 'shared/assets/[name]-[hash][extname]'
      }
    }
  }
});
