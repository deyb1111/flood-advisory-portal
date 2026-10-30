(() => {
  'use strict';
  function init() {
    const grid = document.getElementById('verifiedAdvisoryGrid');
    const apply = document.getElementById('applyAdvisoryFilters');
    if (!grid || !apply) return;
    const barangay = document.getElementById('advisoryBarangayFilter');
    const flood = document.getElementById('advisoryFloodFilter');
    const road = document.getElementById('advisoryRoadFilter');
    const count = document.getElementById('advisoryFilterCount');
    const empty = document.getElementById('noAdvisoriesMatch');
    apply.addEventListener('click', () => {
      const cards = Array.from(grid.querySelectorAll('article[data-barangay]'));
      const b = barangay.value, f = flood.value, r = road.value;
      let visible = 0;
      cards.forEach(card => {
        const match = (b === 'all' || card.dataset.barangay === b) &&
          (f === 'all' || card.dataset.flood === f) &&
          (r === 'all' || card.dataset.road === r);
        card.hidden = !match;
        if (match) visible++;
      });
      cards.sort((a, b) => Number(b.dataset.sort) - Number(a.dataset.sort)).forEach(card => grid.appendChild(card));
      count.textContent = `${visible} ${visible === 1 ? 'advisory' : 'advisories'} match your filters`;
      empty.hidden = visible !== 0;
    });
    [barangay, flood, road].forEach(select => select.addEventListener('change', () => apply.click()));
  }
  // Keep published advisories current without replacing the filter controls.
  async function refreshAdvisories() {
    if (document.hidden) return;
    try {
      const response = await fetch(location.href, {
        credentials: 'same-origin', cache: 'no-store',
        headers: { 'X-Requested-With': 'fetch' }
      });
      if (!response.ok || response.redirected) return;
      const doc = new DOMParser().parseFromString(await response.text(), 'text/html');
      const next = doc.getElementById('verifiedAdvisoryGrid');
      const current = document.getElementById('verifiedAdvisoryGrid');
      if (next && current && next.innerHTML !== current.innerHTML) {
        current.innerHTML = next.innerHTML;
        document.getElementById('applyAdvisoryFilters')?.click();
      }
    } catch (_) { /* retry next cycle */ }
  }
  window.setInterval(refreshAdvisories, 3000);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) refreshAdvisories();
  });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
