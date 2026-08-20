import adapter from '@sveltejs/adapter-static';
import type { Config } from '@sveltejs/kit';

const config: Config = {
	compilerOptions: {
		// Enable Svelte 5 runes mode for the whole project.
		runes: true
	},
	kit: {
		adapter: adapter({
			fallback: 'app.html'
		})
	}
};

export default config;
