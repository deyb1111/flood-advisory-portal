/* Near-real-time refresh (same polling approach as polling.js).
   Re-fetches the current URL (filters/pagination preserved) and swaps every
   [data-live="name"] region. Used by resident My Reports and the personnel
   dashboard / report list, so both sides reflect the same DB state. */
(function () {
  'use strict';
  const INTERVAL_MS = 3000;
  let busy = false;
  // CSRF tokens differ on every render; ignore them when diffing so open forms aren't reset.
  const norm = h => h.replace(/(name="csrf_token"\s+value=")[^"]*/g, '$1');

  async function refresh() {
    if (busy || document.hidden) return;
    busy = true;
    try {
      const res = await fetch(location.href, {
        credentials: 'same-origin', cache: 'no-store', headers: { 'X-Requested-With': 'fetch' }
      });
      if (!res.ok || res.redirected) return;   // e.g. session expired -> login redirect
      const doc = new DOMParser().parseFromString(await res.text(), 'text/html');
      document.querySelectorAll('[data-live]').forEach(el => {
        const next = doc.querySelector('[data-live="' + el.dataset.live + '"]');
        if (next && norm(next.innerHTML) !== norm(el.innerHTML)) {
          el.innerHTML = next.innerHTML;
          document.dispatchEvent(new CustomEvent('bd:live-updated', { detail: { name: el.dataset.live } }));
        }
      });
    } catch (e) { /* offline: try again next tick */ }
    finally { busy = false; }
  }

  window.BDLive = { refresh };
  setInterval(refresh, INTERVAL_MS);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
})();