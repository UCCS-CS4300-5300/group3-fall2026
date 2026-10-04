/* Map-specific Blockly blocks, adapted from Blockly Games Map. */

export function registerMapBlocks(Blockly) {
  Blockly.defineBlocksWithJsonArray([
    {
      type: 'map_moveForward', message0: 'move forward',
      previousStatement: null, nextStatement: null, colour: 290,
    },
    {
      type: 'map_turn', message0: '%1',
      args0: [{type: 'field_dropdown', name: 'DIR', options: [
        ['turn left', 'turnLeft'], ['turn right', 'turnRight']
      ]}],
      previousStatement: null, nextStatement: null, colour: 290,
    },
    {
      type: 'map_if', message0: '%1%2do %3',
      args0: [
        {type: 'field_dropdown', name: 'DIR', options: [
          ['path ahead', 'isPathForward'], ['path left', 'isPathLeft'], ['path right', 'isPathRight']
        ]},
        {type: 'input_dummy'},
        {type: 'input_statement', name: 'DO'}
      ], previousStatement: null, nextStatement: null, colour: 210,
    },
    {
      type: 'map_ifElse', message0: '%1%2do %3else %4',
      args0: [
        {type: 'field_dropdown', name: 'DIR', options: [
          ['path ahead', 'isPathForward'], ['path left', 'isPathLeft'], ['path right', 'isPathRight']
        ]},
        {type: 'input_dummy'}, {type: 'input_statement', name: 'DO'},
        {type: 'input_statement', name: 'ELSE'}
      ], previousStatement: null, nextStatement: null, colour: 210,
    },
    {
      type: 'map_forever', message0: 'repeat until finish %1',
      args0: [{type: 'input_statement', name: 'DO'}],
      previousStatement: null, colour: 120,
    },
    // Demo-only blocks: "if zombie ahead" + "punch" snap together, but have no game behavior yet.
    {
      type: 'map_punch', message0: 'punch',
      previousStatement: null, nextStatement: null, colour: 0,
    },
    {
      type: 'map_zombie', message0: 'zombie ahead',
      output: 'Boolean', colour: 20,
    }
  ]);
}

// The toolbox shared by the Map and Practice pages.
export const MAP_TOOLBOX = {
  kind: 'categoryToolbox',
  contents: [
    {kind: 'category', name: 'Movement', colour: '290', contents: [
      {kind: 'block', type: 'map_moveForward'},
      {kind: 'block', type: 'map_turn'}
    ]},
    {kind: 'category', name: 'Logic', colour: '210', contents: [
      {kind: 'block', type: 'map_if'},
      {kind: 'block', type: 'map_ifElse'},
      {kind: 'block', type: 'controls_if'}
    ]},
    {kind: 'category', name: 'Loops', colour: '120', contents: [
      {kind: 'block', type: 'map_forever'},
      {kind: 'block', type: 'controls_repeat'}
    ]},
    {kind: 'category', name: 'Combat', colour: '0', contents: [
      // An "if" with "zombie ahead" already plugged in
      {kind: 'block', type: 'controls_if', inputs: {IF0: {block: {type: 'map_zombie'}}}},
      {kind: 'block', type: 'map_zombie'},
      {kind: 'block', type: 'map_punch'}
    ]}
  ]
};
