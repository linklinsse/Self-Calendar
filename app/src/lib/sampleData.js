/**
 * sampleData.js — Demo seed data (MOCK_MODE only).
 *
 * v3 changes:
 *  - Calendars use `title` instead of `name` (aligned with OpenAPI)
 *  - Categories now carry a `calendar_id` (they belong to a calendar)
 *  - Events use `calendar_id` / `category_id` (aligned with OpenAPI)
 *    and keep `startDate`/`endDate` + `start`/`end` for the local model
 */

export const CAT_COLORS = {
  personal: '#f4b8c8',
  work:     '#b8c9f4',
  health:   '#b8f4d4',
  social:   '#f4d8b8',
  travel:   '#d8b8f4',
};

// ─── Calendars ────────────────────────────────────────────────
// Field `title` (was `name`) — matches ObjCalendarSchemaComplete
export const sampleCalendars = [
  { id: 'personal', title: 'Personal', color: CAT_COLORS.personal, on: true },
  { id: 'work',     title: 'Work',     color: CAT_COLORS.work,     on: true },
  { id: 'family',   title: 'Family',   color: CAT_COLORS.health,   on: true },
];

// ─── Categories ───────────────────────────────────────────────
// Now scoped to a calendar via `calendar_id`
export const sampleCategories = [
  // Personal calendar
  { id: 'personal', calendar_id: 'personal', label: 'Personal', icon: '🌸', color: CAT_COLORS.personal, on: true },
  { id: 'health',   calendar_id: 'personal', label: 'Health',   icon: '🌿', color: CAT_COLORS.health,   on: true },
  { id: 'social',   calendar_id: 'personal', label: 'Social',   icon: '✨', color: CAT_COLORS.social,   on: true },
  { id: 'travel',   calendar_id: 'personal', label: 'Travel',   icon: '🌍', color: CAT_COLORS.travel,   on: true },
  // Work calendar
  { id: 'work',     calendar_id: 'work',     label: 'Work',     icon: '💼', color: CAT_COLORS.work,     on: true },
  // Family calendar
  { id: 'family',   calendar_id: 'family',   label: 'Family',   icon: '🏠', color: CAT_COLORS.health,   on: true },
];

