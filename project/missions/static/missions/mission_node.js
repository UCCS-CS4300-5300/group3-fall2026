// Shows the success text and the next Left/Right choice once the map is solved.
// The prebuilt map bundle (core/map/dist/map_app.js) only reports its result
// through the #map-status text, so watch that element for its success message.
const SOLVED_TEXT = 'Solved!';

const status = document.getElementById('map-status');
const nextSteps = document.querySelectorAll('[data-reveal-on-solve]');

const observer = new MutationObserver(() => {
  if (status.textContent !== SOLVED_TEXT) return;
  observer.disconnect();
  nextSteps.forEach(el => { el.hidden = false; });
  nextSteps[0]?.scrollIntoView({behavior: 'smooth', block: 'nearest'});
});

observer.observe(status, {childList: true, characterData: true, subtree: true});
