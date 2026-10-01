from django.db import migrations

# Each mission is a small tree: a story node with a Left/Right choice, two
# challenge branches, two final challenges, then a story-only end node back
# at camp. Map levels climb in difficulty across the three missions.
GOAL = "Guide the survivor (blue arrow) to the red marker."

MISSIONS = [
    {
        "title": "Pharmacy Run",
        "summary": "Camp is out of bandages. Scavenge the corner pharmacy before nightfall.",
        "start": "outside",
        "nodes": {
            "outside": {
                "title": "Outside the Pharmacy",
                "scene": "Rusted shutters, a chained front door, and a CLOSED sign swinging in the wind. Something shuffles around inside.",
                "prompt": "The front door won't budge. How do you get in?",
                "choices": [("left", "Try the alley door", "alley"), ("right", "Climb through the broken window", "window")],
            },
            "alley": {
                "title": "The Alley",
                "scene": "A narrow alley littered with trash bags. The side door is only a few steps ahead.",
                "prompt": f"Walk straight to the side door. {GOAL}",
                "map_level": 1,
                "success_text": "The side door creaks open and you slip into the stockroom.",
                "choices": [("left", "Search the stockroom shelves", "shelves"), ("right", "Sneak to the pharmacy counter", "counter")],
            },
            "window": {
                "title": "The Broken Window",
                "scene": "Glass crunches underfoot. A toppled display blocks the straight path, so you will have to step around it.",
                "prompt": f"Move, turn, and move again to get around the display. {GOAL}",
                "map_level": 2,
                "success_text": "You squeeze past the display and drop down behind the shop counter.",
                "choices": [("left", "Search the stockroom shelves", "shelves"), ("right", "Sneak to the pharmacy counter", "counter")],
            },
            "shelves": {
                "title": "Stockroom Shelves",
                "scene": "One long aisle of half-empty shelves. You can only keep a couple of instructions in your head at once.",
                "prompt": f"Use a repeat block so two blocks carry you down the whole aisle. {GOAL}",
                "map_level": 3,
                "success_text": "Bandages, gauze, and a bottle of antiseptic. Your pack is full.",
                "choices": [("left", "Head back to camp", "camp")],
            },
            "counter": {
                "title": "Pharmacy Counter",
                "scene": "A long hallway of locked cabinets leads to the medicine safe. Something groans behind you, so keep the plan short.",
                "prompt": f"Repeat a single move to reach the safe using only two blocks. {GOAL}",
                "map_level": 3,
                "success_text": "The safe swings open. Antibiotics! Time to go.",
                "choices": [("left", "Head back to camp", "camp")],
            },
            "camp": {
                "title": "Back at Camp",
                "scene": "You slip through the gate as the sun sets. The camp medic grins at the sight of your pack.",
                "prompt": "Mission complete. The camp has medical supplies again.",
            },
        },
    },
    {
        "title": "Radio Tower",
        "summary": "A crackling signal came from the old radio tower. Find out who is broadcasting.",
        "start": "park",
        "nodes": {
            "park": {
                "title": "Edge of the Park",
                "scene": "The radio tower blinks on the far side of an overgrown park. Smoke drifts up from the main road.",
                "prompt": "Which route do you take?",
                "choices": [("left", "Cut through the park", "tents"), ("right", "Follow the main road", "road")],
            },
            "tents": {
                "title": "Tent City",
                "scene": "Abandoned tents are pitched in a zig-zag. Step, turn, step, turn, and don't brush the canvas.",
                "prompt": f"Find the repeating pattern in the zig-zag and loop it. {GOAL}",
                "map_level": 4,
                "success_text": "You weave between the tents without a sound and reach the tower fence.",
                "choices": [("left", "Climb the service ladder", "ladder"), ("right", "Take the stairwell", "stairwell")],
            },
            "road": {
                "title": "Main Road",
                "scene": "Burned-out cars line the road. Walk to the corner, then it's a long, straight stretch north to the tower gate.",
                "prompt": f"Get to the corner, turn, then loop the long stretch north. {GOAL}",
                "map_level": 5,
                "success_text": "The tower gate hangs open. Someone has been here recently.",
                "choices": [("left", "Climb the service ladder", "ladder"), ("right", "Take the stairwell", "stairwell")],
            },
            "ladder": {
                "title": "Service Ladder",
                "scene": "Ladder platforms wind around the tower. At every landing you have to check which way the walkway goes.",
                "prompt": f"Use an if block to turn whenever the path bends. {GOAL}",
                "map_level": 6,
                "success_text": "At the top, a radio sits on a crate, still warm. The broadcast is a recording that repeats a set of coordinates.",
                "choices": [("left", "Head back to camp", "camp")],
            },
            "stairwell": {
                "title": "Stairwell",
                "scene": "The stairwell is pitch black and twists in every direction. Feel along the wall and turn when it turns.",
                "prompt": f"Use an if block to turn whenever the path bends. {GOAL}",
                "map_level": 6,
                "success_text": "You burst into the control room. The radio is looping a message with a set of coordinates.",
                "choices": [("left", "Head back to camp", "camp")],
            },
            "camp": {
                "title": "Back at Camp",
                "scene": "You copy down the coordinates and hurry home. The whole camp crowds around the map to plan the next trip.",
                "prompt": "Mission complete. You found a lead on other survivors.",
            },
        },
    },
    {
        "title": "Hospital Generator",
        "summary": "The hospital's backup generator could power camp for a month. Getting to it won't be easy.",
        "start": "entrance",
        "nodes": {
            "entrance": {
                "title": "Hospital Entrance",
                "scene": "Ambulances block the drive. The lobby doors hang open and the lights flicker on and off.",
                "prompt": "Where do you go in?",
                "choices": [("left", "Through the ambulance bay", "bay"), ("right", "Through the main lobby", "lobby")],
            },
            "bay": {
                "title": "Ambulance Bay",
                "scene": "Stretchers and dead ends everywhere. Some corridors loop right back on themselves.",
                "prompt": f"Check for a path before you turn; dead ends are deadly here. {GOAL}",
                "map_level": 7,
                "success_text": "You find the service corridor hidden behind the bay.",
                "choices": [("left", "Take the basement stairs", "basement"), ("right", "Climb down the elevator shaft", "shaft")],
            },
            "lobby": {
                "title": "Main Lobby",
                "scene": "Overturned chairs form a maze across the waiting room, and zombies in scrubs wander between them.",
                "prompt": f"Put if blocks inside a repeat loop to thread the maze. {GOAL}",
                "map_level": 8,
                "success_text": "You slip past the waiting room to a door marked AUTHORIZED PERSONNEL.",
                "choices": [("left", "Take the basement stairs", "basement"), ("right", "Climb down the elevator shaft", "shaft")],
            },
            "basement": {
                "title": "Basement",
                "scene": "Pipes hiss in the dark and the corridor splits again and again.",
                "prompt": f"Combine loops and if blocks to find your way to the generator. {GOAL}",
                "map_level": 9,
                "success_text": "The generator coughs, then roars to life. Light floods the basement.",
                "choices": [("left", "Head back to camp", "camp")],
            },
            "shaft": {
                "title": "Elevator Shaft",
                "scene": "Maintenance catwalks crisscross the shaft. One wrong turn and it's a long way down.",
                "prompt": f"Use if/else to decide every single step. {GOAL}",
                "map_level": 10,
                "success_text": "You reach the generator room from above and throw the main breaker. The whole hospital hums.",
                "choices": [("left", "Head back to camp", "camp")],
            },
            "camp": {
                "title": "Back at Camp",
                "scene": "You roll a portable generator home on a shopping cart. Tonight, the camp has light.",
                "prompt": "Mission complete. The camp has power.",
            },
        },
    },
]


def seed_missions(apps, schema_editor):
    Mission = apps.get_model("missions", "Mission")
    Node = apps.get_model("missions", "Node")
    Choice = apps.get_model("missions", "Choice")

    for order, data in enumerate(MISSIONS, start=1):
        mission = Mission.objects.create(title=data["title"], summary=data["summary"], order=order)
        nodes = {
            key: Node.objects.create(
                mission=mission,
                title=node["title"],
                scene=node["scene"],
                prompt=node["prompt"],
                map_level=node.get("map_level"),
                success_text=node.get("success_text", ""),
            )
            for key, node in data["nodes"].items()
        }
        for key, node in data["nodes"].items():
            for side, label, next_key in node.get("choices", []):
                Choice.objects.create(node=nodes[key], side=side, label=label, next_node=nodes[next_key])
        mission.start_node = nodes[data["start"]]
        mission.save()


def remove_missions(apps, schema_editor):
    Mission = apps.get_model("missions", "Mission")
    Mission.objects.filter(title__in=[data["title"] for data in MISSIONS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("missions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_missions, remove_missions),
    ]
