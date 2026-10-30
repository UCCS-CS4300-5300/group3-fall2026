# Current code architecture

Snapshot of the working tree on October 30, 2026. This describes implemented code, including uncommitted changes. Paths below are relative to `project/`.

## The live game

Arrows show calls or the direction data travels; they are not all Python/JavaScript imports.

```mermaid
flowchart TB
    URL["config/urls.py → core/urls.py<br/>Page, navigation, and check routes"]

    subgraph SERVER["Django server · core/"]
        VIEW["views.py<br/>Assemble pages, handle navigation,<br/>dispatch program checks"]
        ROOM["rooms.py<br/>Open / advance / reset rooms<br/>Initialize encounter requirements"]
        MODEL["models.py → db.sqlite3<br/>Mission · RoomDefinition<br/>RoomState · Puzzle"]
        LESSON["lessons.py<br/>Existing lesson behavior and success checks<br/>Blocks, starting values, requirements<br/>Image settings and room associations"]
        RUNNER["lesson_runner.py<br/>Existing typed assignment evaluation"]
        PUNCH["zombie_checker.py<br/>Evaluate fallback punch text"]
        PLANE["static/core/png_movement/png_move.py<br/>SERVER Python: prepare plane + motion"]
    end

    subgraph CLIENT["Browser · core/templates/ + core/static/"]
        PAGE["templates/core/screen.html<br/>Room image, controls, JSON configuration"]
        APP["screen/screen_app.js<br/>Coordinate workspace, Run, reset,<br/>requests, feedback, and movement"]
        BLOCK["blockly_setup.js · screen_blocks.js<br/>blockly_assignments.js<br/>Blockly setup, blocks, conversion"]
        MOVE["png_move.js + png_move.css<br/>Movement coordinator and helper functions"]
        TUTORIAL["screen/tutorial_panel.js<br/>Load and display tutorial Markdown"]
    end

    URL --> VIEW
    VIEW --> ROOM
    ROOM --> MODEL
    ROOM --> LESSON
    VIEW --> MODEL
    VIEW --> LESSON
    LESSON -->|"applies assignments"| RUNNER
    VIEW --> PUNCH
    VIEW --> PLANE
    PLANE -->|"image settings lookup"| LESSON
    VIEW -->|"HTML + initial state"| PAGE
    PAGE --> APP
    PAGE --> TUTORIAL
    APP --> BLOCK
    APP --> MOVE
    APP -->|"POST /check/ · result JSON returns"| VIEW
```

`main-menu.html` lists missions and links into this screen. Next/Exit forms submit workspace JSON to `views.py`; `Puzzle.workspace_state` stores it by room ID. `RoomState` stores completion and encounter requirements, while `Mission` stores the current room. These are shared database records, not separate per-user progress models.

There are two registered lessons: `BossLessonVar` and `JumpscareCashierLesson`. Their existing methods evaluate submissions and check success; the variables lesson delegates typed assignments to `lesson_runner.py`. The movement feature adds picture associations without replacing that lesson structure. A room without a lesson ID uses the punch-text checker. That checker currently evaluates locally; its Ollama imports do not mean each check calls AI.

## Plane, picture, and translation ownership

```mermaid
flowchart TB
    subgraph DATA["Authored data · read by the server"]
        ROOMDATA["core/exercises/exercises.json<br/>Non-boss lesson_id selected by exercise_set_id<br/>room_profile + visuals + exercises"]
        BOSSDATA["png_movement/data/mission_*_floor_profiles.json<br/>Existing boss room geometry"]
        DEFAULT["png_movement/data/png_move_floor.json<br/>Fallback plane + path"]
        VISUAL["core/data/lesson_profiles.json<br/>Existing boss presentation placements<br/>Defaults + shared speed / death / timing settings"]
    end

    PY["png_move.py · load_room_floor()<br/>Compose room plane/path + lesson picture<br/>Validate and calculate projection matrices"]
    LESSON["lessons.py<br/>load_room_lesson_visuals()<br/>load_movement_settings()"]
    GATE["views.py → screen.html<br/>Last room: prepared floor + movement settings<br/>Other rooms: no floor payload, movement disabled"]

    subgraph BROWSER["Browser movement · functions in png_move.js"]
        GEOMETRY["projectPoint / initializeFloor<br/>Coordinate conversion<br/>Draw cyan grid + yellow path"]
        PREVIEW["initializeMovement / renderSprite<br/>Connect data, images, controls, and drawing<br/>Disabled → createDefaultMovement"]
        ENCOUNTER["createRunAttempt<br/>Attempt identity<br/>Apply results; ignore stale results"]
        PLAYBACK["createTranslation / getTranslationPose<br/>Motion translation + projected poses<br/>Speed, pause, reset, death timing"]
        SPRITE["cat.jpg + png_move.css<br/>Current picture and visual layers"]
    end

    ROOMDATA --> PY
    ROOMDATA --> LESSON
    BOSSDATA --> PY
    DEFAULT -->|"missing or mismatched profile"| PY
    VISUAL --> LESSON
    LESSON -->|"picture, anchor, size, duration"| PY
    LESSON -->|"playback settings"| GATE
    PY --> GATE
    GATE --> GEOMETRY
    GATE --> PREVIEW
    PREVIEW --> ENCOUNTER
    ENCOUNTER -->|"start / speed / die / reset"| PLAYBACK
    PREVIEW -->|"creates translation and handles visibility"| PLAYBACK
    PLAYBACK -->|"uses projection functions"| GEOMETRY
    PLAYBACK -->|"pose + state callback"| PREVIEW
    SPRITE --> PREVIEW
```

