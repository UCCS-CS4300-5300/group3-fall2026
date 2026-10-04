/* Map JavaScript generator, using the modern Blockly generator API. */

export function registerMapGenerators(javascriptGenerator) {
  const id = block => `block_id_${block.id}`;

  javascriptGenerator.forBlock.map_moveForward = function(block) {
    return `moveForward('${id(block)}');\n`;
  };

  javascriptGenerator.forBlock.map_turn = function(block) {
    return `${block.getFieldValue('DIR')}('${id(block)}');\n`;
  };

  javascriptGenerator.forBlock.map_if = function(block, generator) {
    const condition = `${block.getFieldValue('DIR')}('${id(block)}')`;
    const branch = generator.statementToCode(block, 'DO');
    return `if (${condition}) {\n${branch}}\n`;
  };

  javascriptGenerator.forBlock.map_ifElse = function(block, generator) {
    const condition = `${block.getFieldValue('DIR')}('${id(block)}')`;
    const yes = generator.statementToCode(block, 'DO');
    const no = generator.statementToCode(block, 'ELSE');
    return `if (${condition}) {\n${yes}} else {\n${no}}\n`;
  };

  javascriptGenerator.forBlock.map_forever = function(block, generator) {
    const branch = generator.statementToCode(block, 'DO');
    return `while (notDone()) {\n${branch}}\n`;
  };

  // Demo-only blocks: punch does nothing yet and there are no zombies on the map, so the
  // program still runs when they are on the workspace.
  javascriptGenerator.forBlock.map_punch = function() {
    return '// punch\n';
  };

  javascriptGenerator.forBlock.map_zombie = function(block, generator) {
    return ['false', generator.ORDER_ATOMIC];
  };
}
