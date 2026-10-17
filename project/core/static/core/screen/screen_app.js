import {B as Blockly} from './vendor/blockly.js';
import {registerScreenBlocks} from './screen_blocks.js';

const workspaceElement = document.getElementById('blockly-workspace');
const runButton = document.getElementById('lesson-run');
const resetButton = document.getElementById('lesson-reset');

console.info('[screen] Blockly module evaluated', {
  workspaceFound: Boolean(workspaceElement)
});


registerScreenBlocks(Blockly);

const workspace = Blockly.inject('blockly-workspace', {
  toolbox: {
    kind: 'categoryToolbox',
    contents: [
      {
        kind: 'category',
        name: 'Game',
        colour: '290',
        contents: [
          {kind: 'block', type: 'screen_punch'},
          {kind: 'block', type: 'screen_zombie'},
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
console.info('[screen] Blockly workspace injected', workspace);

const task = document.getElementById('screen-task');
const status = document.getElementById('screen-status');

// Turns the blocks into text like "if zombie\n  punch zombie" so the AI can read them
function blocksToText(block, indent = '') {
  let text = '';
  for (; block; block = block.getNextBlock()) {
    if (block.type === 'screen_punch') {
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
  try {
    const response = await fetch(task.dataset.checkUrl, {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': task.dataset.csrfToken},
      body: JSON.stringify({program})
    });
    const data = await response.json();
    status.textContent = response.ok
      ? `${data.punched ? '✓ The zombie was punched!' : '✗ The zombie was not punched.'} ${data.reason}`
      : data.error;
  } catch (error) {
    console.error('[screen] Check failed', error);
    status.textContent = 'Something went wrong checking your program. Refresh the page and try again.';
  }
});

resetButton.addEventListener('click', () => { status.textContent = ''; });


window.addEventListener('resize', () => Blockly.svgResize(workspace));
