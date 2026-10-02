import {javascriptGenerator} from 'blockly/javascript';
import {Blockly} from '../blockly/blockly_setup.js';

const workspaceElement = document.getElementById('blockly-workspace');
console.info('[practice] Blockly module evaluated', {
  workspaceFound: Boolean(workspaceElement)
});

const workspace = Blockly.inject('blockly-workspace', {
  toolbox: {
    kind: 'categoryToolbox',
    contents: [
      {
        kind: 'category',
        name: 'Logic',
        colour: '210',
        contents: [
          {kind: 'block', type: 'controls_if'},
          {kind: 'block', type: 'logic_compare'},
          {kind: 'block', type: 'logic_boolean'}
        ]
      },
      {
        kind: 'category',
        name: 'Loops',
        colour: '120',
        contents: [
          {kind: 'block', type: 'controls_repeat_ext'},
          {kind: 'block', type: 'controls_whileUntil'}
        ]
      },
      {
        kind: 'category',
        name: 'Math',
        colour: '230',
        contents: [
          {kind: 'block', type: 'math_number'},
          {kind: 'block', type: 'math_arithmetic'}
        ]
      },
      {
        kind: 'category',
        name: 'Text',
        colour: '160',
        contents: [
          {kind: 'block', type: 'text'},
          {kind: 'block', type: 'text_join'}
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