The 40 placed non-boss activities store room geometry under `room_profile` and picture settings under `visuals` in `core/exercises/exercises.json`, alongside their exercises. `RoomDefinition.exercise_set_id` selects the record by its JSON `lesson_id`, independently of database mission/room IDs. The 10 bosses retain their existing geometry files and presentation placements. All 50 current rooms retain geometry records; movement is enabled only when `RoomDefinition.next_room_id` is empty. Each presentation can select its own picture, but the current records all use `cat.jpg`.

`RoomDefinition.lesson_id` still selects executable behavior in `lessons.LESSONS`. `exercise_set_id` selects non-boss authored content, including visuals, by the exercise catalog's `lesson_id`. Boss presentation references remain separate from behavior IDs. There is no Lesson database model.

## What happens when Run is pressed

```mermaid
sequenceDiagram
    actor Player
    participant App as screen_app.js
    participant Movement as png_move.js
    participant View as views.check_program()
    participant Lesson as lessons.py / lesson_runner.py
    participant DB as RoomState

    Player->>App: Run
    App->>Movement: start(initial speed) → attempt token
    Note over Movement: Approach starts before the check finishes.<br/>Ordinary rooms use a no-op controller.
    App->>View: POST /check/ with room IDs + assignments
    View->>Lesson: Call the lesson's existing evaluation method
    Lesson-->>View: Variables, actions, passed, feedback
    opt Lesson passed
        View->>DB: Save completed = True
    end
    View-->>App: Result JSON
    App->>Movement: applyResult(attempt token, result)
    Note over Movement: Ignore stale attempts; apply speed.<br/>Success: wait for 500 ms visible time,<br/>then rotate 80° clockwise at the current pose.
    App-->>Player: Feedback and final variables
    Note over App,Movement: Reset / navigation aborts requests and invalidates attempts.
```

Rooms without a lesson ID submit punch text instead of assignments. `zombie_checker.py` returns `punched` and `reason`; the movement controller accepts that result too. The translation uses the server's success result to trigger death. Speed is clamped to 1–20, with normal speed 10.

## Supporting code and boundaries

| Area | Files | Role / connection |
| --- | --- | --- |
| Content creation | `core/management/commands/create_mission.py`, `add_room.py` → `rooms.py` | Create database records, copy room assets, maintain room links and boss placement. |
| AI mission creation | `generate_mission.py` → `core/mission_generator.py` → Ollama | Explicit management command creates Mission/Puzzle content; normal screen requests do not generate missions. |
| Content removal | `remove_content.py` → `core/room_removal.py` | Update room chains and remove unused generated files. |
| Admin | `core/admin.py` | Registers Mission in Django admin. |
| Static content | `assets/`, `gen/`, `core/static/` | Backgrounds, tutorial documents, and application assets served through Django static discovery. |
| Offline calibration | `png_movement/math_context/` | Line evidence, math explanations, review images, and manually invoked calibration scripts. Scripts generate room profiles; server runtime never imports this directory. |
| Separate legacy page | `templates/core/old-map.html`, `static/core/old-map/` | `/old-map/` has its own Blockly app, engine, renderer, generator, and levels; it is not the active screen flow. |
| Unwired tutor helper | `core/tutorial_ai.py` | Ollama question-answer helper; no current URL/view calls it. The live tutorial panel displays Markdown. |
| Build | `vite.config.js` | Bundles `screen_app.js` and `old-map_app.js` into their `dist/` directories and shared chunks. `@png-movement` resolves to the existing movement folder. |
| Verification | `core/test*.py`, feature `test_png_move.py`, `jstests/` | Python and JavaScript checks; these are outside normal request/animation flow. |

## Main responsibilities

- `lessons.py`: existing lesson behavior, requirements, starting state, blocks, and visual associations.
- `lesson_runner.py`: the existing typed-assignment evaluator, unchanged by the movement feature.
- `png_move.py`: server geometry and data composition, despite being under `static/`.
- `png_move.js`: the browser coordinator, with functions for image setup, drawing, translation, Run attempts, projection, and cleanup.
- `load_room_floor()`: returns a composed plane **and motion** payload, not only floor geometry.
- `rooms.py`: room creation and boss assignment as well as runtime navigation/state.

The browser's single entry point is `initializeMovement()`. Its helper functions live in the same file.
