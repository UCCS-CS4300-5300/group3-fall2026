/**
 * Coordinate room PNG movement: prepare floor/image data, preview an approach,
 * start a Run attempt, apply its result, reset, and clean up.
 * Functions below handle image rendering, Motion translation, Run state, and
 * coordinate projection. Lessons supply image settings; rooms supply geometry.
 */
import {animate} from 'motion';

// ============================================================================
// ROOM MOVEMENT COORDINATOR
// Load room/lesson data, wait for images, connect Preview and Run, and clean up.
// ============================================================================

/**
 * Connect room data, lesson image settings, translation, rendering, and Run actions.
 * Setup waits for images; Preview/Run start movement; results adjust speed/death;
 * reset/leave cancels the attempt; destroy releases image and floor listeners.
 */
export function initializeMovement(root = document) {
  const settings = JSON.parse(root.querySelector('#screen-movement-config')?.textContent ?? '{}');
  if (!settings.enabled) return createDefaultMovement();
  // These elements belong to the room preview, not to Blockly or learner Run.
  const background = root.querySelector('.room-background');
  const sprite = root.querySelector('#png-move-sprite');
  const startButton = root.querySelector('#png-preview');
  const resetButton = root.querySelector('#png-preview-reset');
  const status = root.querySelector('#png-preview-status');
  const data = root.querySelector('#screen-floor-config');

  // Roomless and ordinary pages use the same controller API without images.
  if (!background || !sprite || !startButton || !resetButton || !status || !data) {
    return createDefaultMovement();
  }

  const floor = JSON.parse(data.textContent);
  const cleanupFloor = initializeFloor(root, floor);
  // Retain elapsed time separately so a resize redraws the current pose instead
  // of restarting the approach. ready prevents drawing before both images load.
  let elapsed = 0;
  let ready = false;
  let rotation = 0;
  const readinessListeners = new Set();

  function redraw() {
    if (ready) renderSprite(background, sprite, floor, elapsed, rotation);
  }

  // The clock handles frame scheduling and endpoint hold. This callback only
  // renders its current pose and describes the preview state beside the controls.
  const translation = createTranslation(floor.motion.duration_ms, (time, state) => {
    elapsed = time;
    rotation = state === 'dead' ? settings.death_rotation_degrees : 0;
    redraw();
    if (!ready) return;

    const messages = {
      idle: 'Ready to preview.',
      approaching: 'Approaching…',
      stopped: 'Endpoint reached. Preview again to replay.',
      dead: 'Defeated!'
    };

    // Avoid rewriting the live region on every frame.
    if (status.textContent !== messages[state]) status.textContent = messages[state];
  }, settings);
  const runAttempt = createRunAttempt(translation, () => { sprite.hidden = true; }, settings.normal_speed);
  const previewStart = () => runAttempt.start();
  const previewReset = () => runAttempt.reset();

  function notifyReadiness() {
    readinessListeners.forEach(listener => listener(ready));
  }

  function checkImages() {
    // complete also becomes true after a failed load; naturalWidth distinguishes
    // a usable image. Both images are needed for scale and aspect-ratio calculations.
    ready = [background, sprite].every(image => image.complete && image.naturalWidth > 0);
    startButton.disabled = !ready;
    resetButton.disabled = !ready;

    if (ready) runAttempt.reset();
    notifyReadiness();
  }

  function showLoadError() {
    // Cancel pending motion before hiding the sprite and offering a retry.
    ready = false;
    runAttempt.reset();
    sprite.hidden = true;
    startButton.disabled = true;
    resetButton.disabled = true;
    status.textContent = 'Preview image could not load. Reload the page to retry.';
    notifyReadiness();
  }

  function followVisibility() {
    // Hidden-tab time counts toward neither movement nor minimum visible time.
    if (document.hidden) translation.pause();
    else translation.resume();
  }

  const observer = new ResizeObserver(redraw);

  // Observe the background itself: opening Tutorials can resize it without a
  // window resize. These listeners only manage the room's visual state.
  observer.observe(background);
  startButton.addEventListener('click', previewStart);
  resetButton.addEventListener('click', previewReset);
  document.addEventListener('visibilitychange', followVisibility);
  window.addEventListener('pagehide', previewReset);

  // Register load listeners before the immediate check, covering both cached
  // images and downloads that finish after this module starts.
  for (const image of [background, sprite]) {
    image.addEventListener('load', checkImages);
    image.addEventListener('error', showLoadError);
  }

  checkImages();
  followVisibility();

  // Cached failures may have dispatched their error event before setup began.
  if ([background, sprite].some(image => image.complete && !image.naturalWidth)) {
    showLoadError();
  }

  function destroy() {
    // Release the translation, observer, and every listener if the room is removed
    // without a full page navigation. Keep cleanup paired with setup.
    runAttempt.reset();
    cleanupFloor();
    observer.disconnect();
    startButton.removeEventListener('click', previewStart);
    resetButton.removeEventListener('click', previewReset);
    document.removeEventListener('visibilitychange', followVisibility);
    window.removeEventListener('pagehide', previewReset);

    for (const image of [background, sprite]) {
      image.removeEventListener('load', checkImages);
      image.removeEventListener('error', showLoadError);
    }
    readinessListeners.clear();
  }

  return {
    ...runAttempt,
    isReady: () => ready,
    onReady(listener) {
      readinessListeners.add(listener);
      listener(ready);
      return () => readinessListeners.delete(listener);
    },
    destroy
  };
}

