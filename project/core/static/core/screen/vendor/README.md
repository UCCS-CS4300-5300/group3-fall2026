# Local Blockly browser runtime

`blockly.js` is the existing browser-ready runtime copied from
`../../shared/chunks/javascript-CfGl1uZY.js`, with its license notices retained.
Its `B` export provides Blockly with the English locale and standard blocks registered.
The file also includes the JavaScript generator from the original build.

Screen imports this local file directly. Editing `../screen_app.js` or
`../screen_blocks.js` requires only a browser refresh, without npm or a build.
Keep this library file separate from application behavior. Updating the npm
dependency alone does not update this checked-in runtime.
