/**
 * sampleData.js — ALL mock / seed data lives here (MOCK_MODE only).
 *
 * Keeping every mock value in one place makes it trivial to swap them
 * out when connecting a real backend — just search this file.
 *
 * v3 changes:
 *  - Calendars use `title` instead of `name` (aligned with OpenAPI)
 *  - Categories now carry a `calendar_id` (they belong to a calendar)
 *  - Events use `calendar_id` / `category_id` (aligned with OpenAPI)
 *    and keep `startDate`/`endDate` + `start`/`end` for the local model
 */

// ─── Auth ──────────────────────────────────────────────────────
/** The fake user returned during MOCK_MODE login / getMe. */
export const MOCK_USER = { id: 'user-1', login: 'demo', name: 'Demo User', avatar: null };

// ─── User-Calendar links ───────────────────────────────────────
/**
 * Fake membership list returned by fetchUserCalendars in MOCK_MODE.
 * @param {string} calendarId
 */
export const MOCK_USER_CALENDARS = calendarId => [
  { id: 'lnk-1', user_id: 'user-1', username: 'demo',  calendar_id: calendarId, right: 'O' },
  { id: 'lnk-2', user_id: 'user-2', username: 'alice', calendar_id: calendarId, right: 'W' },
];

// ─── Colours ───────────────────────────────────────────────────
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
// Dates are expressed as offsets from today so the demo always has
// visible data regardless of when the app is opened.
// d(0) = today, d(-2) = two days ago, d(3) = three days from now.
function d(offsetDays, h = 0, m = 0) {
  const dt = new Date();
  dt.setDate(dt.getDate() + offsetDays);
  dt.setHours(h, m, 0, 0);
  return dt;
}

