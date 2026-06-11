---
name: openlayers-navigation
description: OpenLayers map navigation — pan, zoom, and rotate. Use when panning (dragging) the map, zooming in/out via scroll wheel or zoom controls, or rotating the map view.
---

# OpenLayers Navigation Skill

This skill covers programmatic pan, zoom, and rotation for OpenLayers maps via Chrome DevTools.

## Pan (Drag the Map)

Panning requires a drag sequence on the canvas: `pointerdown` → `pointermove` (several steps) → `pointerup`. Sending multiple intermediate `pointermove` events produces smoother, more reliable panning.

```javascript
async function panMap(fromX, fromY, toX, toY) {
  const canvas = document.querySelector('.ol-viewport canvas');
  const rect = canvas.getBoundingClientRect();

  const fromClientX = rect.left + rect.width * fromX;
  const fromClientY = rect.top + rect.height * fromY;
  const toClientX = rect.left + rect.width * toX;
  const toClientY = rect.top + rect.height * toY;

  const base = {
    view: window, bubbles: true, cancelable: true,
    button: 0, buttons: 1,
    pointerId: 1, pointerType: 'mouse', isPrimary: true
  };

  // Start drag
  canvas.dispatchEvent(new PointerEvent('pointermove', { ...base, clientX: fromClientX, clientY: fromClientY, buttons: 0 }));
  canvas.dispatchEvent(new PointerEvent('pointerdown', { ...base, clientX: fromClientX, clientY: fromClientY }));
  await new Promise(r => setTimeout(r, 25));

  // Intermediate moves (more steps = smoother pan)
  const steps = 5;
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const cx = fromClientX + (toClientX - fromClientX) * t;
    const cy = fromClientY + (toClientY - fromClientY) * t;
    canvas.dispatchEvent(new PointerEvent('pointermove', { ...base, clientX: cx, clientY: cy }));
    await new Promise(r => setTimeout(r, 25));
  }

  // End drag
  canvas.dispatchEvent(new PointerEvent('pointerup', { ...base, clientX: toClientX, clientY: toClientY, buttons: 0 }));
}

// Example: pan from centre-right toward centre-left
await panMap(0.7, 0.5, 0.3, 0.5);
```

**Parameters:** relative coordinates (0.0–1.0) on the canvas. Dragging from `(0.7, 0.5)` to `(0.3, 0.5)` moves the map to the right (the viewport shifts left).

---

## Zoom via Scroll Wheel

OpenLayers listens for `wheel` events on the `.ol-viewport` element (not the canvas).

```javascript
async function zoomByWheel(centerX, centerY, deltaY) {
  // deltaY < 0  → zoom in   (e.g. -300)
  // deltaY > 0  → zoom out  (e.g. +300)
  const viewport = document.querySelector('.ol-viewport');
  const rect = viewport.getBoundingClientRect();

  const clientX = rect.left + rect.width * centerX;
  const clientY = rect.top + rect.height * centerY;

  viewport.dispatchEvent(new WheelEvent('wheel', {
    view: window,
    bubbles: true,
    cancelable: true,
    clientX,
    clientY,
    deltaY,
    deltaMode: 0   // DOM_DELTA_PIXEL
  }));

  // OL debounces zoom animations — wait for the animation to finish
  await new Promise(r => setTimeout(r, 400));
}

// Zoom in at map centre
await zoomByWheel(0.5, 0.5, -300);

// Zoom out at map centre
await zoomByWheel(0.5, 0.5, 300);
```

**Notes:**
- Dispatch on `.ol-viewport`, not on the canvas.
- Larger `|deltaY|` values produce more zoom steps per event.
- Wait ≥400 ms after each wheel event for the animation to settle before taking a screenshot or firing the next event.

---

## Zoom via OL Zoom Controls

If the map has the default zoom control buttons (`.ol-zoom`):

```javascript
async function clickZoomIn() {
  document.querySelector('.ol-zoom-in').click();
  await new Promise(r => setTimeout(r, 400));
}

async function clickZoomOut() {
  document.querySelector('.ol-zoom-out').click();
  await new Promise(r => setTimeout(r, 400));
}
```

