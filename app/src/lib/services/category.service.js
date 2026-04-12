/**
 * category.service.js — Category service (local / mock only).
 *
 * NOTE: The Self Calendar API (openapi.json) does not expose a /categories
 * endpoint. Categories are referenced by `category_id` on events and are
 * managed locally on the client. This service therefore always falls back
 * to sampleData in MOCK_MODE and operates on localStorage in live mode.
 *
 * Each category is scoped to a calendar via `calendar_id`.
 */

import { MOCK_MODE } from '../config.js';
import { sampleCategories } from '../sampleData.js';

// ─── Local storage key ────────────────────────────────────────────────────────
const LS_KEY = 'sc_categories';

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function saveToStorage(cats) {
  try { localStorage.setItem(LS_KEY, JSON.stringify(cats)); } catch { /* ignore */ }
}

// ─── Types ────────────────────────────────────────────────────────────────────

/**
 * @typedef {Object} Category
 * @property {string}  id
 * @property {string}  calendar_id  — the calendar this category belongs to
 * @property {string}  label        — display name, e.g. "Work"
 * @property {string}  icon         — emoji, e.g. "💼"
 * @property {string}  color        — hex colour, e.g. "#b8c9f4"
 * @property {boolean} on           — local filter visibility toggle (not persisted)
 */

// ─── Service ──────────────────────────────────────────────────────────────────

/**
 * Fetch all categories.
 * @returns {Promise<Category[]>}
 */
export async function fetchCategories() {
  if (MOCK_MODE) return sampleCategories.map(c => ({ on: true, ...c }));
  const stored = loadFromStorage();
  const data = stored ?? sampleCategories;
  return data.map(c => ({ on: true, ...c }));
}

/**
 * Create a new category.
 * @param {{ calendar_id: string, label: string, icon: string, color: string }} payload
 * @returns {Promise<Category>}
 */
export async function createCategory(payload) {
  const cat = { id: `cat-${Date.now()}`, on: true, ...payload };
  if (!MOCK_MODE) {
    const stored = loadFromStorage() ?? [];
    saveToStorage([...stored, cat]);
  }
  return cat;
}

/**
 * Update an existing category.
 * @param {string} id
 * @param {{ label?: string, icon?: string, color?: string, calendar_id?: string }} payload
 * @returns {Promise<Category>}
 */
export async function updateCategory(id, payload) {
  if (!MOCK_MODE) {
    const stored = loadFromStorage() ?? [];
    const updated = stored.map(c => c.id === id ? { ...c, ...payload } : c);
    saveToStorage(updated);
    return updated.find(c => c.id === id) ?? { id, on: true, ...payload };
  }
  return { id, on: true, ...payload };
}

/**
 * Delete a category.
 * @param {string} id
 * @returns {Promise<void>}
 */
export async function deleteCategory(id) {
  if (!MOCK_MODE) {
    const stored = loadFromStorage() ?? [];
    saveToStorage(stored.filter(c => c.id !== id));
  }
}
