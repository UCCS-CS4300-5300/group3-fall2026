/* Maze-specific Blockly blocks, adapted from Blockly Games Maze. */

export function registerMazeBlocks(Blockly) {
  Blockly.defineBlocksWithJsonArray([
    {
      type: 'maze_moveForward', message0: 'move forward',
      previousStatement: null, nextStatement: null, colour: 290,
    },
    {
      type: 'maze_turn', message0: '%1',
      args0: [{type: 'field_dropdown', name: 'DIR', options: [
        ['turn left', 'turnLeft'], ['turn right', 'turnRight']
      ]}],
      previousStatement: null, nextStatement: null, colour: 290,
    },
    {
      type: 'maze_if', message0: '%1%2do %3',
      args0: [
        {type: 'field_dropdown', name: 'DIR', options: [
          ['path ahead', 'isPathForward'], ['path left', 'isPathLeft'], ['path right', 'isPathRight']
        ]},
        {type: 'input_dummy'},
        {type: 'input_statement', name: 'DO'}
      ], previousStatement: null, nextStatement: null, colour: 210,
    },
    {
      type: 'maze_ifElse', message0: '%1%2do %3else %4',
      args0: [
        {type: 'field_dropdown', name: 'DIR', options: [
          ['path ahead', 'isPathForward'], ['path left', 'isPathLeft'], ['path right', 'isPathRight']
        ]},
        {type: 'input_dummy'}, {type: 'input_statement', name: 'DO'},
        {type: 'input_statement', name: 'ELSE'}
      ], previousStatement: null, nextStatement: null, colour: 210,
    },
    {
      type: 'maze_forever', message0: 'repeat until finish %1',
      args0: [{type: 'input_statement', name: 'DO'}],
      previousStatement: null, colour: 120,
    }
  ]);
}
