/* Interactive barangay summary filters for the public home page. */
document.addEventListener('DOMContentLoaded', function () {
  const filters = Array.from(document.querySelectorAll('[data-summary-filter]'));
  const status = document.querySelector('[data-summary-status]');
  const affectedRows = Array.from(document.querySelectorAll('.bd-affected-row[data-barangay]'));
  const advisories = Array.from(document.querySelectorAll('.bd-advisory-card[data-barangay]'));
  if (!filters.length) return;

  const names = { all: 'all three barangays', kalawaan: 'Kalawaan', 'san-joaquin': 'San Joaquin', bambang: 'Bambang' };
  function applyFilter(selected) {
    filters.forEach(function (button) {
      const active = button.dataset.summaryFilter === selected;
      button.classList.toggle('is-active', active);
      button.setAttribute('aria-pressed', active ? 'true' : 'false');
    });
    affectedRows.forEach(function (row) { row.hidden = selected !== 'all' && row.dataset.barangay !== selected; });
    advisories.forEach(function (card) { card.hidden = selected !== 'all' && card.dataset.barangay !== selected; });
    if (status) status.textContent = selected === 'all'
      ? 'Showing the combined summary for all three barangays.'
      : 'Showing affected roads and recent verified advisories for ' + names[selected] + '.';
  }
  filters.forEach(function (button) { button.addEventListener('click', function () { applyFilter(button.dataset.summaryFilter); }); });
});