// ─── Events ───────────────────────────────────────────────────
// Fields: calendar_id / category_id (API names)
//         startDate / endDate (local Date), allDay, start/end ("HH:MM")
export const sampleEvents = [
  {
    id: 1, title: 'Morning yoga',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,20), allDay: false,
    start: '07:00', end: '08:00',
    calendar_id: 'personal', category_id: 'health', color: CAT_COLORS.health,
    adresse: 'Studio Bloom', description: 'Vinyasa flow with Sarah.', recurrence_id: null,
    // legacy aliases kept for view compatibility
    calendar: 'personal', category: 'health', location: 'Studio Bloom', desc: 'Vinyasa flow with Sarah.',
  },
  {
    id: 2, title: 'Design review',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,20), allDay: false,
    start: '10:00', end: '11:30',
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'Room 3B', description: 'Review new component library.', recurrence_id: null,
    calendar: 'work', category: 'work', location: 'Room 3B', desc: 'Review new component library.',
  },
  {
    id: 3, title: 'Lunch with Marie',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,20), allDay: false,
    start: '12:30', end: '13:30',
    calendar_id: 'personal', category_id: 'social', color: CAT_COLORS.social,
    adresse: 'Le Jardin', description: 'She is back from Tokyo.', recurrence_id: null,
    calendar: 'personal', category: 'social', location: 'Le Jardin', desc: 'She is back from Tokyo.',
  },
  {
    id: 4, title: 'Product roadmap',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,20), allDay: false,
    start: '15:00', end: '16:30',
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'War Room', description: 'Q2 planning session.', recurrence_id: null,
    calendar: 'work', category: 'work', location: 'War Room', desc: 'Q2 planning session.',
  },
  {
    id: 5, title: 'Paris conference ✈',
    startDate: new Date(2026,2,23), endDate: new Date(2026,2,26), allDay: false,
    start: '08:00', end: '18:00',
    calendar_id: 'personal', category_id: 'travel', color: CAT_COLORS.travel,
    adresse: 'Paris, France', description: 'Tech conference at Palais des Congrès.', recurrence_id: null,
    calendar: 'personal', category: 'travel', location: 'Paris, France', desc: 'Tech conference at Palais des Congrès.',
  },
  {
    id: 6, title: 'Team offsite',
    startDate: new Date(2026,2,18), endDate: new Date(2026,2,19), allDay: true,
    start: null, end: null,
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'Lyon', description: 'Team building days.', recurrence_id: null,
    calendar: 'work', category: 'work', location: 'Lyon', desc: 'Team building days.',
  },
  {
    id: 7, title: "Maman's birthday 🎂",
    startDate: new Date(2026,2,25), endDate: new Date(2026,2,25), allDay: true,
    start: null, end: null,
    calendar_id: 'family', category_id: 'family', color: CAT_COLORS.health,
    adresse: '', description: "Don't forget flowers.", recurrence_id: null,
    calendar: 'family', category: 'family', location: '', desc: "Don't forget flowers.",
  },
  {
    id: 8, title: 'Daily standup',
    startDate: new Date(2026,2,16), endDate: new Date(2026,2,16), allDay: false,
    start: '09:00', end: '09:30',
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'Remote', description: 'Daily sync.', recurrence_id: null,
    calendar: 'work', category: 'work', location: 'Remote', desc: 'Daily sync.',
    recurrence: { type: 'daily', interval: 1, days: [], endType: 'never', count: null, until: null },
  },
  {
    id: 9, title: 'Evening run',
    startDate: new Date(2026,2,16), endDate: new Date(2026,2,16), allDay: false,
    start: '18:30', end: '19:30',
    calendar_id: 'personal', category_id: 'health', color: CAT_COLORS.health,
    adresse: 'Parc Nord', description: '8 km loop.', recurrence_id: null,
    calendar: 'personal', category: 'health', location: 'Parc Nord', desc: '8 km loop.',
    recurrence: { type: 'weekly', interval: 1, days: [1, 3, 5], endType: 'never', count: null, until: null },
  },
  {
    id: 10, title: 'Book club',
    startDate: new Date(2026,2,19), endDate: new Date(2026,2,19), allDay: false,
    start: '20:00', end: '21:30',
    calendar_id: 'personal', category_id: 'personal', color: CAT_COLORS.personal,
    adresse: "Isabelle's", description: 'La Horde du Contrevent.', recurrence_id: null,
    calendar: 'personal', category: 'personal', location: "Isabelle's", desc: 'La Horde du Contrevent.',
    recurrence: { type: 'weekly', interval: 2, days: [], endType: 'count', count: 12, until: null },
  },
  {
    id: 11, title: 'Weekend brunch',
    startDate: new Date(2026,2,21), endDate: new Date(2026,2,21), allDay: false,
    start: '11:00', end: '13:00',
    calendar_id: 'personal', category_id: 'social', color: CAT_COLORS.social,
    adresse: 'Café Lumière', description: 'With the whole crew.', recurrence_id: null,
    calendar: 'personal', category: 'social', location: 'Café Lumière', desc: 'With the whole crew.',
  },
  {
    id: 12, title: 'GP appointment',
    startDate: new Date(2026,2,17), endDate: new Date(2026,2,17), allDay: false,
    start: '14:00', end: '14:30',
    calendar_id: 'personal', category_id: 'health', color: CAT_COLORS.health,
    adresse: 'Dr. Laurent', description: 'Annual checkup.', recurrence_id: null,
    calendar: 'personal', category: 'health', location: 'Dr. Laurent', desc: 'Annual checkup.',
  },
  {
    id: 13, title: 'Call with Leo',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,20), allDay: false,
    start: '10:00', end: '11:00',
    calendar_id: 'personal', category_id: 'social', color: CAT_COLORS.social,
    adresse: 'Phone', description: 'Overlaps with Design review.', recurrence_id: null,
    calendar: 'personal', category: 'social', location: 'Phone', desc: 'Overlaps with Design review.',
  },
  {
    id: 14, title: 'Sprint planning',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,20), allDay: false,
    start: '10:30', end: '12:00',
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'War Room', description: 'Overlaps with Design review + Call with Leo.', recurrence_id: null,
    calendar: 'work', category: 'work', location: 'War Room', desc: 'Overlaps with Design review + Call with Leo.',
  },
  {
    id: 15, title: 'Late night coding',
    startDate: new Date(2026,2,20), endDate: new Date(2026,2,21), allDay: false,
    start: '22:00', end: '02:00',
    calendar_id: 'personal', category_id: 'personal', color: CAT_COLORS.personal,
    adresse: '', description: 'Hacking on the project.', recurrence_id: null,
    calendar: 'personal', category: 'personal', location: '', desc: 'Hacking on the project.',
  },
];
