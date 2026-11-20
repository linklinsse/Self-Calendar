import adapter from '@sveltejs/adapter-static';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	build: {
		outDir: 'dist' // if this says something else, e.g. 'build', use that instead
	},
	plugins: [
		// SvelteKit 3 no longer reads svelte.config.{js,ts}: its configuration
		// (and vite-plugin-svelte's) is passed to the plugin directly.
		sveltekit({
			// Every page must be pre-renderable (or served from the SPA
			// fallback) — see src/routes/+layout.ts.
			adapter: adapter({
				fallback: 'app.html'
			}),
			compilerOptions: {
				// Enable Svelte 5 runes mode for the whole project.
				runes: true
			}
		})
	]
});
