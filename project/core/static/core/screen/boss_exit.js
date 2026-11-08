// Match the success signal used by zombie playback; failed retries do not erase a win.
export function markBossExitComplete(result, button) {
  if (!button || (result.passed ?? result.punched) !== true) return;
  // Keep the form's ordinary Exit endpoint; only the winning button finishes the run.
  if (button.dataset.completeUrl) button.setAttribute('formaction', button.dataset.completeUrl);
  button.classList.add('boss-exit--defeated');
  button.setAttribute('aria-label', 'Exit — zombie defeated');
}

export function installBossExitNavigation(button, cancelPendingRun) {
  if (!button?.form) return;
  const form = button.form;
  form.addEventListener('submit', event => {
    if (event.defaultPrevented) return;
    // Submit normally. Cancel pending responses without rewinding the visible scene.
    cancelPendingRun();
  });
}
