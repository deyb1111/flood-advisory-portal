/* Community upvote: submit in place, then let live-refresh.js re-sync the count. */
(function () {
  'use strict';
  document.addEventListener('submit', async function (e) {
    const form = e.target.closest('[data-upvote-form]');
    if (!form) return;
    e.preventDefault();
    const msg = document.querySelector('[data-upvote-msg]');
    const btn = form.querySelector('button');
    if (btn) btn.disabled = true;
    try {
      const res = await fetch(form.action, {
        method: 'POST', body: new FormData(form), credentials: 'same-origin',
        headers: { 'X-Requested-With': 'fetch' }
      });
      const data = await res.json();
      if (msg) msg.textContent = data.ok ? '' : (data.message || 'Could not save your confirmation.');
    } catch (err) {
      form.submit();   // network/JSON failure: fall back to a normal POST
      return;
    }
    if (window.BDLive) await window.BDLive.refresh();
    else location.reload();
  });
})();
