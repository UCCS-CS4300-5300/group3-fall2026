import {Blockly} from '../blockly/blockly_setup.js';
import {javascriptGenerator} from 'blockly/javascript';
import Interpreter from 'js-interpreter';
import {registerMapBlocks} from './map_blocks.js';
import {registerMapGenerators} from './map_generator.js';
import {MapEngine} from './map_engine.js';
import {MapRenderer} from './map_renderer.js';
import {MAP_LEVELS, MAX_BLOCKS} from './levels.js';

registerMapBlocks(Blockly);
registerMapGenerators(javascriptGenerator);

const levelNumber = Math.max(1, Math.min(10, Number(window.MAP_LEVEL || 1)));
const engine = new MapEngine(MAP_LEVELS[levelNumber - 1]);
const renderer = new MapRenderer(document.getElementById('map-visualization'));
renderer.draw(engine);

const workspace = Blockly.inject('blockly-workspace', {
  toolbox: {
    kind: 'categoryToolbox',
    contents: [
      {kind: 'category', name: 'Movement', colour: '290', contents: [
        {kind: 'block', type: 'map_moveForward'},
        {kind: 'block', type: 'map_turn'}
      ]},
      {kind: 'category', name: 'Logic', colour: '210', contents: [
        {kind: 'block', type: 'map_if'},
        {kind: 'block', type: 'map_ifElse'}
      ]},
      {kind: 'category', name: 'Loops', colour: '120', contents: [
        {kind: 'block', type: 'map_forever'}
      ]}
    ]
  },
  trashcan: true,
  maxBlocks: MAX_BLOCKS[levelNumber - 1],
  zoom: {controls: true, wheel: true, startScale: 1.1},
  move: {scrollbars: true, drag: true, wheel: true}
});

Blockly.serialization.blocks.append(
  {
    type: 'map_moveForward',
    x: 40,
    y: 40
  },
  workspace
);

Blockly.serialization.blocks.append(
  {
    type: 'map_turn',
    x: 40,
    y: 110
  },
  workspace
);

Blockly.serialization.blocks.append(
  {
    type: 'map_forever',
    x: 40,
    y: 180
  },
  workspace
);

console.log('BLOCKS:', workspace.getAllBlocks(false));
console.log('BLOCK COUNT:', workspace.getAllBlocks(false).length);

workspace.render();
Blockly.svgResize(workspace);

const runButton = document.getElementById('map-run');
const resetButton = document.getElementById('map-reset');
const status = document.getElementById('map-status');

function highlight(blockId) { workspace.highlightBlock(blockId); }

function runProgram() {
  engine.reset();
  renderer.draw(engine);
  status.textContent = 'Running...';

  javascriptGenerator.STATEMENT_PREFIX = '';
  const code = javascriptGenerator.workspaceToCode(workspace);
  const interpreter = new Interpreter(code, (interpreter, globalObject) => {
    const wrap = (name, fn) => interpreter.setProperty(globalObject, name,
      interpreter.createNativeFunction(fn));
    wrap('moveForward', id => engine.move(0, id));
    wrap('turnLeft', id => engine.turn(0, id));
    wrap('turnRight', id => engine.turn(1, id));
    wrap('isPathForward', id => engine.isPath(0, id));
    wrap('isPathRight', id => engine.isPath(1, id));
    wrap('isPathLeft', id => engine.isPath(3, id));
    wrap('notDone', () => engine.notDone());
  });

  let result = 'failure';
  try {
    let ticks = 10000;
    while (interpreter.step()) {
      if (--ticks <= 0) throw new Error('Program timed out.');
    }
    result = engine.notDone() ? 'failure' : 'success';
  } catch (error) {
    if (error && error.mapSuccess) result = 'success';
    else if (error instanceof Error && error.message === 'Map collision') result = 'failure';
    else {
      console.error(error);
      result = 'error';
    }
  }

  // Replay from a clean starting position.  The engine state has already
  // recorded the actions, so use a separate replay position below.
  const replayEngine = new MapEngine(MAP_LEVELS[levelNumber - 1]);
  renderer.draw(replayEngine);
  replayLog(replayEngine, result);
}

async function replayLog(replayEngine, result) {
  for (const action of engine.log) {
    highlight(action.blockId || null);
    if (action.type === 'move') {
      replayEngine.position = replayEngine.target(0);
      replayEngine.direction = action.direction;
      renderer.setPlayer(replayEngine.position, replayEngine.direction);
    } else if (action.type === 'left') {
      replayEngine.direction = (replayEngine.direction + 3) % 4;
      renderer.setPlayer(replayEngine.position, replayEngine.direction);
    } else if (action.type === 'right') {
      replayEngine.direction = (replayEngine.direction + 1) % 4;
      renderer.setPlayer(replayEngine.position, replayEngine.direction);
    }
    await renderer.wait(120);
  }
  highlight(null);
  status.textContent = result === 'success' ? 'Solved!' : result === 'error' ? 'Error running program.' : 'Program finished without reaching the goal.';
}

runButton.addEventListener('click', runProgram);
resetButton.addEventListener('click', () => {
  engine.reset();
  renderer.draw(engine);
  workspace.highlightBlock(null);
  status.textContent = '';
});

window.addEventListener('resize', () => Blockly.svgResize(workspace));
