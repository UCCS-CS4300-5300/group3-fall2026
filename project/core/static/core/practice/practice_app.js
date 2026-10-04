import {Blockly} from '../blockly/blockly_setup.js';
import {MAP_TOOLBOX, registerMapBlocks} from '../map/map_blocks.js';

registerMapBlocks(Blockly);

const workspaceElement = document.getElementById('blockly-workspace');
const runButton = document.getElementById('lesson-run');
const resetButton = document.getElementById('lesson-reset');

console.info('[practice] Blockly module evaluated', {
  workspaceFound: Boolean(workspaceElement)
});

const workspace = Blockly.inject('blockly-workspace', {
  toolbox: MAP_TOOLBOX,
  trashcan: true,
  zoom: {controls: true, wheel: true, startScale: 1.1},
  move: {scrollbars: true, drag: true, wheel: true}
});
console.info('[practice] Blockly workspace injected', workspace);

runButton.addEventListener('click', () => console.log('Run button clicked'));
resetButton.addEventListener('click', () => console.log('Reset button clicked'));


window.addEventListener('resize', () => Blockly.svgResize(workspace));

// Writes the workspace as text, one block per line, indented for nesting, in the same words the
// AI uses for its intended code (see core/block_checker.py), so the server can compare them.
const PATH_NAMES = {isPathForward: 'path ahead', isPathLeft: 'path left', isPathRight: 'path right'};

function conditionText(block) {
  if (!block) return '(empty)';
  return block.type === 'map_zombie' ? 'zombie ahead' : block.type;
}

function stackLines(block, depth) {
  const lines = [];
  for (let b = block; b; b = b.getNextBlock()) lines.push(...blockLines(b, depth));
  return lines;
}

function blockLines(block, depth) {
  const line = text => '  '.repeat(depth) + text;
  const inside = input => stackLines(block.getInputTargetBlock(input), depth + 1);

  switch (block.type) {
    case 'map_moveForward': return [line('move forward')];
    case 'map_turn': return [line(block.getFieldValue('DIR') === 'turnLeft' ? 'turn left' : 'turn right')];
    case 'map_punch': return [line('punch')];
    case 'map_forever': return [line('repeat until finish'), ...inside('DO')];
    case 'controls_repeat': return [line(`repeat ${block.getFieldValue('TIMES')} times`), ...inside('DO')];
    case 'map_if': return [line(`if ${PATH_NAMES[block.getFieldValue('DIR')]}`), ...inside('DO')];
    case 'map_ifElse': return [
      line(`if ${PATH_NAMES[block.getFieldValue('DIR')]}`), ...inside('DO'), line('else'), ...inside('ELSE')
    ];
    case 'controls_if': {
      const lines = [];
      for (let i = 0; block.getInput(`IF${i}`); i++) {
        const condition = conditionText(block.getInputTargetBlock(`IF${i}`));
        lines.push(line(`${i ? 'else if' : 'if'} ${condition}`), ...inside(`DO${i}`));
      }
      if (block.getInput('ELSE')) lines.push(line('else'), ...inside('ELSE'));
      return lines;
    }
    default: return [line(block.type)];
  }
}

function workspaceToProgram() {
  return workspace.getTopBlocks(true)
    .filter(block => !block.outputConnection)  // a loose "zombie ahead" isn't part of the program
    .flatMap(block => stackLines(block, 0))
    .join('\n');
}

const checkButton = document.getElementById('practice-check');
const status = document.getElementById('practice-status');

async function checkBlocks() {
  status.textContent = 'Checking...';
  const response = await fetch(checkButton.dataset.checkUrl, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': checkButton.dataset.csrfToken},
    body: JSON.stringify({program: workspaceToProgram()})
  });
  if (!response.ok) {
    status.textContent = 'Could not check your blocks.';
    return;
  }
  const result = await response.json();

  result.tests.forEach((test, i) => {
    const item = document.querySelector(`.practice-tests li[data-test="${i}"]`);
    if (!item || test.passed === null) return;
    item.classList.toggle('passed', test.passed);
    item.classList.toggle('failed', !test.passed);
  });

  status.replaceChildren(result.passed ? 'All the blocks are in place!' : 'Still missing:');
  if (!result.passed) {
    const list = document.createElement('ul');
    for (const missing of result.missing) {
      const item = document.createElement('li');
      item.textContent = missing;
      list.append(item);
    }
    status.append(list);
  }
}

checkButton?.addEventListener('click', checkBlocks);
