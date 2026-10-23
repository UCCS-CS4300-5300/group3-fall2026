/* Custom Blocks for screen. We're likely gonna want to our custom blocks into their own specific file so we can import them into anywhere */

// Currently these blocks have no functionality and exist just for display purposes. We will need to implement their functionality in the future.
export function registerScreenBlocks(Blockly) {
  Blockly.defineBlocksWithJsonArray([
    {
      type: 'screen_punch',
      message0: 'punch zombie',
      previousStatement: null,
      nextStatement: null,
      colour: 290
    },
    {
      type: 'screen_zombie',
      message0: 'zombie',
      output: 'Boolean',
      colour: 210
    }
]);
}