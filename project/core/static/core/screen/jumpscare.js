// Jumpscare in room 2 or 3: lunge 3s after entering, play the scare video, wait 1s, open the debug window.
const jumpscareElement = document.getElementById('screen-jumpscare');
const overlay = document.getElementById('jumpscare');
const video = document.getElementById('jumpscare-video');
const SCARE_DELAY_MS = 3000;
const DEBUG_DELAY_MS = 1000;

if (jumpscareElement && overlay && video) {
  const jumpscare = JSON.parse(jumpscareElement.textContent);

  video.addEventListener('ended', () => {
    // Hold the last frame, then hand off to exercise_popup.js.
    setTimeout(() => {
      overlay.hidden = true;
      document.dispatchEvent(new CustomEvent('jumpscare:debug', {detail: jumpscare.exercise}));
    }, DEBUG_DELAY_MS);
  }, {once: true});

  setTimeout(async () => {
    overlay.hidden = false;
    overlay.classList.add('lunge');
    try {
      await video.play();
    } catch {
      // Browsers can block autoplay with sound on a fresh page; play muted instead.
      video.muted = true;
      await video.play().catch(() => video.dispatchEvent(new Event('ended')));
    }
  }, SCARE_DELAY_MS);
}
