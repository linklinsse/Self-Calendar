/**
 * category.service.js — Category HTTP service.
 *
 * Endpoints (OpenAPI):
 *   POST   /category/                          body → Category
 *   GET    /category/calendar/{calendar_id}          → Category[]
 *   GET    /category/{id}                             → Category
 *   PATCH  /category/{id}                       body → Category
 *   DELETE /category/{id}                              → void
 *
 * The API only stores `title` and `color` per category (see
 * ObjCategorySchemaBase) — there is no `icon` column server-side. `icon`
 * is therefore kept as a small local-only overlay (id → emoji), merged
 * onto the server record on read. Everything else (label, color,
 * calendar_id) is authoritative on the server so categories are
 * consistent across devices/logins, same as calendars.
 */

import { api } from './api.js';

// ─── Local icon overlay ─────────────────────────────────────────────────────
const ICON_LS_KEY = 'sc_category_icons';
const DEFAULT_ICON = '🌸';

function loadIcons() {
  try {
    const raw = localStorage.getItem(ICON_LS_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch { return {}; }
}

function saveIcons(icons) {
  try { localStorage.setItem(ICON_LS_KEY, JSON.stringify(icons)); } catch { /* ignore */ }
}

// ─── Types ────────────────────────────────────────────────────────────────────

/**
 * @typedef {Object} Category
 * @property {string}  id
 * @property {string}  calendar_id  — the calendar this category belongs to
 * @property {string}  label        — display name, e.g. "Work"
 * @property {string}  icon         — emoji, e.g. "💼" (client-only)
 * @property {string}  color        — hex colour, e.g. "#b8c9f4"
 * @property {boolean} on           — local filter visibility toggle (not persisted)
 */

/** Map an API category record (`title`/`color`) to the client shape (`label`/`icon`/`color`). */
function toClient(apiCat, icons) {
  return {
    id: apiCat.id,
    calendar_id: apiCat.calendar_id,
    label: apiCat.title,
    color: apiCat.color,
    icon: icons[apiCat.id] ?? DEFAULT_ICON,
  };
}

// ─── Service ──────────────────────────────────────────────────────────────────

/**
 * Fetch all categories across the given calendars (there is no
 * "all my categories" endpoint — categories are listed per calendar).
 * @param {string[]} calendarIds
 * @returns {Promise<Category[]>}
 */
export async function fetchCategories(calendarIds) {
  const icons = loadIcons();
  const lists = await Promise.all(
    (calendarIds ?? []).map(id => api.get(`/category/calendar/${id}`))
  );
  return lists.flat().map(c => toClient(c, icons));
}

/**
 * Create a new category.
 * @param {{ calendar_id: string, label: string, icon?: string, color: string }} payload
 * @returns {Promise<Category>}
 */
export async function createCategory(payload) {
  const created = await api.post('/category/', {
    calendar_id: payload.calendar_id,
    title: payload.label,
    color: payload.color,
  });
  const icons = loadIcons();
  icons[created.id] = payload.icon ?? DEFAULT_ICON;
  saveIcons(icons);
  return toClient(created, icons);
}

/**
 * Update an existing category.
 * @param {string} id
 * @param {{ label?: string, icon?: string, color?: string }} payload
 * @returns {Promise<Category>}
 */
export async function updateCategory(id, payload) {
  const body = {};
  if (payload.label !== undefined) body.title = payload.label;
  if (payload.color !== undefined) body.color = payload.color;

  const updated = Object.keys(body).length
    ? await api.patch(`/category/${id}`, body)
    : await api.get(`/category/${id}`);

  const icons = loadIcons();
  if (payload.icon !== undefined) {
    icons[id] = payload.icon;
    saveIcons(icons);
  }
  return toClient(updated, icons);
}

/**
 * Delete a category.
 * @param {string} id
 * @returns {Promise<void>}
 */
export async function deleteCategory(id) {
  await api.delete(`/category/${id}`);
  const icons = loadIcons();
  delete icons[id];
  saveIcons(icons);
}
