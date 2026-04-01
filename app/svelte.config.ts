import adapter from '@sveltejs/adapter-static';
import type { Config } from '@sveltejs/kit';

const config: Config = {
	compilerOptions: {
		// Enable Svelte 5 runes mode for the whole project.
		runes: true
	},
	kit: {
		adapter: adapter({
			// SPA fallback required for Capacitor and client-side routing.
			// Every route is served from index.html; the router handles the rest.
			fallback: 'index.html'
		})
	}
};

export default config;
