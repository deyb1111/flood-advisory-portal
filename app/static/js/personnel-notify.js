/* Personnel + resident notifications (new reports / community confirmations): polls unread count, shows a toast for
   newly arrived items, and triggers an immediate live-region refresh. */
(function () {
  'use strict';
  const bell = document.getElementById('bd-notif');
  if (!bell) return;
  const badge = document.getElementById('bd-notif-badge');
  const toasts = document.getElementById('bd-toasts');
  const meta = document.querySelector('meta[name="csrf-token"]');
  const token = (window.BDP && window.BDP.csrfToken) || (meta && meta.content) || '';
  let lastId = null;   // highest notification id already shown

  function toast(n) {
    const a = document.createElement('a');
    a.className = 'bd-toast';
    a.href = n.url || ('/personnel/reports/' + n.report_id);   // server supplies the role-correct link
    a.textContent = n.message;           // textContent: message is user-influenced
    toasts.appendChild(a);
    setTimeout(() => a.remove(), 8000);
  }

  async function poll() {
    try {
      const res = await fetch(bell.dataset.api, { credentials: 'same-origin' });
      if (!res.ok) return;
      const data = await res.json();
      badge.textContent = data.unread > 99 ? '99+' : data.unread;
      badge.hidden = !data.unread;

      const maxId = data.items.reduce((m, n) => Math.max(m, n.id), 0);
      if (lastId !== null && maxId > lastId) {
        data.items.filter(n => n.id > lastId && !n.is_read).reverse().forEach(toast);
        if (window.BDLive) window.BDLive.refresh();   // update stats/list now
      }
      lastId = Math.max(lastId || 0, maxId);
    } catch (e) { /* retry next tick */ }
  }

  bell.addEventListener('click', () => {
    fetch(bell.dataset.readApi, { method: 'POST', credentials: 'same-origin',
                                  headers: { 'X-CSRFToken': token }, keepalive: true });
  });

  poll();
  setInterval(poll, 10000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) poll(); });
})();
