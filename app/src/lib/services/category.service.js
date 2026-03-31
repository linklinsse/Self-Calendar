/**
 * category.service.js — Category HTTP service.
 *
 * Endpoints (when MOCK_MODE = false):
 *   GET    /categories            → Category[]
 *   POST   /categories  body      → Category
 *   PUT    /categories/:id body   → Category
 *   DELETE /categories/:id        → void
 *
 * Categories belong to the user (not to a specific calendar).
 * Each category has a name, icon (emoji), hex colour, and a visibility toggle.
 */

import { api, MOCK_MODE } from './api.js';
import { sampleCategories } from '../sampleData.js';

// ─── Types ────────────────────────────────────────────────────────────────────

/**
 * @typedef {Object} Category
 * @property {string}  id
 * @property {string}  label     — Display name, e.g. "Work"
 * @property {string}  icon      — Emoji, e.g. "💼"
 * @property {string}  color     — Hex colour, e.g. "#b8c9f4"
 * @property {boolean} on        — Local filter visibility toggle (not persisted)
 */

// ─── Service ──────────────────────────────────────────────────────────────────

/**
 * Fetch the user's categories.
 * @returns {Promise<Category[]>}
 */
export async function fetchCategories() {
  if (MOCK_MODE) return sampleCategories.map(c => ({ ...c }));
  const data = await api.get('/categories');
  return data.map(c => ({ on: true, ...c }));
}

/**
 * Create a new category.
 * @param {{ label: string, icon: string, color: string }} payload
 * @returns {Promise<Category>}
 */
export async function createCategory(payload) {
  if (MOCK_MODE) {
    return { id: `cat-${Date.now()}`, on: true, ...payload };
  }
  const cat = await api.post('/categories', payload);
  return { on: true, ...cat };
}

/**
 * Update an existing category.
 * @param {string} id
 * @param {{ label?: string, icon?: string, color?: string }} payload
 * @returns {Promise<Category>}
 */
export async function updateCategory(id, payload) {
  if (MOCK_MODE) return { id, on: true, ...payload };
  return api.put(`/categories/${id}`, payload);
}

/**
 * Delete a category.
 * @param {string} id
 * @returns {Promise<void>}
 */
export async function deleteCategory(id) {
  if (MOCK_MODE) return;
  return api.delete(`/categories/${id}`);
}
