/* Resident report form: barangay-scoped road choices and current observation time. */
(function () {
  'use strict';

  const barangay = document.querySelector('[name="barangay_id"]');
  const roadSelect = document.getElementById('road-select');
  const customWrap = document.getElementById('custom-road-wrap');
  const customRoad = document.getElementById('custom-road');
  const observedAt = document.getElementById('observed-at');
  const form = document.getElementById('report-form');
  if (!form) return;

  // Keep options grouped by the selected barangay. “Other” permits a resident
  // to report a street that is not yet in the local list.
  const roadsByBarangay = {
    '1': ['A. Sandoval Avenue', 'M. Concepcion Avenue', 'Lopez Jaena Street'],
    '2': ['Lopez Jaena Street', 'Ilaya Street', 'F. Mariano Avenue'],
    '3': ['F. Mariano Avenue', 'Ilaya Street', 'M. Concepcion Avenue']
  };

  function updateRoads() {
    if (!roadSelect || !barangay) return;
    const previous = roadSelect.value;
    roadSelect.replaceChildren();
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Select a street / road';
    roadSelect.appendChild(placeholder);
    (roadsByBarangay[barangay.value] || []).forEach(function (name) {
      const option = document.createElement('option');
      option.value = name;
      option.textContent = name;
      roadSelect.appendChild(option);
    });
    const other = document.createElement('option');
    other.value = '__other__';
    other.textContent = 'Other — enter a specific street';
    roadSelect.appendChild(other);
    if ([...roadSelect.options].some(option => option.value === previous)) {
      roadSelect.value = previous;
    }
    updateCustomRoad();
  }

  function updateCustomRoad() {
    const isOther = roadSelect && roadSelect.value === '__other__';
    if (customWrap) customWrap.hidden = !isOther;
    if (customRoad) {
      customRoad.required = Boolean(isOther);
      if (!isOther) customRoad.value = '';
    }
  }

  function localDateTimeValue(date) {
    const pad = n => String(n).padStart(2, '0');
    return date.getFullYear() + '-' + pad(date.getMonth() + 1) + '-' + pad(date.getDate()) +
      'T' + pad(date.getHours()) + ':' + pad(date.getMinutes());
  }

  function updateObservationLimit() {
    if (!observedAt) return;
    const now = new Date();
    const nowValue = localDateTimeValue(now);
    observedAt.max = nowValue;
    // Observation timestamp is system-generated so residents cannot backdate it.
    observedAt.value = nowValue;
    observedAt.setCustomValidity('');
  }

  if (barangay && roadSelect) {
    barangay.addEventListener('change', updateRoads);
    roadSelect.addEventListener('change', updateCustomRoad);
    updateRoads();
  }

  if (observedAt) {
    updateObservationLimit();
    observedAt.addEventListener('input', updateObservationLimit);
    observedAt.addEventListener('change', updateObservationLimit);
  }

  form.addEventListener('submit', function (event) {
    updateObservationLimit();
    updateCustomRoad();
    if (observedAt && observedAt.value > localDateTimeValue(new Date())) {
      observedAt.setCustomValidity('Observation date and time cannot be in the future.');
      observedAt.reportValidity();
      event.preventDefault();
      return;
    }
    if (customRoad && customRoad.required && !customRoad.value.trim()) {
      customRoad.setCustomValidity('Enter the specific street or road.');
      customRoad.reportValidity();
      event.preventDefault();
    } else if (customRoad) {
      customRoad.setCustomValidity('');
    }
  });
})();
