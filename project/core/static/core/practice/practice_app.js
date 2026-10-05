import {javascriptGenerator} from 'blockly/javascript';
import {Blockly} from '../blockly/blockly_setup.js';
import {registerPracticeBlocks} from '../practice/practice_blocks.js';

const workspaceElement = document.getElementById('blockly-workspace');
const runButton = document.getElementById('lesson-run');
const resetButton = document.getElementById('lesson-reset');

console.info('[practice] Blockly module evaluated', {
  workspaceFound: Boolean(workspaceElement)
});


registerPracticeBlocks(Blockly);

const workspace = Blockly.inject('blockly-workspace', {
  toolbox: {
    kind: 'categoryToolbox',
    contents: [
      {
        kind: 'category',
        name: 'Game',
        colour: '290',
        contents: [
          {kind: 'block', type: 'practice_punch'},
          {kind: 'block', type: 'practice_zombie'},
        ]
      },
      {
        kind: 'category',
        name: 'Logic',
        colour: '210',
        contents: [
          {kind: 'block', type: 'controls_if'}
      ]
      }
    ]
  },
  trashcan: true,
  zoom: {controls: true, wheel: true, startScale: 1.1},
  move: {scrollbars: true, drag: true, wheel: true}
});
console.info('[practice] Blockly workspace injected', workspace);

const task = document.getElementById('practice-task');
const status = document.getElementById('practice-status');

// Turns the blocks into text like "if zombie\n  punch zombie" so the AI can read them
function blocksToText(block, indent = '') {
  let text = '';
  for (; block; block = block.getNextBlock()) {
    if (block.type === 'practice_punch') {
      text += `${indent}punch zombie\n`;
    } else if (block.type === 'controls_if') {
      const condition = block.getInputTargetBlock('IF0');
      text += `${indent}if ${condition ? 'zombie' : '(empty)'}\n`;
      text += blocksToText(block.getInputTargetBlock('DO0'), indent + '  ');
    }
  }
  return text;
}

runButton.addEventListener('click', async () => {
  const program = workspace.getTopBlocks(true).map(block => blocksToText(block)).join('');
  status.textContent = 'Checking your program...';
  const response = await fetch(task.dataset.checkUrl, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': task.dataset.csrfToken},
    body: JSON.stringify({program})
  });
  const data = await response.json();
  status.textContent = response.ok
    ? `${data.punched ? '✓ The zombie was punched!' : '✗ The zombie was not punched.'} ${data.reason}`
    : data.error;
});

resetButton.addEventListener('click', () => { status.textContent = ''; });


window.addEventListener('resize', () => Blockly.svgResize(workspace));

// Keep the generator imported here so this page is ready for its own task logic.
void javascriptGenerator;
