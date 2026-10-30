/* ============================================================
   Bantay Daan Pasig — Near-real-time polling (30–60s)
   Replaces "real-time" with a measurable polling loop.
   ============================================================ */
(function () {
  'use strict';

  const INTERVAL_MS = 45000;

  function stamp() {
    const d = new Date();
    const time = d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    document.querySelectorAll('[data-poll="last-updated"]').forEach(el => {
      el.textContent = 'Last refreshed today, ' + time;
    });
  }

  async function refresh() {
    try {
      const response = await fetch('/api/advisories', { credentials: 'same-origin', cache: 'no-store' });
      if (response.ok) stamp();
    } catch (_) { /* Keep the previous refresh time when the API is unavailable. */ }
  }

  stamp();
  setInterval(refresh, INTERVAL_MS);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) refresh();
  });
})();