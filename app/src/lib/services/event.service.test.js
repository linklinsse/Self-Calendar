/**
 * event.service.test.js — API <-> CalEvent (de)serialisation.
 *
 * The API field is `address`; the form and display components read the
 * French spelling `adresse` (see the CalEvent typedef). deserialise() used
 * to spread the raw API object straight through, so `adresse` was always
 * undefined on a loaded event: the location never showed in the edit form,
 * and since serialise() always sends `address` back (never omitted), every
 * edit of an existing event silently wiped whatever address it had.
 */

import { describe, expect, it } from 'vitest';
import { deserialise, serialise } from './event.service.js';

const RAW = {
  id: 'ev-1',
  calendar_id: 'cal-1',
  title: 'Dentist',
  description: null,
  date_start: 1770000000,
  date_end:   1770003600,
  category_id: null,
  color: null,
  address: '12 Rue de Rivoli, Paris',
  reminder: null,
  obj_recurence: null,
};

describe('deserialise', () => {
  it('surfaces the API address as adresse', () => {
    const ev = deserialise(RAW);
    expect(ev.adresse).toBe('12 Rue de Rivoli, Paris');
  });

  it('is null, not undefined, when the API has no address', () => {
    const ev = deserialise({ ...RAW, address: null });
    expect(ev.adresse).toBeNull();
  });
});

describe('serialise', () => {
  it('round-trips an address unchanged through deserialise -> serialise', () => {
    const ev = deserialise(RAW);
    const payload = serialise(ev);
    expect(payload.address).toBe('12 Rue de Rivoli, Paris');
  });
});
