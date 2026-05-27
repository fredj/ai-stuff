---
name: openlayers-interaction
description: OpenLayers map interaction patterns and automation. Use when interacting with OpenLayers maps (ol-viewport, canvas elements), simulating clicks/draws on maps, drawing/modifying geometries, dragging vertices/edges, deleting vertices, or automating map features programmatically.
---

# OpenLayers Interaction Skill

This skill provides guidance for interacting with OpenLayers maps programmatically through Chrome DevTools.

## Overview

When automating interactions with OpenLayers maps, you need to dispatch proper pointer events to canvas elements since standard click automation often doesn't work with canvas-based map rendering.

## Key Concepts

### Map Structure

OpenLayers maps typically have this DOM structure:
- `.ol-viewport` - the main viewport container
- `canvas` elements - where the map is rendered
- `.ol-overlay` - overlay elements (popups, tooltips, etc.)

### Event Requirements

OpenLayers requires proper pointer events with specific properties to register user interactions. Mouse events alone may not work reliably.

## Simulating Map Clicks

### Use Pointer Events Only

When simulating clicks on an OpenLayers map, use **only PointerEvent types**, not MouseEvent:

```javascript
function simulatePointerClick(element, clientX, clientY) {
  const eventInit = {
    view: window,
    bubbles: true,
    cancelable: true,
    clientX: clientX,
    clientY: clientY,
    button: 0,
    buttons: 1,
    pointerId: 1,
    pointerType: 'mouse',
    isPrimary: true
  };

  // Dispatch pointer events in sequence
  element.dispatchEvent(new PointerEvent('pointerenter', eventInit));
  element.dispatchEvent(new PointerEvent('pointerover', eventInit));
  element.dispatchEvent(new PointerEvent('pointermove', eventInit));
  element.dispatchEvent(new PointerEvent('pointerdown', { ...eventInit, buttons: 1 }));
  element.dispatchEvent(new PointerEvent('pointerup', { ...eventInit, buttons: 0 }));
  element.dispatchEvent(new PointerEvent('click', eventInit));
}
```

#### Event Sequence & Properties

Click sequence: `pointerenter` → `pointerover` → `pointermove` → `pointerdown` (buttons: 1) → `pointerup` (buttons: 0) → `click`

Required properties: `view: window`, `bubbles: true`, `cancelable: true`, `clientX`, `clientY`, `button: 0`, `buttons` (1 or 0), `pointerId: 1`, `pointerType: 'mouse'`, `isPrimary: true`

## Drawing Multi-Point Geometries

### Drawing LineStrings and Polygons

**Finish by clicking the last point again** (within snapTolerance, default 12px):

- **LineString:** Click the last point again to finish
- **Polygon:** Click the second-to-last point to close the ring (creates closing edge back to first point)

#### Delay Strategy

OpenLayers uses a **250ms double-click detection window**. When clicks occur faster than 250ms apart, they interfere with the drawing interaction's click handling. To prevent drawing failures:
- Use **250ms or greater delay between ALL clicks** (including clicks at different locations)
- Use **300ms delay for finishing by clicking the same location twice** (provides safety margin above threshold)
- Use **25ms delay for internal operations** (pointermove sequences, event dispatching within drag operations, etc.)

**Critical Note:** Delays less than 250ms between any clicks will cause drawing to fail entirely.

```javascript
async function drawLineString(points) {
  const canvas = document.querySelector('.ol-viewport canvas');
  const rect = canvas.getBoundingClientRect();

  // Click all points with 250ms delay between clicks (prevents drawing failure)
  for (let i = 0; i < points.length; i++) {
    const clientX = rect.left + rect.width * points[i].x;
    const clientY = rect.top + rect.height * points[i].y;
    simulatePointerClick(canvas, clientX, clientY);
    // 250ms minimum to avoid interfering with OpenLayers double-click detection
    if (i < points.length - 1) {
      await new Promise(resolve => setTimeout(resolve, 250));
    }
  }

  // Finish: click same point again - use 300ms delay to ensure clear separation
  await new Promise(resolve => setTimeout(resolve, 300));
  const lastX = rect.left + rect.width * points[points.length - 1].x;
  const lastY = rect.top + rect.height * points[points.length - 1].y;
  simulatePointerClick(canvas, lastX, lastY);
}

// Example: Draw a LineString with 3 points
await drawLineString([
  { x: 0.3, y: 0.4 },
  { x: 0.7, y: 0.6 },
  { x: 0.5, y: 0.8 }
]);
```

