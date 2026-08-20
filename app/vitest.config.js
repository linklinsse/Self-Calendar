import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    // The recurrence conformance fixture is generated in UTC so it is
    // reproducible on any machine. The expansion under test works in local
    // civil time, so the two only agree when the test process is on UTC.
    // Without this the suite fails everywhere except a UTC machine — and,
    // worse, would pass in CI while failing on a developer's laptop.
    env: { TZ: 'UTC' },
  },
});