export const sampleEvents = [
  {
    id: 1, title: 'Morning yoga',
    startDate: d(0), endDate: d(0), allDay: false,
    start: '07:00', end: '08:00',
    calendar_id: 'personal', category_id: 'health', color: CAT_COLORS.health,
    adresse: 'Studio Bloom', description: 'Vinyasa flow with Sarah.', recurrence_id: null,
  },
  {
    id: 2, title: 'Design review',
    startDate: d(0), endDate: d(0), allDay: false,
    start: '10:00', end: '11:30',
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'Room 3B', description: 'Review new component library.', recurrence_id: null,
  },
  {
    id: 3, title: 'Lunch with Marie',
    startDate: d(0), endDate: d(0), allDay: false,
    start: '12:30', end: '13:30',
    calendar_id: 'personal', category_id: 'social', color: CAT_COLORS.social,
    adresse: 'Le Jardin', description: 'She is back from Tokyo.', recurrence_id: null,
  },
  {
    id: 4, title: 'Product roadmap',
    startDate: d(0), endDate: d(0), allDay: false,
    start: '15:00', end: '16:30',
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'War Room', description: 'Q2 planning session.', recurrence_id: null,
  },
  {
    id: 5, title: 'Paris conference ✈',
    startDate: d(3), endDate: d(6), allDay: false,
    start: '08:00', end: '18:00',
    calendar_id: 'personal', category_id: 'travel', color: CAT_COLORS.travel,
    adresse: 'Paris, France', description: 'Tech conference at Palais des Congrès.', recurrence_id: null,
  },
  {
    id: 6, title: 'Team offsite',
    startDate: d(-2), endDate: d(-1), allDay: true,
    start: null, end: null,
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'Lyon', description: 'Team building days.', recurrence_id: null,
  },
  {
    id: 7, title: "Maman's birthday 🎂",
    startDate: d(5), endDate: d(5), allDay: true,
    start: null, end: null,
    calendar_id: 'family', category_id: 'family', color: CAT_COLORS.health,
    adresse: '', description: "Don't forget flowers.", recurrence_id: null,
  },
  {
    id: 8, title: 'Daily standup',
    startDate: d(-4), endDate: d(-4), allDay: false,
    start: '09:00', end: '09:30',
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'Remote', description: 'Daily sync.', recurrence_id: null,
    recurrence: { type: 'daily', interval: 1, days: [], endType: 'never', count: null, until: null },
  },
  {
    id: 9, title: 'Evening run',
    startDate: d(-4), endDate: d(-4), allDay: false,
    start: '18:30', end: '19:30',
    calendar_id: 'personal', category_id: 'health', color: CAT_COLORS.health,
    adresse: 'Parc Nord', description: '8 km loop.', recurrence_id: null,
    recurrence: { type: 'weekly', interval: 1, days: [1, 3, 5], endType: 'never', count: null, until: null },
  },
  {
    id: 10, title: 'Book club',
    startDate: d(-1), endDate: d(-1), allDay: false,
    start: '20:00', end: '21:30',
    calendar_id: 'personal', category_id: 'personal', color: CAT_COLORS.personal,
    adresse: "Isabelle's", description: 'La Horde du Contrevent.', recurrence_id: null,
    recurrence: { type: 'weekly', interval: 2, days: [], endType: 'count', count: 12, until: null },
  },
  {
    id: 11, title: 'Weekend brunch',
    startDate: d(1), endDate: d(1), allDay: false,
    start: '11:00', end: '13:00',
    calendar_id: 'personal', category_id: 'social', color: CAT_COLORS.social,
    adresse: 'Café Lumière', description: 'With the whole crew.', recurrence_id: null,
  },
  {
    id: 12, title: 'GP appointment',
    startDate: d(-3), endDate: d(-3), allDay: false,
    start: '14:00', end: '14:30',
    calendar_id: 'personal', category_id: 'health', color: CAT_COLORS.health,
    adresse: 'Dr. Laurent', description: 'Annual checkup.', recurrence_id: null,
  },
  {
    id: 13, title: 'Call with Leo',
    startDate: d(0), endDate: d(0), allDay: false,
    start: '10:00', end: '11:00',
    calendar_id: 'personal', category_id: 'social', color: CAT_COLORS.social,
    adresse: 'Phone', description: 'Overlaps with Design review.', recurrence_id: null,
  },
  {
    id: 14, title: 'Sprint planning',
    startDate: d(0), endDate: d(0), allDay: false,
    start: '10:30', end: '12:00',
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'War Room', description: 'Overlaps with Design review + Call with Leo.', recurrence_id: null,
  },
  {
    id: 15, title: 'Late night coding',
    startDate: d(0), endDate: d(1), allDay: false,
    start: '22:00', end: '02:00',
    calendar_id: 'personal', category_id: 'personal', color: CAT_COLORS.personal,
    adresse: '', description: 'Hacking on the project.', recurrence_id: null,
  },
  {
    id: 16, title: 'Weekly review',
    startDate: d(-7), endDate: d(-7), allDay: false,
    start: '17:00', end: '17:30',
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'Remote', description: 'End-of-week wrap-up.', recurrence_id: null,
    recurrence: { type: 'weekly', interval: 1, days: [], endType: 'never', count: null, until: null },
  },
  {
    id: 17, title: 'Dentist 🦷',
    startDate: d(-9), endDate: d(-9), allDay: false,
    start: '09:30', end: '10:30',
    calendar_id: 'personal', category_id: 'health', color: CAT_COLORS.health,
    adresse: 'Dr. Fontaine', description: 'Routine cleaning.', recurrence_id: null,
  },
  {
    id: 18, title: 'Client presentation',
    startDate: d(-11), endDate: d(-11), allDay: false,
    start: '14:00', end: '15:30',
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'Zoom', description: 'Q2 results deck.', recurrence_id: null,
  },
  {
    id: 19, title: 'Family dinner 🍽',
    startDate: d(-5), endDate: d(-5), allDay: false,
    start: '19:30', end: '22:00',
    calendar_id: 'family', category_id: 'family', color: CAT_COLORS.health,
    adresse: 'Parents place', description: 'Sunday roast.', recurrence_id: null,
  },
  {
    id: 20, title: 'Hackathon 🚀',
    startDate: d(8), endDate: d(9), allDay: true,
    start: null, end: null,
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'Station F', description: '48h build sprint.', recurrence_id: null,
  },
  {
    id: 21, title: 'Pilates',
    startDate: d(7), endDate: d(7), allDay: false,
    start: '08:00', end: '09:00',
    calendar_id: 'personal', category_id: 'health', color: CAT_COLORS.health,
    adresse: 'Studio Zen', description: 'Mat pilates.', recurrence_id: null,
    recurrence: { type: 'weekly', interval: 1, days: [2, 4], endType: 'never', count: null, until: null },
  },
  {
    id: 22, title: 'Cinema night 🎬',
    startDate: d(10), endDate: d(10), allDay: false,
    start: '20:30', end: '23:00',
    calendar_id: 'personal', category_id: 'social', color: CAT_COLORS.social,
    adresse: 'UGC Ciné Cité', description: 'New thriller with Jules.', recurrence_id: null,
  },
  {
    id: 23, title: 'Quarterly OKRs',
    startDate: d(12), endDate: d(12), allDay: false,
    start: '10:00', end: '12:00',
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'HQ', description: 'Set Q3 objectives.', recurrence_id: null,
  },
  {
    id: 24, title: 'Anniversary dinner ❤️',
    startDate: d(14), endDate: d(14), allDay: false,
    start: '20:00', end: '23:00',
    calendar_id: 'personal', category_id: 'personal', color: CAT_COLORS.personal,
    adresse: 'Chez Pierre', description: '5 years!', recurrence_id: null,
  },
  {
    id: 25, title: 'Half marathon 🏃',
    startDate: d(18), endDate: d(18), allDay: false,
    start: '08:30', end: '11:30',
    calendar_id: 'personal', category_id: 'health', color: CAT_COLORS.health,
    adresse: 'Bois de Vincennes', description: '21km race day.', recurrence_id: null,
  },
  {
    id: 26, title: 'School holiday',
    startDate: d(20), endDate: d(25), allDay: true,
    start: null, end: null,
    calendar_id: 'family', category_id: 'family', color: CAT_COLORS.health,
    adresse: '', description: 'Kids off school.', recurrence_id: null,
  },
  {
    id: 27, title: 'Ski trip ⛷',
    startDate: d(21), endDate: d(24), allDay: false,
    start: '07:00', end: '20:00',
    calendar_id: 'personal', category_id: 'travel', color: CAT_COLORS.travel,
    adresse: 'Les Deux Alpes', description: 'Family ski weekend.', recurrence_id: null,
  },
  {
    id: 28, title: 'Onboarding Thomas',
    startDate: d(-13), endDate: d(-13), allDay: false,
    start: '09:00', end: '11:00',
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'Office', description: 'Welcome new hire.', recurrence_id: null,
  },
  {
    id: 29, title: 'Yoga retreat',
    startDate: d(-15), endDate: d(-14), allDay: true,
    start: null, end: null,
    calendar_id: 'personal', category_id: 'health', color: CAT_COLORS.health,
    adresse: 'Normandie', description: 'Weekend detox.', recurrence_id: null,
  },
  {
    id: 30, title: 'Budget review',
    startDate: d(-6), endDate: d(-6), allDay: false,
    start: '11:00', end: '12:00',
    calendar_id: 'work', category_id: 'work', color: CAT_COLORS.work,
    adresse: 'Finance room', description: 'Monthly accounts.', recurrence_id: null,
  },
];