For Polygon, use the same approach but click the **second-to-last point** instead to finish.

### Coordinate Calculation

Convert relative position (0.0 to 1.0) to absolute coordinates:

```javascript
const canvas = document.querySelector('.ol-viewport canvas');
const rect = canvas.getBoundingClientRect();
const absoluteX = rect.left + rect.width * relativeX;
const absoluteY = rect.top + rect.height * relativeY;
```

## Modifying Features

### Dragging Vertices

To drag a vertex: pointerdown → pointermove (multiple times, buttons: 1) → pointerup.

```javascript
async function dragVertex(fromX, fromY, toX, toY) {
  const canvas = document.querySelector('.ol-viewport canvas');
  const rect = canvas.getBoundingClientRect();
  const fromClientX = rect.left + rect.width * fromX;
  const fromClientY = rect.top + rect.height * fromY;
  const toClientX = rect.left + rect.width * toX;
  const toClientY = rect.top + rect.height * toY;

  // Start drag
  const downEvent = {
    view: window, bubbles: true, cancelable: true,
    clientX: fromClientX, clientY: fromClientY, button: 0, buttons: 1,
    pointerId: 1, pointerType: 'mouse', isPrimary: true
  };
  canvas.dispatchEvent(new PointerEvent('pointerdown', downEvent));
  await new Promise(resolve => setTimeout(resolve, 25));

  // During drag, send multiple pointermove events with buttons: 1
  const moveEvent = { ...downEvent, clientX: toClientX, clientY: toClientY, buttons: 1 };
  canvas.dispatchEvent(new PointerEvent('pointermove', moveEvent));
  await new Promise(resolve => setTimeout(resolve, 25));

  // End drag
  const upEvent = { ...moveEvent, buttons: 0 };
  canvas.dispatchEvent(new PointerEvent('pointerup', upEvent));
}
// Example: await dragVertex(0.7, 0.3, 0.5, 0.3);
```

### Dragging Edges (Create New Vertices)

Drag an edge between two vertices to create a new vertex at that location. Same mechanism as vertex dragging.

```javascript
async function dragEdge(edgeStartX, edgeStartY, edgeEndX, edgeEndY, dragToX, dragToY) {
  const canvas = document.querySelector('.ol-viewport canvas');
  const rect = canvas.getBoundingClientRect();

  // Click midpoint of edge to start drag
  const midX = (edgeStartX + edgeEndX) / 2;
  const midY = (edgeStartY + edgeEndY) / 2;
  const midClientX = rect.left + rect.width * midX;
  const midClientY = rect.top + rect.height * midY;

  const downEvent = {
    view: window, bubbles: true, cancelable: true,
    clientX: midClientX, clientY: midClientY, button: 0, buttons: 1,
    pointerId: 1, pointerType: 'mouse', isPrimary: true
  };
  canvas.dispatchEvent(new PointerEvent('pointerdown', downEvent));
  await new Promise(resolve => setTimeout(resolve, 25));

  // Drag to new position (buttons: 1)
  const dragClientX = rect.left + rect.width * dragToX;
  const dragClientY = rect.top + rect.height * dragToY;
  const moveEvent = { ...downEvent, clientX: dragClientX, clientY: dragClientY, buttons: 1 };
  canvas.dispatchEvent(new PointerEvent('pointermove', moveEvent));
  await new Promise(resolve => setTimeout(resolve, 25));

  // End drag
  const upEvent = { ...moveEvent, buttons: 0 };
  canvas.dispatchEvent(new PointerEvent('pointerup', upEvent));
}
// Example: drag edge between (0.3, 0.3) and (0.7, 0.3) to position (0.5, 0.5)
// await dragEdge(0.3, 0.3, 0.7, 0.3, 0.5, 0.5);
```