// ============================================================================
// SPRITE RENDERING
// Put the picture on the plane: foot anchor, position, size, and death rotation.
// ============================================================================

function renderSprite(background, sprite, floor, elapsedMs, rotationDegrees = 0) {
  // This is the background element's visible box, which may crop the source image.
  const {width, height} = background.getBoundingClientRect();

  // A temporarily hidden/collapsed room has no drawable area. ResizeObserver
  // will try again when the layout gives the background a size.
  if (!width || !height) return;

  const transform = coverTransform(
    background.naturalWidth, background.naturalHeight, width, height
  );
  // The pose uses original-image fractions; cover mapping converts its feet to
  // visible pixels, including any cropped margins around the room background.
  const pose = getTranslationPose(floor, elapsedMs);
  const [footX, footY] = imageToDisplay(pose.feet, transform);

  // Height is relative to the room image. Derive width from the photo's own
  // aspect ratio so the cat cannot stretch when the room changes shape.
  const spriteHeight = pose.height * transform.height;
  const [anchorX, anchorY] = floor.motion.foot_anchor;

  // Keep a natural-size bitmap and transform it uniformly around its foot anchor.
  const scale = spriteHeight / sprite.naturalHeight;
  // The selected paw/foot anchor need not lie on the photo's bottom edge.
  const anchorPixelsX = anchorX * sprite.naturalWidth;
  const anchorPixelsY = anchorY * sprite.naturalHeight;

  sprite.style.width = `${sprite.naturalWidth}px`;
  sprite.style.height = `${sprite.naturalHeight}px`;
  sprite.style.transformOrigin = '0 0';
  // Move the bitmap's foot to the origin, scale and rotate there, then put that
  // origin on the path. Rotation cannot lift or slide the contact point.
  sprite.style.transform = `translate(${footX}px, ${footY}px) rotate(${rotationDegrees}deg) `
    + `scale(${scale}) translate(${-anchorPixelsX}px, ${-anchorPixelsY}px)`;
  sprite.hidden = false;
}

// ============================================================================
// APPROACH TRANSLATION
// Calculate the current pose; start, reset, change speed, pause, resume, and die.
// ============================================================================

/**
 * Evaluate a server-validated approach at elapsed milliseconds, clamped to its ends.
 * Returns normalized image feet, height as a fraction of background height, and
 * progress in [0, 1]. The inverse-depth size models a screen-facing billboard.
 */
export function getTranslationPose(floor, elapsedMs) {
  const motion = floor.motion;
  const progress = Math.min(1, Math.max(0, elapsedMs / motion.duration_ms));
  const floorPoint = motion.start_floor.map((start, axis) => (
    start + (motion.end_floor[axis] - start) * progress
  ));
  const [g, h, i] = floor.matrix.slice(6);
  const depth = g * floorPoint[0] + h * floorPoint[1] + i;

  return {
    feet: projectPoint(floor.matrix, floorPoint),
    height: motion.end_height * motion.end_depth / depth,
    progress
  };
}

/**
 * Control approach playback using Motion's translation controls.
 * Supports start, reset, pause/resume, speed changes, and delayed death.
 * render receives motion elapsed milliseconds and idle/approaching/stopped/dead.
 * Movement time follows zombie speed; minimum visible time runs independently.
 * Motion owns frame scheduling, interpolation, playback rate, and pause/resume.
 */
