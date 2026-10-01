# Blockly Games Map integration

This folder contains a Django-friendly adaptation of the public Blockly Games Map architecture.

The original Blockly Games Map is Apache-2.0 licensed and lives at:
https://github.com/blockly-games/blockly-games/tree/master/appengine/maze

The adaptation keeps the useful Map concepts from Google's implementation:
- the 0/1/2/3 grid format (wall/open/start/finish)
- Map-specific Blockly blocks
- JavaScript generation with block IDs
- JS-Interpreter execution with an injected Map API
- execution log followed by animated replay

The old Closure/Blockly Games application shell is intentionally not included. Django owns the page, and modern Blockly is loaded from the npm package.

## Install JavaScript dependencies

From the project root:

    npm install
    npm run build

The build is required because modern Blockly publishes its npm modules for bundlers rather than direct browser module loading. The Vite build writes the browser bundle to `core/static/core/map/dist/`.

Then run Django normally:

    python manage.py runserver

The first implementation uses CSS/SVG primitives for the map character and tiles so the integration has no external binary asset dependency. Google's original sprite/audio assets can be added later, with their original license/attribution notices retained.

## What was intentionally removed

The original Map source depends on Blockly Games globals such as `BlocklyGames`, `BlocklyInterface`, `BlocklyCode`, and Closure `goog.provide`/`goog.require`. Those are replaced here by Django, modern Blockly, and a small local runner. The original Map block set, level grids, injected interpreter API, action log, and replay model are retained conceptually.
