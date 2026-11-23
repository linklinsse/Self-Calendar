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
 * Everything (label → API `title`, color, icon, calendar_id) is stored on
 * the server, so categories look the same on every device/browser/login.
 *
 * `icon` used to be a localStorage-only overlay (id → emoji). Any browser
 * that had not picked the icon itself — another browser, a private window,
 * cleared site data, the mobile app vs. the web — showed every category
 * with the same default icon. That overlay is now only read to recover
 * legacy icons: a category whose server icon is still NULL gets the local
 * one uploaded once (see backfillLegacyIcons), then the entry is dropped.
 */

import { api } from './api.js';

const DEFAULT_ICON = '🌸';

// ─── Legacy local icon overlay (read-only migration source) ─────────────────
const LEGACY_ICON_LS_KEY = 'sc_category_icons';

function loadLegacyIcons() {
  try {
    const raw = localStorage.getItem(LEGACY_ICON_LS_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch { return {}; }
}

function saveLegacyIcons(icons) {
  try {
    if (Object.keys(icons).length) localStorage.setItem(LEGACY_ICON_LS_KEY, JSON.stringify(icons));
    else localStorage.removeItem(LEGACY_ICON_LS_KEY);
  } catch { /* ignore */ }
}

function forgetLegacyIcons(ids) {
  const icons = loadLegacyIcons();
  let changed = false;
  for (const id of ids) {
    if (id in icons) { delete icons[id]; changed = true; }
  }
  if (changed) saveLegacyIcons(icons);
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

/** Map an API category record (`title`/`color`/`icon`) to the client shape. */
function toClient(apiCat, legacyIcons = {}) {
  return {
    id: apiCat.id,
    calendar_id: apiCat.calendar_id,
    label: apiCat.title,
    color: apiCat.color,
    icon: apiCat.icon || legacyIcons[apiCat.id] || DEFAULT_ICON,
  };
}

/**
 * Upload icons that only exist in this device's legacy localStorage overlay
 * for categories the server has no icon for yet. Best-effort: a failure
 * (offline, read-only calendar) keeps the local entry, which still displays
 * through toClient's fallback and is retried on the next load.
 * @param {object[]} apiCats — raw API records
 * @param {Record<string,string>} legacyIcons
 */
async function backfillLegacyIcons(apiCats, legacyIcons) {
  // Entries the server already has an icon for are obsolete — drop them.
  forgetLegacyIcons(apiCats.filter(c => c.icon).map(c => c.id));

  // `=== null`, not falsy: an API too old to have the column omits the key
  // entirely, and PATCHing it there would be ignored and retried forever.
  const pending = apiCats.filter(c => c.icon === null && legacyIcons[c.id]);
  const results = await Promise.allSettled(
    pending.map(c => api.patch(`/category/${c.id}`, { icon: legacyIcons[c.id] }))
  );
  forgetLegacyIcons(pending.filter((_, i) => results[i].status === 'fulfilled').map(c => c.id));
}

// ─── Service ──────────────────────────────────────────────────────────────────

/**
 * Fetch all categories across the given calendars (there is no
 * "all my categories" endpoint — categories are listed per calendar).
 * @param {string[]} calendarIds
 * @returns {Promise<Category[]>}
 */
export async function fetchCategories(calendarIds) {
  const lists = await Promise.all(
    (calendarIds ?? []).map(id => api.get(`/category/calendar/${id}`))
  );
  const apiCats = lists.flat();
  const legacyIcons = loadLegacyIcons();
  if (Object.keys(legacyIcons).length) {
    // Not awaited: the list renders right away with the local icon as a
    // fallback; the upload only matters for the *other* devices.
    backfillLegacyIcons(apiCats, legacyIcons);
  }
  return apiCats.map(c => toClient(c, legacyIcons));
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
    icon: payload.icon || DEFAULT_ICON,
  });
  return toClient(created);
}

/**
 * Update an existing category.
 * @param {string} id
 * @param {{ label?: string, icon?: string, color?: string, calendar_id?: string }} payload
 * @returns {Promise<Category>}
 */
export async function updateCategory(id, payload) {
  const body = {};
  if (payload.label !== undefined) body.title = payload.label;
  if (payload.color !== undefined) body.color = payload.color;
  if (payload.icon !== undefined) body.icon = payload.icon || DEFAULT_ICON;
  if (payload.calendar_id !== undefined) body.calendar_id = payload.calendar_id;

  const updated = Object.keys(body).length
    ? await api.patch(`/category/${id}`, body)
    : await api.get(`/category/${id}`);

  // The server value is authoritative from now on.
  if (payload.icon !== undefined) forgetLegacyIcons([id]);
  return toClient(updated, loadLegacyIcons());
}

/**
 * Delete a category.
 * @param {string} id
 * @returns {Promise<void>}
 */
export async function deleteCategory(id) {
  await api.delete(`/category/${id}`);
  forgetLegacyIcons([id]);
}
