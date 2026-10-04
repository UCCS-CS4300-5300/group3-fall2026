import {javascriptGenerator} from 'blockly/javascript';
import {Blockly} from '../blockly/blockly_setup.js';
import {registerPracticeBlocks} from '../practice/practice_blocks.js';

const workspaceElement = document.getElementById('blockly-workspace');
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

window.addEventListener('resize', () => Blockly.svgResize(workspace));

// Keep the generator imported here so this page is ready for its own task logic.
void javascriptGenerator;
