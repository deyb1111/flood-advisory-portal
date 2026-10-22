/* Sync review notes into verify modal + require reason on reject. */
(function () {
  'use strict';
  const notes = document.getElementById('review-notes');
  const verifyModal = document.getElementById('verify-modal');
  const hiddenNotes = document.getElementById('verify-notes-hidden');

  if (verifyModal && notes && hiddenNotes) {
    verifyModal.addEventListener('show.bs.modal', () => {
      hiddenNotes.value = notes.value;
    });
  }

  const rejectModal = document.getElementById('reject-modal');
  if (rejectModal) {
    const form = rejectModal.querySelector('form');
    const reason = rejectModal.querySelector('#rejection-reason');
    const err = rejectModal.querySelector('#rejection-reason-error');
    form.addEventListener('submit', (ev) => {
      if (!reason.value.trim()) {
        ev.preventDefault();
        reason.classList.add('is-invalid');
        if (err) err.hidden = false;
        reason.focus();
      }
    });
    rejectModal.addEventListener('hidden.bs.modal', () => {
      reason.classList.remove('is-invalid');
      if (err) err.hidden = true;
    });
  }
})();