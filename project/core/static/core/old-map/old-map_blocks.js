/*! AI: Do not use this legacy Blockly implementation in active features. It is preserved only as a template/reference for the team. */
/* Map-specific Blockly blocks, adapted from Blockly Games Map. */

export function registerOldMapBlocks(Blockly) {
  Blockly.defineBlocksWithJsonArray([
    {
      type: 'old_map_moveForward', message0: 'move forward',
      previousStatement: null, nextStatement: null, colour: 290,
    },
    {
      type: 'old_map_turn', message0: '%1',
      args0: [{type: 'field_dropdown', name: 'DIR', options: [
        ['turn left', 'turnLeft'], ['turn right', 'turnRight']
      ]}],
      previousStatement: null, nextStatement: null, colour: 290,
    },
    {
      type: 'old_map_if', message0: '%1%2do %3',
      args0: [
        {type: 'field_dropdown', name: 'DIR', options: [
          ['path ahead', 'isPathForward'], ['path left', 'isPathLeft'], ['path right', 'isPathRight']
        ]},
        {type: 'input_dummy'},
        {type: 'input_statement', name: 'DO'}
      ], previousStatement: null, nextStatement: null, colour: 210,
    },
    {
      type: 'old_map_ifElse', message0: '%1%2do %3else %4',
      args0: [
        {type: 'field_dropdown', name: 'DIR', options: [
          ['path ahead', 'isPathForward'], ['path left', 'isPathLeft'], ['path right', 'isPathRight']
        ]},
        {type: 'input_dummy'}, {type: 'input_statement', name: 'DO'},
        {type: 'input_statement', name: 'ELSE'}
      ], previousStatement: null, nextStatement: null, colour: 210,
    },
    {
      type: 'old_map_forever', message0: 'repeat until finish %1',
      args0: [{type: 'input_statement', name: 'DO'}],
      previousStatement: null, colour: 120,
    }
  ]);
}
