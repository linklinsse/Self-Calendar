/**
 * stores/categories.js — Category list state and CRUD.
 *
 * Categories are scoped to a calendar via `calendar_id`.
 * There is no /categories API endpoint; data lives locally.
 *
 * Key exported derived helpers:
 *   categoriesForCalendars(calendarIds) — returns only categories
 *     belonging to the given calendar ids (used by FilterDrawer /
 *     CategoryList to hide categories when their calendar is off).
 */

import { writable, derived, get } from 'svelte/store';
import { sampleCategories } from '../sampleData.js';
import * as catSvc from '../services/category.service.js';
import { showToast } from './ui.js';
import { calendars } from './calendars.js';

// ── Store ─────────────────────────────────────────────────────

/** @type {import('svelte/store').Writable<import('../services/category.service').Category[]>} */
export const categories = writable([...sampleCategories]);

// ── Derived: categories filtered by active calendars ──────────

/**
 * Only the categories whose calendar is currently toggled ON.
 * Used by sidebar + filter drawer to hide orphaned categories.
 *
 * @type {import('svelte/store').Readable<import('../services/category.service').Category[]>}
 */
export const visibleCategories = derived(
  [categories, calendars],
  ([$cats, $cals]) => {
    const activeCals = new Set($cals.filter(c => c.on).map(c => c.id));
    return $cats.filter(c => activeCals.has(c.calendar_id));
  }
);

// ── Load ──────────────────────────────────────────────────────

export async function loadCategories() {
  try {
    const data = await catSvc.fetchCategories();
    if (data) categories.set(data.map(c => ({ on: true, ...c })));
  } catch (e) {
    showToast('Could not load categories: ' + e.message, 'error');
  }
}

// ── Create ────────────────────────────────────────────────────

/**
 * @param {{ calendar_id: string, label: string, icon: string, color: string }} payload
 */
export async function createCategory(payload) {
  try {
    const cat = await catSvc.createCategory(payload);
    categories.update(list => [...list, { on: true, ...cat }]);
    showToast(`Category "${cat.label}" created`, 'success');
    return cat;
  } catch (e) {
    showToast('Error: ' + e.message, 'error');
    throw e;
  }
}

// ── Update ────────────────────────────────────────────────────

/**
 * @param {string} id
 * @param {object} payload
 */
export async function updateCategory(id, payload) {
  try {
    const updated = await catSvc.updateCategory(id, payload);
    categories.update(list =>
      list.map(c => c.id === id ? { ...c, ...updated } : c)
    );
    showToast('Category updated', 'success');
  } catch (e) {
    showToast('Error: ' + e.message, 'error');
  }
}

// ── Delete ────────────────────────────────────────────────────

/** @param {string} id */
export async function removeCategory(id) {
  const cat = get(categories).find(c => c.id === id);
  try {
    await catSvc.deleteCategory(id);
    categories.update(list => list.filter(c => c.id !== id));
    showToast(`Category "${cat?.label}" deleted`);
  } catch (e) {
    showToast('Error: ' + e.message, 'error');
  }
}

// ── Filter toggle ─────────────────────────────────────────────

/** Toggle a category's filter visibility. */
export function toggleCategory(id) {
  categories.update(list =>
    list.map(c => c.id === id ? { ...c, on: !c.on } : c)
  );
}

// ── Calendar cascade ──────────────────────────────────────────

/**
 * Called when a calendar is deleted: removes all its categories from local state.
 * @param {string} calendarId
 */
export function removeCategoriesByCalendar(calendarId) {
  categories.update(list => list.filter(c => c.calendar_id !== calendarId));
}