**Note:** Dragging an edge creates a new vertex at the drag location. Ensure Modify interaction is active.

### Deleting Vertices

The `deleteCondition` option controls when vertices are deleted. **By default:** Alt+SingleClick on a vertex deletes it.

The `deleteCondition` is **configurable** and can be set to any custom function. Example with default behavior:
```javascript
async function deleteVertex(vertexX, vertexY) {
  const canvas = document.querySelector('.ol-viewport canvas');
  const rect = canvas.getBoundingClientRect();
  const clientX = rect.left + rect.width * vertexX;
  const clientY = rect.top + rect.height * vertexY;

  // Default deleteCondition: Alt+SingleClick
  const clickEvent = {
    view: window, bubbles: true, cancelable: true,
    clientX: clientX, clientY: clientY, button: 0, buttons: 0,
    altKey: true,
    pointerId: 1, pointerType: 'mouse', isPrimary: true
  };

  canvas.dispatchEvent(new PointerEvent('pointerdown', clickEvent));
  await new Promise(resolve => setTimeout(resolve, 25));
  canvas.dispatchEvent(new PointerEvent('pointerup', clickEvent));
  await new Promise(resolve => setTimeout(resolve, 25));
  canvas.dispatchEvent(new PointerEvent('click', clickEvent));
}
// Example: await deleteVertex(0.5, 0.3);
```

**Note:** `deleteCondition` can be customized when creating the Modify interaction. Check OpenLayers docs for custom condition functions.

**Constraints:** LineString requires ≥2 vertices, Polygon requires ≥3 vertices (≥4 coordinates including closing point). Deletion is blocked below these minimums.

## Map Elements & Utilities

```javascript
const canvas = document.querySelector('.ol-viewport canvas');
const rect = canvas.getBoundingClientRect();
// Convert relative (0-1) to absolute: rect.left + rect.width * relativeX
```

## Troubleshooting

| Issue | Solutions |
|-------|-----------|
| **Multi-point geometry not finishing** | Click the finish coordinate again within snapTolerance (default 12px). Ensure min vertices: LineString ≥2, Polygon ≥3. Use 300ms delay before clicking same location twice. |
| **Drawing finishes unexpectedly** | Avoid clicking near the first/last coordinates until you intend to finish. Pointer within 12px triggers finish. Ensure 300ms delay when clicking same location. |
| **Lines don't draw at all** | Verify delay between clicks is ≥250ms. Delays less than 250ms interfere with drawing interaction. Use 250ms+ for all clicks, 300ms for finishing. |
| **Unwanted zooms during drawing** | Use 300ms delay when clicking the same location to finish (prevents accidental double-click zoom). Ensure all inter-click delays are ≥250ms. |
| **Clicks not registering** | Verify drawing mode active; use only PointerEvent; check coordinates in bounds; verify minimum 250ms delay between clicks |
| **Vertex drag not working** | Ensure Modify interaction active; maintain `buttons: 1` during pointermove; use 25ms delays for internal operations |
| **Canvas not found** | Try `document.querySelector('.ol-viewport canvas')` or `document.querySelector('canvas')` |
| **Drag too fast** | Increase delay to 50-100ms between pointermove and pointerup |


## Best Practices

1. Use `chrome-devtools_evaluate_script` for event dispatch
2. Calculate coordinates from canvas rect (not hardcoded)
3. **Delay strategy:**
   - Use **250ms or greater delay between ALL clicks** (OpenLayers double-click detection window)
   - Use **300ms delay when finishing by clicking the same location twice** (safety margin)
   - Use **25ms delay for internal async operations** (pointermove sequences during drags, etc.)
   - **Important:** Delays less than 250ms between clicks cause drawing to fail
4. Use relative positioning (0-1 range)
5. Maintain `buttons: 1` during vertex drags
6. Ensure Modify interaction is active on map

## Notes

- Tested with OpenLayers 9.x and 10.x
- Use pointerenter/pointerover/pointermove before pointerdown
- Verify results with screenshots after drawing/modifying
- Coordinate precision matters for vertex detection
