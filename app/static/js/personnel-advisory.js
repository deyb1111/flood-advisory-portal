/* Live preview + checklist + publish-modal mirroring. */
(function () {
  'use strict';
  const form = document.getElementById('advisory-form');
  if (!form) return;
  const $ = (id) => document.getElementById(id);

  const ROAD_LABELS = { passable: 'Passable', caution: 'Difficult to pass', not_passable: 'Not passable' };
  const ROAD_PILLS  = { passable: 'bd-pill--passable', caution: 'bd-pill--caution', not_passable: 'bd-pill--not-passable' };

  const preview = {
    title: document.querySelector('[data-preview-title]'),
    street: document.querySelector('[data-preview-street]'),
    message: document.querySelector('[data-preview-message]'),
    road: document.querySelector('[data-preview-road]'),
  };

  function sync() {
    const title = $('adv-title').value.trim();
    const message = $('adv-message').value.trim();
    const roadId = $('adv-road').value;
    const roadStatus = $('adv-status').value;
    const sourceReport = $('adv-source').value;
    const streetLabel = $('adv-road').selectedOptions[0]?.textContent || '';

    if (preview.title) preview.title.textContent = title || 'Advisory title';
    if (preview.street) preview.street.textContent = streetLabel || 'Choose a street';
    if (preview.message) preview.message.textContent = message || 'Add a description to complete this preview.';
    if (preview.road) {
      preview.road.textContent = ROAD_LABELS[roadStatus] || 'Not passable';
      preview.road.className = 'bd-pill ' + (ROAD_PILLS[roadStatus] || 'bd-pill--not-passable');
    }

    const checkSource = document.querySelector('[data-check-source]');
    if (checkSource) {
      const ok = !!sourceReport;
      checkSource.classList.toggle('is-done', ok);
      checkSource.classList.toggle('is-pending', !ok);
    }
    const checkRoad = document.querySelector('[data-check-road]');
    if (checkRoad) {
      checkRoad.classList.toggle('is-done', !!roadStatus);
      checkRoad.classList.toggle('is-pending', !roadStatus);
    }
  }

  ['input', 'change'].forEach(evt => form.addEventListener(evt, sync));
  sync();

  const publishModal = document.getElementById('publish-modal');
  if (publishModal) {
    publishModal.addEventListener('show.bs.modal', () => {
      const mirror = document.getElementById('publish-mirror');
      if (!mirror) return;
      mirror.innerHTML = '';
      ['title', 'message', 'road_id', 'report_id', 'road_status'].forEach(name => {
        const src = form.querySelector(`[name="${name}"]`);
        if (!src) return;
        const h = document.createElement('input');
        h.type = 'hidden'; h.name = name; h.value = src.value;
        mirror.appendChild(h);
      });
      const t = publishModal.querySelector('[data-preview-title]');
      if (t) t.textContent = $('adv-title').value || 'Advisory title';
      const s = publishModal.querySelector('[data-preview-street]');
      if (s) s.textContent = $('adv-road').selectedOptions[0]?.textContent || '';
      const m = publishModal.querySelector('[data-preview-message]');
      if (m) m.textContent = $('adv-message').value;
    });

    publishModal.querySelector('form')?.addEventListener('submit', (ev) => {
      const missing = [];
      if (!$('adv-title').value.trim()) missing.push('Title');
      if (!$('adv-message').value.trim()) missing.push('Description');
      if (!$('adv-source').value) missing.push('Verified source report');
      if (!$('adv-road').value) missing.push('Street');
      if (missing.length) {
        ev.preventDefault();
        alert('Please fill in: ' + missing.join(', '));
        publishModal.querySelector('.btn-close')?.click();
      }
    });
  }
})();