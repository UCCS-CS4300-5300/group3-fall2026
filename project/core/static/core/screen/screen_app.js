import {createEncounterController} from '../boss/encounter_controller.js';

// =====================================================================
// Connect the screen controls to the active encounter's public commands
// =====================================================================
const encounter = createEncounterController(document);
document.getElementById('lesson-run').addEventListener('click', encounter.start);
document.getElementById('lesson-reset').addEventListener('click', encounter.reset);
