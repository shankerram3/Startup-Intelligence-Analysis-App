import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // Allow external connections
    port: 5173,
    open: false
  },
  publicDir: 'public',
  // Serve lib folder from root
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  }
});


