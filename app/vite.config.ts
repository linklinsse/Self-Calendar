import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	build: {
    	outDir: 'dist' // if this says something else, e.g. 'build', use that instead
  	},
	plugins: [sveltekit()]
});
