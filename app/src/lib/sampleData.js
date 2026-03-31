/**
 * sampleData.js — Demo seed data (MOCK_MODE only).
 *
 * Event model v2:
 *   startDate  — Date (replaces `date`)
 *   endDate    — Date (same as startDate for single-day events)
 *   allDay     — boolean (if true, start/end time strings are ignored)
 *   start/end  — "HH:MM" strings (used only when !allDay)
 *   recurrence — null | RecurrenceRule
 *
 * RecurrenceRule: {
 *   type:     'daily' | 'weekly' | 'monthly' | 'yearly'
 *   interval: number              (e.g. 2 = every 2 weeks)
 *   days:     number[]            (for weekly: 0=Sun … 6=Sat)
 *   endType:  'never'|'count'|'until'
 *   count:    number              (max occurrences, when endType='count')
 *   until:    Date                (stop date, when endType='until')
 * }
 */

export const CAT_COLORS = {
  personal: '#f4b8c8',
  work:     '#b8c9f4',
  health:   '#b8f4d4',
  social:   '#f4d8b8',
  travel:   '#d8b8f4',
};

// ─── Calendars ────────────────────────────────────────────────
export const sampleCalendars = [
  { id: 'personal', name: 'Personal', color: CAT_COLORS.personal, on: true, role: 'admin', ownerId: 'user-1' },
  { id: 'work',     name: 'Work',     color: CAT_COLORS.work,     on: true, role: 'admin', ownerId: 'user-1' },
  { id: 'family',   name: 'Family',   color: CAT_COLORS.health,   on: true, role: 'admin', ownerId: 'user-1' },
];

// ─── Categories ───────────────────────────────────────────────
export const sampleCategories = [
  { id: 'personal', label: 'Personal', icon: '🌸', color: CAT_COLORS.personal, on: true },
  { id: 'work',     label: 'Work',     icon: '💼', color: CAT_COLORS.work,     on: true },
  { id: 'health',   label: 'Health',   icon: '🌿', color: CAT_COLORS.health,   on: true },
  { id: 'social',   label: 'Social',   icon: '✨', color: CAT_COLORS.social,   on: true },
  { id: 'travel',   label: 'Travel',   icon: '🌍', color: CAT_COLORS.travel,   on: true },
];

// ─── Events ───────────────────────────────────────────────────
export const sampleEvents = [
  // Single-day timed events
  {
    id: 1, title: 'Morning yoga',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,20), allDay: false,
    start: '07:00', end: '08:00',
    calendar: 'personal', category: 'health', color: CAT_COLORS.health,
    location: 'Studio Bloom', desc: 'Vinyasa flow with Sarah.', recurrence: null,
  },
  {
    id: 2, title: 'Design review',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,20), allDay: false,
    start: '10:00', end: '11:30',
    calendar: 'work', category: 'work', color: CAT_COLORS.work,
    location: 'Room 3B', desc: 'Review new component library.', recurrence: null,
  },
  {
    id: 3, title: 'Lunch with Marie',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,20), allDay: false,
    start: '12:30', end: '13:30',
    calendar: 'personal', category: 'social', color: CAT_COLORS.social,
    location: 'Le Jardin', desc: 'She is back from Tokyo.', recurrence: null,
  },
  {
    id: 4, title: 'Product roadmap',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,20), allDay: false,
    start: '15:00', end: '16:30',
    calendar: 'work', category: 'work', color: CAT_COLORS.work,
    location: 'War Room', desc: 'Q2 planning session.', recurrence: null,
  },
  // Multi-day timed event
  {
    id: 5, title: 'Paris conference ✈',
    startDate: new Date(2026,2,23), endDate: new Date(2026,2,26), allDay: false,
    start: '08:00', end: '18:00',
    calendar: 'personal', category: 'travel', color: CAT_COLORS.travel,
    location: 'Paris, France', desc: 'Tech conference at Palais des Congrès.', recurrence: null,
  },
  // All-day events
  {
    id: 6, title: 'Team offsite',
    startDate: new Date(2026,2,18), endDate: new Date(2026,2,19), allDay: true,
    start: null, end: null,
    calendar: 'work', category: 'work', color: CAT_COLORS.work,
    location: 'Lyon', desc: 'Team building days.', recurrence: null,
  },
  {
    id: 7, title: "Maman's birthday 🎂",
    startDate: new Date(2026,2,25), endDate: new Date(2026,2,25), allDay: true,
    start: null, end: null,
    calendar: 'family', category: 'social', color: CAT_COLORS.social,
    location: '', desc: "Don't forget flowers.", recurrence: null,
  },
  // Recurring events
  {
    id: 8, title: 'Daily standup',
    startDate: new Date(2026,2,16), endDate: new Date(2026,2,16), allDay: false,
    start: '09:00', end: '09:30',
    calendar: 'work', category: 'work', color: CAT_COLORS.work,
    location: 'Remote', desc: 'Daily sync.',
    recurrence: { type: 'daily', interval: 1, days: [], endType: 'never', count: null, until: null },
  },
  {
    id: 9, title: 'Evening run',
    startDate: new Date(2026,2,16), endDate: new Date(2026,2,16), allDay: false,
    start: '18:30', end: '19:30',
    calendar: 'personal', category: 'health', color: CAT_COLORS.health,
    location: 'Parc Nord', desc: '8 km loop.',
    recurrence: { type: 'weekly', interval: 1, days: [1, 3, 5], endType: 'never', count: null, until: null },
  },
  {
    id: 10, title: 'Book club',
    startDate: new Date(2026,2,19), endDate: new Date(2026,2,19), allDay: false,
    start: '20:00', end: '21:30',
    calendar: 'personal', category: 'personal', color: CAT_COLORS.personal,
    location: "Isabelle's", desc: 'La Horde du Contrevent.',
    recurrence: { type: 'weekly', interval: 2, days: [], endType: 'count', count: 12, until: null },
  },
  {
    id: 11, title: 'Weekend brunch',
    startDate: new Date(2026,2,21), endDate: new Date(2026,2,21), allDay: false,
    start: '11:00', end: '13:00',
    calendar: 'personal', category: 'social', color: CAT_COLORS.social,
    location: 'Café Lumière', desc: 'With the whole crew.', recurrence: null,
  },
  {
    id: 12, title: 'GP appointment',
    startDate: new Date(2026,2,17), endDate: new Date(2026,2,17), allDay: false,
    start: '14:00', end: '14:30',
    calendar: 'personal', category: 'health', color: CAT_COLORS.health,
    location: 'Dr. Laurent', desc: 'Annual checkup.', recurrence: null,
  },
  // Overlapping events on March 20 — exercises the side-by-side column layout
  {
    id: 13, title: 'Call with Leo',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,20), allDay: false,
    start: '10:00', end: '11:00',
    calendar: 'personal', category: 'social', color: CAT_COLORS.social,
    location: 'Phone', desc: 'Overlaps with Design review.', recurrence: null,
  },
  {
    id: 14, title: 'Sprint planning',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,20), allDay: false,
    start: '10:30', end: '12:00',
    calendar: 'work', category: 'work', color: CAT_COLORS.work,
    location: 'War Room', desc: 'Overlaps with Design review + Call with Leo.', recurrence: null,
  },
  // Cross-midnight timed event — exercises week/day view clipping (start day shows 22:00→23:59, end day 00:00→02:00)
  {
    id: 15, title: 'Late night coding',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,21), allDay: false,
    start: '22:00', end: '02:00',
    calendar: 'personal', category: 'personal', color: CAT_COLORS.personal,
    location: '', desc: 'Hacking on the project.', recurrence: null,
  },
];