export function createTranslation(durationMs, render, settings = {}) {
  const normalSpeed = settings.normal_speed ?? 10;
  const minimumVisible = settings.minimum_visible_ms ?? 0;
  let elapsed = 0;
  let state = 'idle';
  let paused = false;
  let deathRequested = false;
  let visibleEnough = minimumVisible === 0;
  let approach;
  let visibility;
  let generation = 0;

  const draw = () => render(elapsed, state);

  function finishDeath() {
    approach?.pause();
    visibility?.pause();
    state = 'dead';
    draw();
  }

  function setSpeed(value) {
    const speed = Number.isFinite(value) ? value : normalSpeed;
    if (approach) approach.speed = Math.min(settings.speed_max ?? 20,
      Math.max(settings.speed_min ?? 1, speed)) / normalSpeed;
  }

  function start(initialSpeed = normalSpeed) {
    const currentGeneration = ++generation;
    approach?.stop();
    visibility?.stop();
    elapsed = 0;
    deathRequested = false;
    visibleEnough = minimumVisible === 0;
    state = 'approaching';

    // Interpolate movement time directly; the shared renderer still projects the pose.
    approach = animate(0, durationMs, {
      duration: durationMs / 1000,
      ease: 'linear',
      autoplay: false,
      onUpdate(value) {
        if (currentGeneration !== generation) return;
        elapsed = value;
        draw();
      },
      onComplete() {
        if (currentGeneration !== generation || state !== 'approaching') return;
        state = 'stopped';
        draw();
      }
    });

    // Independent real-time timer: changing approach speed cannot shorten it.
    visibility = visibleEnough ? undefined : animate(0, 1, {
      duration: minimumVisible / 1000,
      ease: 'linear',
      autoplay: false,
      onComplete() {
        if (currentGeneration !== generation) return;
        visibleEnough = true;
        if (deathRequested) finishDeath();
      }
    });
    setSpeed(initialSpeed);
    draw();
    if (!paused) {
      approach.play();
      visibility?.play();
    }
  }

  function reset() {
    // Motion may already have queued a completion promise before stop is called.
    generation += 1;
    approach?.stop();
    visibility?.stop();
    approach = visibility = undefined;
    elapsed = 0;
    deathRequested = false;
    visibleEnough = minimumVisible === 0;
    state = 'idle';
    draw();
  }

  function pause() {
    paused = true;
    approach?.pause();
    visibility?.pause();
  }

  function resume() {
    if (!paused) return;
    paused = false;
    if (state === 'idle' || state === 'dead') return;
    if (state === 'approaching') approach?.play();
    if (!visibleEnough) visibility?.play();
  }

  function die() {
    if (state === 'idle' || state === 'dead') return;
    deathRequested = true;
    if (visibleEnough) finishDeath();
  }

  return {start, reset, pause, resume, setSpeed, die};
}

// ============================================================================
// RUN ATTEMPTS AND RESULTS
// Associate movement with the current Run; apply its result and ignore old ones.
// ============================================================================

/**
 * Associate local movement with Run attempts. Older results cannot change a new
 * attempt or a reset. The injected translation also powers the independent preview.
 */
export function createRunAttempt(translation, hide, normalSpeed = 10) {
  let attempt = 0;

  function reset() {
    attempt += 1;
    translation.reset();
  }

  function start(speed = normalSpeed) {
    reset();
    translation.start(speed);
    return attempt;
  }

  function applyResult(token, result) {
    if (token !== attempt) return;

    if (Number.isFinite(result.variables?.zombie_speed)) translation.setSpeed(result.variables.zombie_speed);
    if (result.passed ?? result.punched) translation.die();
  }

  function fail(token) {
    if (token !== attempt) return;

    reset();
    hide();
  }

  return {start, reset, applyResult, fail};
}

// ============================================================================
// DEFAULT MOVEMENT FOR ORDINARY ROOMS
// Provide the same ready controller interface when movement is disabled.
// ============================================================================

export function createDefaultMovement() {
  const noop = () => {};
  return {
    start: noop, reset: noop, applyResult: noop, fail: noop, destroy: noop,
    isReady: () => true,
    onReady(listener) { listener(true); return noop; }
  };
}

// ============================================================================
// FLOOR PROJECTION AND OVERLAY
// Map plane/image/display coordinates; draw the grid/path and align on resize.
// ============================================================================

