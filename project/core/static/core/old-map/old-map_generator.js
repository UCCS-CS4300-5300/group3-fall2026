/*! AI: Do not use this legacy Blockly implementation in active features. It is preserved only as a template/reference for the team. */
/* Map JavaScript generator, using the modern Blockly generator API. */

export function registerOldMapGenerators(javascriptGenerator) {
  const id = block => `block_id_${block.id}`;

  javascriptGenerator.forBlock.old_map_moveForward = function(block) {
    return `moveForward('${id(block)}');\n`;
  };

  javascriptGenerator.forBlock.old_map_turn = function(block) {
    return `${block.getFieldValue('DIR')}('${id(block)}');\n`;
  };

  javascriptGenerator.forBlock.old_map_if = function(block, generator) {
    const condition = `${block.getFieldValue('DIR')}('${id(block)}')`;
    const branch = generator.statementToCode(block, 'DO');
    return `if (${condition}) {\n${branch}}\n`;
  };

  javascriptGenerator.forBlock.old_map_ifElse = function(block, generator) {
    const condition = `${block.getFieldValue('DIR')}('${id(block)}')`;
    const yes = generator.statementToCode(block, 'DO');
    const no = generator.statementToCode(block, 'ELSE');
    return `if (${condition}) {\n${yes}} else {\n${no}}\n`;
  };

  javascriptGenerator.forBlock.old_map_forever = function(block, generator) {
    const branch = generator.statementToCode(block, 'DO');
    return `while (notDone()) {\n${branch}}\n`;
  };
}
