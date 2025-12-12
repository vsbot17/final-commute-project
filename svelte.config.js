import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),

	kit: {
		adapter: adapter({
			// Output to docs folder for GitHub Pages
			pages: 'docs',
			assets: 'docs',
			fallback: undefined,
			precompress: false,
			strict: true
		}),
		// Set base path for GitHub Pages (repository name)
		paths: {
			base: '/FinalViz'
		}
	}
};

export default config;