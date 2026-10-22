/* Personnel shell: CSRF passthrough + generic client-side form validation. */
(function () {
  'use strict';
  const csrfToken =
    document.querySelector('meta[name="csrf-token"]')?.content ||
    document.querySelector('input[name="csrf_token"]')?.value ||
    '';
  window.BDP = { csrfToken };

  document.querySelectorAll('form[data-bd-validate]').forEach((form) => {
    form.addEventListener('submit', (ev) => {
      let ok = true;
      form.querySelectorAll('[required]').forEach((el) => {
        const errId = el.getAttribute('aria-describedby');
        const errEl = errId ? document.getElementById(errId) : null;
        if (!el.value.trim()) {
          ok = false;
          el.classList.add('is-invalid');
          if (errEl) errEl.hidden = false;
        } else {
          el.classList.remove('is-invalid');
          if (errEl) errEl.hidden = true;
        }
      });
      if (!ok) ev.preventDefault();
    });
  });
})();