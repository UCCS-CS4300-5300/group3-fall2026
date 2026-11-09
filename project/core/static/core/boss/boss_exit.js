// =================================================================================
// Unlock the completion action after a verified win without erasing earlier success
// =================================================================================
export function markBossExitComplete(result, button) {
  if (!button) return;

  let completed = result.passed;
  if (completed === null || completed === undefined) completed = result.punched;
  if (completed !== true) return;
  // Keep the form's ordinary Exit endpoint; only the winning button finishes the run.
  if (button.dataset.completeUrl) button.setAttribute('formaction', button.dataset.completeUrl);
  button.classList.add('boss-exit--defeated');
  button.setAttribute('aria-label', 'Exit — zombie defeated');
}

// ===================================================================
// Cancel late program responses when the player submits the Exit form
// ===================================================================
export function installBossExitNavigation(button, cancelPendingRun) {
  if (!button || !button.form) return;
  const form = button.form;
  function cancelBeforeNavigation(event) {
    if (event.defaultPrevented) return;
    // Submit normally. Cancel pending responses without rewinding the visible scene.
    cancelPendingRun();
  }
  form.addEventListener('submit', cancelBeforeNavigation);
  return function removeExitListener() {
    form.removeEventListener('submit', cancelBeforeNavigation);
  };
}
