import 'blockly/blocks';
import {javascriptGenerator} from 'blockly/javascript';
import {pythonGenerator} from 'blockly/python';
import {Blockly} from '../blockly/blockly_setup.js';

const blockCategories = [
  {
    name: 'Logic',
    colour: '#4c97ff',
    blocks: [
      {type: 'controls_if', label: 'if'},
      {type: 'logic_compare', label: 'comparison'},
      {type: 'logic_boolean', label: 'true / false'}
    ]
  },
  {
    name: 'Loops',
    colour: '#5ba55b',
    blocks: [
      {type: 'controls_repeat_ext', label: 'repeat'},
      {type: 'controls_whileUntil', label: 'while / until'}
    ]
  },
  {
    name: 'Math',
    colour: '#5b67a5',
    blocks: [
      {type: 'math_number', label: 'number'},
      {type: 'math_arithmetic', label: 'arithmetic'}
    ]
  },
  {
    name: 'Text',
    colour: '#5ba58c',
    blocks: [
      {type: 'text', label: 'text'},
      {type: 'text_join', label: 'join text'}
    ]
  }
];
const availableBlockTypes = new Set(
  blockCategories.flatMap(category => category.blocks.map(block => block.type))
);

const workspace = Blockly.inject('blockly-workspace', {
  trashcan: true,
  zoom: {controls: true, wheel: true, startScale: 1.1},
  move: {scrollbars: true, drag: true, wheel: true}
});

const wordBank = document.getElementById('blockly-toolbox');
const workspaceSvg = workspace.getParentSvg();
const generatedCodeOutput = document.getElementById('generated-code-output');

function updateGeneratedCode(event) {
  if (event?.isUiEvent) return;
  generatedCodeOutput.textContent = pythonGenerator.workspaceToCode(workspace) || '// No code generated yet.';
}

workspace.addChangeListener(updateGeneratedCode);

workspaceSvg.addEventListener('dragover', (event) => {
  event.preventDefault();
  event.dataTransfer.dropEffect = 'copy';
}, true);

workspaceSvg.addEventListener('drop', (event) => {
  event.preventDefault();
  const blockType = event.dataTransfer.getData('text/plain');
  if (availableBlockTypes.has(blockType)) {
    createBlock(blockType, event.clientX, event.clientY);
  }
}, true);

function createBlock(blockType, screenX, screenY) {
  const coordinates = Blockly.utils.svgMath.screenToWsCoordinates(
    workspace,
    {x: screenX, y: screenY}
  );
  const block = workspace.newBlock(blockType);
  block.initSvg();
  block.render();
  block.moveBy(coordinates.x, coordinates.y);
}

for (const category of blockCategories) {
  const section = document.createElement('section');
  section.className = 'word-bank-category';

  const heading = document.createElement('h3');
  heading.textContent = category.name;
  section.append(heading);

  for (const item of category.blocks) {
    const blockButton = document.createElement('button');
    blockButton.className = 'word-bank-block';
    blockButton.type = 'button';
    blockButton.draggable = true;
    blockButton.textContent = item.label;
    blockButton.style.setProperty('--block-colour', category.colour);
    blockButton.dataset.blockType = item.type;
    blockButton.addEventListener('dragstart', (event) => {
      event.dataTransfer.setData('text/plain', item.type);
      event.dataTransfer.effectAllowed = 'copy';
    });
    blockButton.addEventListener('click', () => {
      const bounds = workspaceSvg.getBoundingClientRect();
      const blockCount = workspace.getAllBlocks(false).length;
      const column = blockCount % 4;
      const row = Math.floor(blockCount / 4);
      createBlock(item.type, bounds.left + 32 + column * 36, bounds.top + 48 + row * 48);
    });
    section.append(blockButton);
  }

  wordBank.append(section);
}

window.addEventListener('resize', () => Blockly.svgResize(workspace));
