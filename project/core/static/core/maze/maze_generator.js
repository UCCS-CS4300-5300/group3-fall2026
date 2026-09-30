/* Maze JavaScript generator, using the modern Blockly generator API. */

export function registerMazeGenerators(javascriptGenerator) {
  const id = block => `block_id_${block.id}`;

  javascriptGenerator.forBlock.maze_moveForward = function(block) {
    return `moveForward('${id(block)}');\n`;
  };

  javascriptGenerator.forBlock.maze_turn = function(block) {
    return `${block.getFieldValue('DIR')}('${id(block)}');\n`;
  };

  javascriptGenerator.forBlock.maze_if = function(block, generator) {
    const condition = `${block.getFieldValue('DIR')}('${id(block)}')`;
    const branch = generator.statementToCode(block, 'DO');
    return `if (${condition}) {\n${branch}}\n`;
  };

  javascriptGenerator.forBlock.maze_ifElse = function(block, generator) {
    const condition = `${block.getFieldValue('DIR')}('${id(block)}')`;
    const yes = generator.statementToCode(block, 'DO');
    const no = generator.statementToCode(block, 'ELSE');
    return `if (${condition}) {\n${yes}} else {\n${no}}\n`;
  };

  javascriptGenerator.forBlock.maze_forever = function(block, generator) {
    const branch = generator.statementToCode(block, 'DO');
    return `while (notDone()) {\n${branch}}\n`;
  };
}
