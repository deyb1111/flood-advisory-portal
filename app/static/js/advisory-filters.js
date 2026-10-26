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
    const cards = Array.from(grid.querySelectorAll('article[data-barangay]'));
    apply.addEventListener('click', () => {
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
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