## Rotate (Alt+Shift+Drag)

OpenLayers' `DragRotate` interaction fires on pointer drag with Alt+Shift held. The rotation is derived from the angle of the pointer relative to the map centre: moving the pointer clockwise around the centre rotates the map clockwise.

```javascript
async function rotateMap(angleDeg) {
  // angleDeg > 0: clockwise (north tilts right); < 0: counterclockwise
  const canvas = document.querySelector('.ol-viewport canvas');
  const rect = canvas.getBoundingClientRect();

  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;
  const radius = Math.min(rect.width, rect.height) * 0.3;

  const angleRad = angleDeg * Math.PI / 180;

  // Drag from theta=0 to theta=-angleRad around map centre.
  // OL computes theta = atan2(halfH - y, x - halfW) and applies -delta to rotation,
  // so a decrease of angleRad in theta adds +angleRad to the view rotation.
  const startTheta = 0;
  const endTheta = -angleRad;

  const base = {
    view: window, bubbles: true, cancelable: true,
    button: 0, buttons: 1,
    pointerId: 1, pointerType: 'mouse', isPrimary: true,
    altKey: true, shiftKey: true
  };

  const startX = centerX + radius * Math.cos(startTheta);
  const startY = centerY - radius * Math.sin(startTheta);

  canvas.dispatchEvent(new PointerEvent('pointermove', { ...base, clientX: startX, clientY: startY, buttons: 0 }));
  canvas.dispatchEvent(new PointerEvent('pointerdown', { ...base, clientX: startX, clientY: startY }));
  await new Promise(r => setTimeout(r, 25));

  const steps = 8;
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const theta = startTheta + (endTheta - startTheta) * t;
    const cx = centerX + radius * Math.cos(theta);
    const cy = centerY - radius * Math.sin(theta);
    canvas.dispatchEvent(new PointerEvent('pointermove', { ...base, clientX: cx, clientY: cy }));
    await new Promise(r => setTimeout(r, 25));
  }

  const endX = centerX + radius * Math.cos(endTheta);
  const endY = centerY - radius * Math.sin(endTheta);
  canvas.dispatchEvent(new PointerEvent('pointerup', { ...base, clientX: endX, clientY: endY, buttons: 0 }));
  await new Promise(r => setTimeout(r, 300));
}

// Rotate 45° clockwise
await rotateMap(45);

// Rotate 90° counterclockwise
await rotateMap(-90);
```

---

## Reset to North (Rotate Control)

If the map has the default Rotate control (`.ol-rotate`), clicking its button resets rotation to 0 with a short animation. The button has `ol-hidden` when rotation is 0, but clicking it still works.

```javascript
async function clickResetNorth() {
  document.querySelector('.ol-rotate button').click();
  await new Promise(r => setTimeout(r, 300));
}
```

---

## Coordinate Utilities

```javascript
const canvas = document.querySelector('.ol-viewport canvas');
const rect = canvas.getBoundingClientRect();

// Relative (0–1) → absolute pixel
const absX = rect.left + rect.width  * relX;
const absY = rect.top  + rect.height * relY;
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Pan does nothing** | Ensure no interaction (e.g. Draw) is active that captures drag events. Check that `buttons: 1` is set on all `pointermove` events during drag. |
| **Scroll zoom does nothing** | Dispatch on `.ol-viewport`, not on `canvas`. Confirm `deltaMode: 0`. |
| **Map snaps back after pan** | Increase the number of intermediate `pointermove` steps or the delay between them. |
| **Animation not complete before screenshot** | Wait ≥400 ms after a zoom or pan event. |
| **Canvas not found** | Try `document.querySelector('.ol-viewport canvas')` or `document.querySelector('canvas')`. |
| **Rotation does nothing** | Check that `DragRotate` interaction is active (it is by default). Ensure `altKey: true` and `shiftKey: true` on all events, and `pointerType: 'mouse'`. |
| **Reset north button missing** | The `.ol-rotate button` is hidden (`ol-hidden`) when rotation is 0. Click it anyway or add the Rotate control to the map first. |
