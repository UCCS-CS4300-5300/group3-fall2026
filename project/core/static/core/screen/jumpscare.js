// Jumpscare in room 2 or 3: lunge 3s after entering, play the scare video, wait 1s, open the debug window.
// Solving the debug plays the zombie's defeat video.
const jumpscareElement = document.getElementById('screen-jumpscare');
const overlay = document.getElementById('jumpscare');
const video = document.getElementById('jumpscare-video');
const canvas = document.getElementById('jumpscare-canvas');
const SCARE_DELAY_MS = 3000;
const DEBUG_DELAY_MS = 1000;
// "Magenta amount" is how much more red and blue than green a pixel has.
// Pixels fade out between KEY_START and KEY_END; the videos' backgrounds score about 95-130.
const KEY_START = 25;
const KEY_END = 55;
// Used until a frame's corner shows the real background colour.
let background = [238, 72, 185];

function magentaAmount(red, green, blue) {
  return Math.min(red, blue) - green;
}

// Make the videos' magenta background transparent, so the zombie lunges over the room.
function removeMagenta(context) {
  const frame = context.getImageData(0, 0, canvas.width, canvas.height);
  const pixels = frame.data;
  const corner = [pixels[0], pixels[1], pixels[2]];
  if (magentaAmount(...corner) >= KEY_END) background = corner;
  const backgroundMagenta = magentaAmount(...background);

  for (let i = 0; i < pixels.length; i += 4) {
    const magenta = magentaAmount(pixels[i], pixels[i + 1], pixels[i + 2]);
    if (magenta <= 0) continue;
    if (magenta >= KEY_END) {
      pixels[i + 3] = 0;
      continue;
    }
    // Edge pixels are a blend of zombie and background; take the background's share out of the colour.
    const zombieShare = Math.max(1 - magenta / backgroundMagenta, 0.1);
    for (let channel = 0; channel < 3; channel++) {
      pixels[i + channel] = (pixels[i + channel] - (1 - zombieShare) * background[channel]) / zombieShare;
    }
    if (magenta > KEY_START) pixels[i + 3] = 255 * (KEY_END - magenta) / (KEY_END - KEY_START);
  }
  context.putImageData(frame, 0, 0);
}

function drawFrames() {
  const context = canvas.getContext('2d', {willReadFrequently: true});
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  // Draw once per new video frame where the browser supports it.
  const nextFrame = video.requestVideoFrameCallback
    ? (callback) => video.requestVideoFrameCallback(callback)
    : (callback) => requestAnimationFrame(callback);
  const draw = () => {
    context.drawImage(video, 0, 0);
    try {
      removeMagenta(context);
    } catch {
      // The browser won't let pages read this video's pixels; show the video as it is.
      overlay.classList.add('no-key');
      return;
    }
    if (!video.paused && !video.ended) nextFrame(draw);
  };
  draw();
}

if (jumpscareElement && overlay && video && canvas) {
  const jumpscare = JSON.parse(jumpscareElement.textContent);

  // Runs for both the scare and the defeat video.
  video.addEventListener('playing', drawFrames);
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

  // exercise_popup.js sends this when the player solves the debug exercise.
  document.addEventListener('jumpscare:defeated', async () => {
    if (!jumpscare.defeat_video) return;
    video.src = jumpscare.defeat_video;
    video.muted = false;                  // the player just clicked Run, so sound is allowed now
    overlay.classList.remove('lunge');    // the zombie dies where it stands instead of lunging again
    overlay.hidden = false;
    video.addEventListener('ended', () => { overlay.hidden = true; }, {once: true});
    await video.play().catch(() => { overlay.hidden = true; });
  });
}