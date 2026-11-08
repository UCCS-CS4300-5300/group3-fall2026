# Shared boss and block structure

Blocks belong to the shared pool. Boss modules request stable block IDs, limits,
case labels, and a submission/playback format. A boss module does not register
its own Blockly definitions.

## Responsibilities

| Part | Responsibility |
| --- | --- |
| `core/bosses/__init__.py` | Resolve configured lessons and catalogue entries to boss modules; combine their workspace requests with shared defaults |
| `core/bosses/variables.py` | Request variable blocks and implement the variables encounter |
| `core/bosses/conditionals.py` | Request control/action blocks and resolve the fixed action-unit encounter |
| `core/blockly/block_program.py` | Read connected pooled blocks and validate requested types, labels, and allowances before execution |
| `core/rooms.py` | Initialize saved requirements, record verified wins, and require completion before leaving a boss |
| `core/views.py` | Validate the current mission/room and submit programs through the selected rules module |
| `core/bosses/program_results.py` | Give assignment, workspace, and legacy punch responses common feedback/detail fields |
| `blockly/block_pool.js` | Register pooled definitions and build a toolbox from requested IDs |
| `blockly/value_and_assignment_blocks.js` | Define reusable literal, variable, cashier, and punch blocks |
| `blockly/control_and_action_blocks.js` | Define reusable controls/actions and keep case chains structurally valid |
| `blockly/workspace_policy.js` | Apply allowances and label choices, display counts, and upgrade old saves |
| `blockly/assignment_conversion.js` | Read typed assignments from custom blocks |
| `blockly/program_submission.js` | Serialize the requested workspace, assignment, or legacy punch format |
| `screen/screen_app.js` | Wire Run to `encounter.start()` and Reset to `encounter.reset()` |
| `boss/encounter_controller.js` | Own submissions, request cancellation, result display, navigation, and playback coordination |
| `blockly/workspace_controller.js` | Own Blockly setup, saved connections, form saves, and program collection |
| `boss/run_feedback.js` | Display feedback and detail lines without identifying the active boss |

`core/bosses/thoughts.py` formats boss observations for the sidebar. The old
`BossLessonVar` import remains available from `lessons.py` for its lesson
registry, but its implementation lives in `core/bosses/variables.py`.

The screen does not collect or serialize programs, call the server, select
playback, or display results. Run only signals `encounter.start()`. The encounter
controller asks the workspace controller to collect the program, submits it,
and handles the response. Reset and navigation cancel stale requests so their
responses cannot update a newer attempt. Controller cleanup removes listeners
and disposes its workspace and playback resources.

JavaScript paths in this table are relative to `core/static/core/`.
The historical `boss_` block IDs remain to preserve saved programs. They do not
mean that a block definition belongs to an individual boss.

## Adding a boss module

Register the module and any catalogue aliases in `BOSS_MODULES`. Implement:

- `request_workspace_blocks()`: request pooled IDs, limits, case labels, and formats.
- `get_initial_requirements()`: return fresh victory requirements for a new room.
- `get_initial_variables()`: return fresh values for the page.
- `evaluate_submission(submission, requirements)`: evaluate fresh attempt state
  and return `passed` and `feedback`, plus optional `details` and execution data.

Add a definition to the shared pool only when a requested block does not already
exist. Extend shared readers for new syntax. Shared views, navigation, and result
display do not need branches for the new boss.

## Program submission and completion

All room programs use `/check/` with the current mission and room IDs. The
workspace request chooses `workspace`, typed `assignments`, or the legacy punch
text format. The server checks the room, loads its saved requirements, selects
its rules, and records verified completion through the same functions.

Every response exposes `feedback` and `details`; additional state and action data
remain available to playback. Failed retries never erase a saved win. The
conditional encounter starts fresh on every Run without losing lives.

## Conditional encounter

The remaining conditions are `undetected` and `not_close`. There is no numerical
distance simulation or final attack guard. The fixed attack is lunge.

```text
if undetected:
    make_noise()
    if not_close:
        wait()

if not_close:
    step_forward()
else:
    hold_position()

switch attack_type:
    case "grab":
        dodge()
    case "swipe":
        block()
    case "lunge":
        step_back()
    case "high_swing":
        duck()
    case "charge":
        step_aside()

attack()
```

Allowances are three plain if blocks, one if/else, one switch, five cases, and one
of each defense. All placed blocks count. Blockly prevents extra placements and
pastes; deleting restores capacity. Client and server both check the limits.
Extra if branches cannot bypass the plain-if allowance.

The switch contains a `CASES` statement chain. Each case stores its label in
`ATTACK` and actions in `DO`. Labels are supplied by the encounter request.
Actions cannot occupy the case chain, and cases cannot occupy ordinary action
slots. Only the selected case runs; cases do not fall through.

The intended executed path is make_noise, wait, step_forward, step_back, attack.
`ACTION_UNITS` is derived from that reference path, not student-program length.
Each action uses one of five units. Conditions, case selection, and skipped code
use none. The next action after the approach must defend; the finishing attack
then wins. Incomplete programs, incorrect defenses, and exhausting the action
budget without winning fail the attempt.

Execution events retain block IDs, decisions, and before/after states. Their
turns provide the boundaries for later animation; each action occupies one fifth
of total duration. Stage 3 computes results immediately. Stage 4 adds timelines,
stage 5 adds the synchronized Blockly pointer, and stage 6 adds broader testing.
Variation remains excluded.

Old fixed-slot switch saves are upgraded to case chains. The obsolete finishing
guard is unwrapped to retain its attack, while other incomplete inputs remain
visible for the player to repair. Focused controller checks cover cancellation and both playback modes; the
existing boss and regression checks cover the rules and shared block requests.

Each test covers one behavior and contains at most two assertions. Shared
fixtures provide setup rather than hiding assertions in helpers.
