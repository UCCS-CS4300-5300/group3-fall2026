import {javascriptGenerator} from 'blockly/javascript';
import {Blockly} from '../blockly/blockly_setup.js';
import {registerMapBlocks} from '../map/map_blocks.js';

const workspaceElement = document.getElementById('blockly-workspace');
console.info('[practice] Blockly module evaluated', {
  workspaceFound: Boolean(workspaceElement)
});


registerMapBlocks(Blockly);

const workspace = Blockly.inject('blockly-workspace', {
  toolbox: {
    kind: 'categoryToolbox',
    contents: [
      {
        kind: 'category',
        name: 'Game',
        colour: '290',
        contents: [
          {kind: 'block', type: 'map_moveForward'},
          {kind: 'block', type: 'map_turn'},
          {kind: 'block', type: 'map_punch'},
          {kind: 'block', type: 'map_zombie'},
          {kind: 'block', type: 'map_if'},
          {kind: 'block', type: 'map_ifElse'},
          {kind: 'block', type: 'map_forever'}
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
