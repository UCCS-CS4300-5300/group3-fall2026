# Zombie

Zombie is a game that teaches programming. The world has ended, the streets belong to the undead, and the only way to survive is to learn to code. Players explore an abandoned street, clear buildings room by room, and fight zombies by writing and fixing real code.

## How to Run the Game

### Requirements

- [Python 3.12](https://www.python.org/downloads/)
- [Node.js](https://nodejs.org/) (includes `npm`)

### First-time setup

Run these commands from the repository root.

**macOS / Linux**

```bash
cd project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
npm run build
python manage.py migrate
python manage.py runserver
```

**Windows (PowerShell)**

```powershell
cd project
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
npm.cmd install
npm.cmd run build
python manage.py migrate
python manage.py runserver
```

Then open **http://127.0.0.1:8000/** in your browser to play.

### Playing again later

You only need to do the setup once. After that, start the game with:

**macOS / Linux**

```bash
cd project
source .venv/bin/activate
python manage.py runserver
```

**Windows (PowerShell)**

```powershell
cd project
.venv\Scripts\Activate.ps1
python manage.py runserver
```

Press `Ctrl+C` in the terminal to stop the server.

> If you pull new changes, run `pip install -r requirements.txt`, `npm install`, `npm run build`, and `python manage.py migrate` again before starting the server.

### Optional: AI tutor

The in-game tutor uses [Groq](https://console.groq.com/). To turn it on, set your API key before running the server:

```bash
export GROQ_API_KEY=your-key-here          # macOS / Linux
```

```powershell
$env:GROQ_API_KEY = "your-key-here"        # Windows (PowerShell)
```

The rest of the game works without it.

## Running Tests

Run these commands from the `project` folder:

```bash
cd project
pytest        # Python tests
npm test      # JavaScript tests (Vitest); use npm.cmd test on Windows
```

To run a single JavaScript test file:

```bash
npx vitest run jstests/blockly_integer_input.test.js
```

## The Street

The game’s hub is a ruined street lined with ten buildings. Each building is dedicated to one programming concept, such as loops, conditional statements, or inheritance. The player picks a building and enters it to begin.

<p align="center">
  <img src="project/assets/images/Street/street.jpeg" alt="The Street" width="100%"><br>
  <em>The Street</em>
</p>

## Buildings and Rooms

- Every building has four or more rooms, and each room teaches one topic within that building’s concept.
- Every room contains one tutorial and one or more coding exercises.
- Exercises are hidden in the scene: the player clicks objects in the room, such as a flickering terminal, a radio, or a survivor’s journal, to activate them.
- Each room has a door that leads to the next room once the player is ready.

## Zombies

**The Jumpscare Zombie:** Hidden in one room of every building, this zombie bursts out without warning. To survive, the player must quickly debug broken code.

**The Boss Zombie:** Waiting in the final room of every building, the boss is defeated by writing code that uses everything the player learned in that building’s rooms.

## Building Map

| # | Building | Concept | Room 1 | Room 2 | Room 3 | Room 4 | Boss Room | Jump Scare | Total |
|---|---|---|---|---|---|---|:-:|:-:|:-:|
| 1 | The Corner Store | Variables & Data Types | Variables Room | Data Types Room | Operators Room | - | 1 | 1 | 5 |
| 2 | The Police station | Conditionals | If/Else Room | Else-If | Switch Room | Logic Room | 1 | 1 | 6 |
| 3 | The Laundromat | Loops | For Room | While Room | Do-While Room | - | 1 | 1 | 5 |
| 4 | The Morgue | Arrays | Indexing Room | Traversal Room | Modifying Room | - | 1 | 1 | 5 |
| 5 | The Radio Station | Strings | Concatenation Room | Indexing | Slicing Room | Methods Room | 1 | 1 | 6 |
| 6 | The Diner | Functions | Define & Call Room | Parameters & Return Room | Scope Room | - | 1 | 1 | 5 |
| 7 | The Hotel | Dictionaries / Maps | Key-Value Room | Updating Room | Iteration Room | - | 1 | 1 | 5 |
| 8 | The Factory | Classes & Objects | Classes & Objects Room | Constructors & Methods Room | Inheritance Room | - | 1 | 1 | 5 |
| 9 | The Funhouse | Recursion | Base Case Room | Call Stack Room | Recursive Problems Room | - | 1 | 1 | 5 |
| 10 | The Hospital | Searching & Sorting | Linear Search Room | Binary Search Room | Sorting Room | - | 1 | 1 | 5 |
| | **TOTAL** | | **10** | **10** | **10** | **2** | **10** | **10** | **52** |

## Buildings

### 1. The Corner Store (Variables & Data Types)

<table>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Corner%20Store/corner_store_room1_variables.jpeg" alt="The Corner Store: Room 1: Variables" width="100%"><br>
      <em>Room 1: Variables</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Corner%20Store/corner_store_room2_data_types.jpeg" alt="The Corner Store: Room 2: Data Types" width="100%"><br>
      <em>Room 2: Data Types</em>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Corner%20Store/corner_store_room3_operators.jpeg" alt="The Corner Store: Room 3: Operators" width="100%"><br>
      <em>Room 3: Operators</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Corner%20Store/corner_store_boss_zombie.jpeg" alt="The Corner Store: Boss Zombie" width="100%"><br>
      <em>Boss Zombie</em>
    </td>
  </tr>
</table>

### 2. The Police station (Conditionals)

<table>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Police%20station/police_station_room1_if_else_alt.jpeg" alt="The Police station: Room 1: If/Else" width="100%"><br>
      <em>Room 1: If/Else</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Police%20station/police_station_room2_else_if.jpeg" alt="The Police station: Room 2: Else-If" width="100%"><br>
      <em>Room 2: Else-If</em>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Police%20station/police_station_room3_switch.jpeg" alt="The Police station: Room 3: Switch" width="100%"><br>
      <em>Room 3: Switch</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Police%20station/police_station_boss_zombie.jpeg" alt="The Police station: Boss Zombie" width="100%"><br>
      <em>Boss Zombie</em>
    </td>
  </tr>
</table>

### 3. The Laundromat (Loops)

<table>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Laundromat/laundromat_room1_for.jpeg" alt="The Laundromat: Room 1: For" width="100%"><br>
      <em>Room 1: For</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Laundromat/laundromat_room2_while.jpeg" alt="The Laundromat: Room 2: While" width="100%"><br>
      <em>Room 2: While</em>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Laundromat/laundromat_room3_do_while.jpeg" alt="The Laundromat: Room 3: Do-While" width="100%"><br>
      <em>Room 3: Do-While</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Laundromat/laundromat_boss_zombie.jpeg" alt="The Laundromat: Boss Zombie" width="100%"><br>
      <em>Boss Zombie</em>
    </td>
  </tr>
</table>

### 4. The Morgue (Arrays)

<table>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Morgue/morgue_room1_indexing_alt.jpeg" alt="The Morgue: Room 1: Indexing" width="100%"><br>
      <em>Room 1: Indexing</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Morgue/morgue_room2_traversal.jpeg" alt="The Morgue: Room 2: Traversal" width="100%"><br>
      <em>Room 2: Traversal</em>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Morgue/morgue_room3_modifying.jpeg" alt="The Morgue: Room 3: Modifying" width="100%"><br>
      <em>Room 3: Modifying</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Morgue/morgue_jumpscare_zombie.jpeg" alt="The Morgue: Jump Scare Zombie" width="100%"><br>
      <em>Jump Scare Zombie</em>
    </td>
  </tr>
</table>

### 5. The Radio Station (Strings)

<table>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Radio%20Station/radio_station_room1_concatenation.jpeg" alt="The Radio Station: Room 1: Concatenation" width="100%"><br>
      <em>Room 1: Concatenation</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Radio%20Station/radio_station_room2_indexing.jpeg" alt="The Radio Station: Room 2: Indexing" width="100%"><br>
      <em>Room 2: Indexing</em>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Radio%20Station/radio_station_room4_methods.jpeg" alt="The Radio Station: Room 4: Methods" width="100%"><br>
      <em>Room 4: Methods</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Radio%20Station/radio_station_boss_zombie.jpeg" alt="The Radio Station: Boss Zombie" width="100%"><br>
      <em>Boss Zombie</em>
    </td>
  </tr>
</table>

### 6. The Diner (Functions)

<table>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Diner/diner_room1_define_and_call.jpeg" alt="The Diner: Room 1: Define &amp; Call" width="100%"><br>
      <em>Room 1: Define &amp; Call</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Diner/diner_room2_parameters_and_return.jpeg" alt="The Diner: Room 2: Parameters &amp; Return" width="100%"><br>
      <em>Room 2: Parameters &amp; Return</em>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Diner/diner_room3_scope.jpeg" alt="The Diner: Room 3: Scope" width="100%"><br>
      <em>Room 3: Scope</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Diner/diner_boss_zombie.jpeg" alt="The Diner: Boss Zombie" width="100%"><br>
      <em>Boss Zombie</em>
    </td>
  </tr>
</table>

### 7. The Hotel (Dictionaries / Maps)

<table>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Hotel/hotel_room1_lobby.jpeg" alt="The Hotel: Room 1: Key-Value (Lobby)" width="100%"><br>
      <em>Room 1: Key-Value (Lobby)</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Hotel/hotel_room2_stairwell.jpeg" alt="The Hotel: Room 2: Updating (Stairwell)" width="100%"><br>
      <em>Room 2: Updating (Stairwell)</em>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Hotel/hotel_room3_hallway.jpeg" alt="The Hotel: Room 3: Iteration (Hallway)" width="100%"><br>
      <em>Room 3: Iteration (Hallway)</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Hotel/hotel_boss_zombie.jpeg" alt="The Hotel: Boss Zombie" width="100%"><br>
      <em>Boss Zombie</em>
    </td>
  </tr>
</table>

### 8. The Factory (Classes & Objects)

<table>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Factory/factory_room1_classes_and_objects.jpeg" alt="The Factory: Room 1: Classes &amp; Objects" width="100%"><br>
      <em>Room 1: Classes &amp; Objects</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Factory/factory_room2_constructors_and_methods.jpeg" alt="The Factory: Room 2: Constructors &amp; Methods" width="100%"><br>
      <em>Room 2: Constructors &amp; Methods</em>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Factory/factory_room3_inheritance.jpeg" alt="The Factory: Room 3: Inheritance" width="100%"><br>
      <em>Room 3: Inheritance</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Factory/factory_boss_zombie.jpeg" alt="The Factory: Boss Zombie" width="100%"><br>
      <em>Boss Zombie</em>
    </td>
  </tr>
</table>

### 9. The Funhouse (Recursion)

<table>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Funhouse/funhouse_room1_base_case.jpeg" alt="The Funhouse: Room 1: Base Case" width="100%"><br>
      <em>Room 1: Base Case</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Funhouse/funhouse_room2_call_stack.jpeg" alt="The Funhouse: Room 2: Call Stack" width="100%"><br>
      <em>Room 2: Call Stack</em>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Funhouse/funhouse_room3_recursive_problems.jpeg" alt="The Funhouse: Room 3: Recursive Problems" width="100%"><br>
      <em>Room 3: Recursive Problems</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Funhouse/funhouse_boss_zombie.jpeg" alt="The Funhouse: Boss Zombie" width="100%"><br>
      <em>Boss Zombie</em>
    </td>
  </tr>
</table>

### 10. The Hospital (Searching & Sorting)

<table>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Hospital/hospital_room1_linear_search.jpeg" alt="The Hospital: Room 1: Linear Search" width="100%"><br>
      <em>Room 1: Linear Search</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Hospital/hospital_room2_binary_search.jpeg" alt="The Hospital: Room 2: Binary Search" width="100%"><br>
      <em>Room 2: Binary Search</em>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Hospital/hospital_room4_microscope_lab.jpeg" alt="The Hospital: Microscope Lab" width="100%"><br>
      <em>Microscope Lab</em>
    </td>
    <td width="50%" align="center">
      <img src="project/assets/images/The%20Hospital/hospital_jumpscare_zombie.jpeg" alt="The Hospital: Jump Scare Zombie" width="100%"><br>
      <em>Jump Scare Zombie</em>
    </td>
  </tr>
</table>

---
