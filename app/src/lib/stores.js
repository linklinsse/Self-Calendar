/**
 * stores.js — Compatibility shim.
 *
 * All store logic has been split into src/lib/stores/ (multiple files).
 * This file re-exports everything from the new location so existing
 * imports still work during migration. Prefer importing directly from
 * 'src/lib/stores/index.js' in new code.
 */
export * from './stores/index.js';
