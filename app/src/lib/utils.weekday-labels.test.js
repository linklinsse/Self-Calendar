/**
 * utils.weekday-labels.test.js — locale-driven weekday headers.
 *
 * DAY_ABBR_MON / DOW_LETTERS used to be hardcoded English regardless of the
 * LOCALE config value, so a French deployment (the app's own default, see
 * config.js) still showed "Mon Tue Wed..." / "M T W..." headers. They're now
 * derived from Intl.DateTimeFormat(LOCALE, ...), which for the default
 * LOCALE=fr-FR and FIRST_DAY_OF_WEEK=1 produces French, Monday-first labels.
 */

import { describe, expect, it } from 'vitest';
import { DAY_ABBR_MON, DOW_LETTERS } from './utils.js';

describe('locale-driven weekday headers (default LOCALE=fr-FR, FIRST_DAY_OF_WEEK=1)', () => {
  it('DOW_LETTERS are the French Monday-first single letters', () => {
    expect(DOW_LETTERS).toEqual(['L', 'M', 'M', 'J', 'V', 'S', 'D']);
  });

  it('DAY_ABBR_MON are the French Monday-first short abbreviations', () => {
    expect(DAY_ABBR_MON).toEqual(['lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.', 'dim.']);
  });
});
