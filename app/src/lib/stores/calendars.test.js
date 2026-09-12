/**
 * calendars.test.js — hidden-calendar persistence and reordering.
 *
 * loadCalendars() used to hardcode `on: true` for every calendar on every
 * load, so toggling a calendar off never survived a reload (see TODO).
 * These tests pin the localStorage-backed fix, plus the reorderCalendars()
 * added for the "reorder calendars" TODO item.
 */

import { describe, expect, it, vi, beforeEach } from 'vitest';
import { get } from 'svelte/store';

vi.mock('../services/calendar.service.js', () => ({
  fetchCalendars: vi.fn(),
  createCalendar: vi.fn(),
  updateCalendar: vi.fn(),
  deleteCalendar: vi.fn(),
  reorderCalendars: vi.fn(),
}));

import * as calSvc from '../services/calendar.service.js';
import {
  calendars, loadCalendars, toggleCalendar, removeCalendar, reorderCalendars,
} from './calendars.js';

function createFakeStorage() {
  const store = new Map();
  return {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
  };
}

const CAL_A = { id: 'a', title: 'A', color: '#111111' };
const CAL_B = { id: 'b', title: 'B', color: '#222222' };
const CAL_C = { id: 'c', title: 'C', color: '#333333' };

const HIDDEN_KEY = 'sc_hidden_calendars';

beforeEach(() => {
  vi.stubGlobal('localStorage', createFakeStorage());
  calSvc.fetchCalendars.mockReset();
  calSvc.deleteCalendar.mockReset();
  calSvc.reorderCalendars.mockReset();
});

describe('loadCalendars — hidden-calendar persistence', () => {
  it('defaults every calendar to visible when nothing is hidden', async () => {
    calSvc.fetchCalendars.mockResolvedValue([CAL_A, CAL_B]);

    await loadCalendars();

    expect(get(calendars).map((c) => c.on)).toEqual([true, true]);
  });

  it('restores a previously hidden calendar as hidden', async () => {
    localStorage.setItem(HIDDEN_KEY, JSON.stringify(['b']));
    calSvc.fetchCalendars.mockResolvedValue([CAL_A, CAL_B]);

    await loadCalendars();

    const onById = Object.fromEntries(get(calendars).map((c) => [c.id, c.on]));
    expect(onById).toEqual({ a: true, b: false });
  });
});

describe('toggleCalendar — persists across a reload', () => {
  beforeEach(async () => {
    calSvc.fetchCalendars.mockResolvedValue([CAL_A, CAL_B]);
    await loadCalendars();
  });

  it('hiding a calendar persists the hidden id', () => {
    toggleCalendar('a');

    expect(get(calendars).find((c) => c.id === 'a').on).toBe(false);
    expect(JSON.parse(localStorage.getItem(HIDDEN_KEY))).toEqual(['a']);
  });

  it('a calendar hidden and then reloaded stays hidden', async () => {
    toggleCalendar('a');
    await loadCalendars(); // simulates a page reload against the same storage

    expect(get(calendars).find((c) => c.id === 'a').on).toBe(false);
  });

  it('showing a previously hidden calendar removes it from the persisted set', () => {
    toggleCalendar('a'); // hide
    toggleCalendar('a'); // show again

    expect(get(calendars).find((c) => c.id === 'a').on).toBe(true);
    expect(JSON.parse(localStorage.getItem(HIDDEN_KEY))).toEqual([]);
  });
});

describe('removeCalendar — prunes the persisted hidden set', () => {
  it('drops a deleted calendar id from storage so it cannot linger', async () => {
    localStorage.setItem(HIDDEN_KEY, JSON.stringify(['a', 'b']));
    calSvc.fetchCalendars.mockResolvedValue([CAL_A, CAL_B]);
    await loadCalendars();

    calSvc.deleteCalendar.mockResolvedValue(undefined);
    await removeCalendar('a');

    expect(JSON.parse(localStorage.getItem(HIDDEN_KEY))).toEqual(['b']);
  });
});

describe('reorderCalendars', () => {
  beforeEach(async () => {
    calSvc.fetchCalendars.mockResolvedValue([CAL_A, CAL_B, CAL_C]);
    await loadCalendars();
  });

  it('applies the new order optimistically and saves it via the service', async () => {
    calSvc.reorderCalendars.mockResolvedValue(undefined);

    await reorderCalendars(['c', 'a', 'b']);

    expect(get(calendars).map((c) => c.id)).toEqual(['c', 'a', 'b']);
    expect(calSvc.reorderCalendars).toHaveBeenCalledWith(['c', 'a', 'b']);
  });

  it('reverts to the previous order when saving fails', async () => {
    const before = get(calendars).map((c) => c.id);
    calSvc.reorderCalendars.mockRejectedValue(new Error('network down'));

    await reorderCalendars(['c', 'a', 'b']);

    expect(get(calendars).map((c) => c.id)).toEqual(before);
  });
});
