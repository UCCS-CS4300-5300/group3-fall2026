import * as Blockly from 'blockly/core';
import {javascriptGenerator} from 'blockly/javascript';
import Interpreter from 'js-interpreter';
import {registerMazeBlocks} from './maze_blocks.js';
import {registerMazeGenerators} from './maze_generator.js';
import {MazeEngine} from './maze_engine.js';
import {MazeRenderer} from './maze_renderer.js';
import {MAZE_LEVELS, MAX_BLOCKS} from './levels.js';

registerMazeBlocks(Blockly);
registerMazeGenerators(javascriptGenerator);

const levelNumber = Math.max(1, Math.min(10, Number(window.MAZE_LEVEL || 1)));
const engine = new MazeEngine(MAZE_LEVELS[levelNumber - 1]);
const renderer = new MazeRenderer(document.getElementById('maze-visualization'));
renderer.draw(engine);

const workspace = Blockly.inject('blockly-workspace', {
  toolbox: {
    kind: 'categoryToolbox',
    contents: [
      {kind: 'category', name: 'Movement', colour: '290', contents: [
        {kind: 'block', type: 'maze_moveForward'},
        {kind: 'block', type: 'maze_turn'}
      ]},
      {kind: 'category', name: 'Logic', colour: '210', contents: [
        {kind: 'block', type: 'maze_if'},
        {kind: 'block', type: 'maze_ifElse'}
      ]},
      {kind: 'category', name: 'Loops', colour: '120', contents: [
        {kind: 'block', type: 'maze_forever'}
      ]}
    ]
  },
  trashcan: true,
  maxBlocks: MAX_BLOCKS[levelNumber - 1],
  zoom: {controls: true, wheel: true, startScale: 1.1},
  move: {scrollbars: true, drag: true, wheel: true}
});

const runButton = document.getElementById('maze-run');
const resetButton = document.getElementById('maze-reset');
const status = document.getElementById('maze-status');

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
    if (error && error.mazeSuccess) result = 'success';
    else if (error instanceof Error && error.message === 'Maze collision') result = 'failure';
    else {
      console.error(error);
      result = 'error';
    }
  }

  // Replay from a clean starting position.  The engine state has already
  // recorded the actions, so use a separate replay position below.
  const replayEngine = new MazeEngine(MAZE_LEVELS[levelNumber - 1]);
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
