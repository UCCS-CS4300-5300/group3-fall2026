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
    {
      type: 'map_punch', message0: 'punch',
      previousStatement: null, nextStatement: null, colour: 0,
    },
    {
      type: 'map_zombie', message0: 'if zombie ahead%1do %2',
      args0: [
        {type: 'input_dummy'},
        {type: 'input_statement', name: 'DO'}
      ], previousStatement: null, nextStatement: null, colour: 0,
    }
  ]);
}
