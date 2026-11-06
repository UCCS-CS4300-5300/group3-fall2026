# Zombie Room Tutorials

One tutorial document per lesson and jumpscare room (boss rooms have none), in Python, written to match the exercise sets in `project/core/exercises/exercises.json`. Topics follow the [w3resource Python tutorial](https://www.w3resource.com/python/python-tutorial.php) and [Python exercises](https://www.w3resource.com/python-exercises/).

Each file is named after the room's background image, the same way the seed migration (`0007_seed_buildings.py`) builds `tutorial_document_path` (`tutorials/<image>.md`). To use them in the game, copy them to `project/gen/tutorials/` (or `project/assets/tutorials/`) so they are served at `/static/tutorials/<image>.md`.

The files use only the Markdown the in-game tutorial panel renders: headings, paragraphs, lists, block quotes, code fences and inline code, bold and links. They contain no tables.

Lesson rooms cover what you'll learn, the concept with examples, and common mistakes. Jumpscare rooms cover how to debug, bugs to look for, and a checklist.

## 1. The Corner Store (Variables & Data Types)
- [Variables Room](corner_store_room1_variables.md)
- [Data Types Room](corner_store_room2_data_types.md)
- [Operators Room](corner_store_room3_operators.md)
- [Jumpscare: The Cashier](corner_store_jumpscare_room.md)

## 2. The Police Station (Conditionals)
- [If/Else Room](police_station_room1_if_else_alt.md)
- [Else-If Room](police_station_room2_else_if.md)
- [Switch Room](police_station_room3_switch.md)
- [Logic Room](police_station_room4_logic.md) (not in the current seed)
- [Jumpscare: The Patrol Officer](police_station_jumpscare_room.md)

## 3. The Laundromat (Loops)
- [For Room](laundromat_room1_for.md)
- [While Room](laundromat_room2_while.md)
- [Do-While Room](laundromat_room3_do_while.md)
- [Jumpscare: The Spinning Drum](laundromat_jumpscare_zombie.md)

## 4. The Morgue (Arrays)
- [Indexing Room](morgue_room1_indexing_alt.md)
- [Traversal Room](morgue_room2_traversal.md)
- [Modifying Room](morgue_room3_modifying.md)
- [Jumpscare: The Body Bag](morgue_jumpscare_room.md)

## 5. The Radio Station (Strings)
- [Concatenation Room](radio_station_room1_concatenation.md)
- [Indexing Room](radio_station_room2_indexing.md)
- [Slicing Room](radio_station_room3_slicing.md) (not in the current seed)
- [Methods Room](radio_station_room4_methods.md)
- [Jumpscare: The Night DJ](radio_station_jumpscare_room.md)

## 6. The Diner (Functions)
- [Define & Call Room](diner_room1_define_and_call.md)
- [Parameters & Return Room](diner_room2_parameters_and_return.md)
- [Scope Room](diner_room3_scope.md)
- [Jumpscare: The Short-Order Cook](diner_jumpscare_zombie.md)

## 7. The Hotel (Dictionaries / Maps)
- [Key-Value Room (Lobby)](hotel_room1_lobby.md)
- [Updating Room (Stairwell)](hotel_room2_stairwell.md)
- [Iteration Room (Hallway)](hotel_room3_hallway.md)
- [Jumpscare: The Mail Carrier](hotel_jumpscare_room.md)

## 8. The Factory (Classes & Objects)
- [Classes & Objects Room](factory_room1_classes_and_objects.md)
- [Constructors & Methods Room](factory_room2_constructors_and_methods.md)
- [Inheritance Room](factory_room3_inheritance.md)
- [Jumpscare: The Assembly-Line Turret](factory_jumpscare_zombie.md)

## 9. The Funhouse (Recursion)
- [Base Case Room](funhouse_room1_base_case.md)
- [Call Stack Room](funhouse_room2_call_stack.md)
- [Recursive Problems Room](funhouse_room3_recursive_problems.md)
- [Jumpscare: The Clown](funhouse_jumpscare_zombie.md)

## 10. The Hospital (Searching & Sorting)
- [Linear Search Room](hospital_room1_linear_search.md)
- [Binary Search Room](hospital_room2_binary_search.md)
- [Sorting Room (Microscope Lab)](hospital_room4_microscope_lab.md)
- [Jumpscare: The Night Nurse](hospital_jumpscare_room.md)
