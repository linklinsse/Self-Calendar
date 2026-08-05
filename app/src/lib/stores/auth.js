/**
 * stores/auth.js — Authentication state.
 *
 * Exports: currentUser, isLoggedIn, authLoading
 * Compound ops (loginUser, logoutUser) live in index.js because they
 * must reset other stores too, which would create circular deps here.
 */

import { writable, derived } from 'svelte/store';

/** @type {import('svelte/store').Writable<import('../services/auth.service').User|null>} */
export const currentUser = writable(null);

/** True when a user is authenticated. Derived from currentUser. */
export const isLoggedIn = derived(currentUser, $u => $u !== null);

/** True while a login/logout request is in flight. */
export const authLoading = writable(false);