/**
 * Project a 2D point using a prepared, row-major 3x3 matrix.
 * Python's matrix maps floor units to normalized original-image coordinates;
 * its inverse maps image coordinates back to floor units.
 * Returns [x, y] in the destination space; throws near a projection singularity.
 */
export function projectPoint(matrix, [x, y]) {
  const [a, b, c, d, e, f, g, h, i] = matrix;
  const w = g * x + h * y + i;

  if (Math.abs(w) <= 1e-9 * (Math.abs(g * x) + Math.abs(h * y) + Math.abs(i))) {
    throw new Error('Point lies on a projection singularity.');
  }

  return [(a * x + b * y + c) / w, (d * x + e * y + f) / w];
}

/**
 * Calculate centered cover scaling from natural image pixels to CSS pixels.
 * width/height describe the image element's displayed box, independently of Blockly.
 * Returns scaled image dimensions and crop offsets, all in CSS pixels.
 * Throws when any dimension is nonfinite or nonpositive.
 */
export function coverTransform(imageWidth, imageHeight, width, height) {
  if (![imageWidth, imageHeight, width, height].every(v => Number.isFinite(v) && v > 0)) {
    throw new Error('Image and container dimensions must be positive.');
  }

  const scale = Math.max(width / imageWidth, height / imageHeight);

  return {
    width: imageWidth * scale,
    height: imageHeight * scale,
    offsetX: (width - imageWidth * scale) / 2,
    offsetY: (height - imageHeight * scale) / 2
  };
}

/**
 * Map normalized original-image [x, y] to CSS-pixel [x, y] in the image box.
 * Requires a valid coverTransform result; cropped points may lie outside the box.
 */
export function imageToDisplay([x, y], transform) {
  return [
    transform.offsetX + x * transform.width,
    transform.offsetY + y * transform.height
  ];
}

/**
 * Map CSS-pixel [x, y] relative to the image box to normalized image coordinates.
 * Requires a valid coverTransform result; returns unclamped [x, y].
 */
export function displayToImage([x, y], transform) {
  return [
    (x - transform.offsetX) / transform.width,
    (y - transform.offsetY) / transform.height
  ];
}

// Project a unit-square grid using the same mapping as the floor outline.
function createFloorShapes(position, motion) {
  const namespace = 'http://www.w3.org/2000/svg';
  const floorCorners = [[0, 0], [1, 0], [1, 1], [0, 1]];
  const polygon = document.createElementNS(namespace, 'polygon');

  polygon.setAttribute('points', floorCorners.map(position).join(' '));
  polygon.setAttribute('class', 'png-floor-outline');

  const grid = document.createElementNS(namespace, 'path');
  const segments = [];

  for (let step = 1; step < 10; step++) {
    const floorFraction = step / 10;

    segments.push(
      `M${position([floorFraction, 0])} L${position([floorFraction, 1])}`,
      `M${position([0, floorFraction])} L${position([1, floorFraction])}`
    );
  }

  grid.setAttribute('d', segments.join(' '));
  grid.setAttribute('class', 'png-floor-grid');

  const shapes = [polygon, grid];

  if (motion) {
    const path = document.createElementNS(namespace, 'path');

    path.setAttribute('d', `M${position(motion.start_floor)} L${position(motion.end_floor)}`);
    path.setAttribute('class', 'png-floor-path');
    shapes.push(path);
  }

  return shapes;
}

/**
 * Initialize the floor within a document or element containing the room layers.
 * Draws prepared room geometry and follows the background image's load and size.
 * Returns cleanup; absent room layers return a no-op. Invalid JSON throws.
 */
function initializeFloor(root, floor) {
  const image = root.querySelector('.room-background');
  const svg = root.querySelector('#png-move-floor');
  if (!image || !svg || !floor) return () => {};

  function draw() {
    const {width, height} = image.getBoundingClientRect();

    if (!image.naturalWidth || !image.naturalHeight || !width || !height) return;

    const transform = coverTransform(image.naturalWidth, image.naturalHeight, width, height);

    function position(floorPoint) {
      const imagePoint = projectPoint(floor.matrix, floorPoint);

      return imageToDisplay(imagePoint, transform).join(',');
    }

    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.replaceChildren(...createFloorShapes(position, floor.motion));
  }

  const observer = new ResizeObserver(draw);

  observer.observe(image);
  image.addEventListener('load', draw);
  draw();

  return () => {
    observer.disconnect();
    image.removeEventListener('load', draw);
  };
}
