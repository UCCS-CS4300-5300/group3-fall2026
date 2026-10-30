from django.core.exceptions import ValidationError
from django.db import models

class Mission(models.Model):
    title=models.CharField(max_length=120)
    description=models.TextField(blank=True)
    instructions=models.TextField(blank=True)
    # Blank missions have no automatic boss; configured missions use their final room.
    boss_lesson_id = models.CharField("Boss LessonID", max_length=100, blank=True, default="")
    tutorials_unlocked = models.BooleanField(default=False)
    first_room = models.ForeignKey(
        "RoomDefinition", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="first_for_missions",
    )
    current_room = models.ForeignKey(
        "RoomDefinition", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="current_for_missions",
    )

    @property
    def mission_id(self) -> int:
        return self.pk

    @property
    def room_states(self):
        return RoomState.objects.filter(room__mission=self)

    def clean(self):
        super().clean()
        for field in ("first_room", "current_room"):
            if getattr(self, f"{field}_id") and getattr(self, field).mission_id != self.pk:
                raise ValidationError({field: "Room must belong to this mission."})

    def __str__(self):
        return self.title

class Puzzle(models.Model):
    mission = models.OneToOneField(
        Mission,
        on_delete=models.CASCADE, # this is kinda risky for current implementation, maybe rethink how relationship is defined
        related_name="puzzle",
    )

    # The intended block program, one block per line, indented for nesting
    solution = models.TextField(blank=True)
    # Plain-language checks for the student's code, e.g.
    # [{"action": "Punch zombie", "check": "Was zombie punched?"}]
    tests = models.JSONField(default=list, blank=True)
    # Room ID (or "mission" for a roomless mission) -> Blockly workspace JSON.
    workspace_state = models.JSONField(default=dict, blank=True)

    # Possible members of a puzzle class, for Jigmi to decide:
    # level = models.IntegerField()
    # available_blocks = models.JSONField(default=list)

    def __str__(self):
        return f"Puzzle for {self.mission.title}"


class RoomDefinition(models.Model):
    room_id = models.BigAutoField(primary_key=True)
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="rooms")
    background_asset_path = models.CharField(max_length=500)
    next_room = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="previous_rooms",
    )
    tutorial_document_path = models.CharField(max_length=500)
    # ID in lessons.LESSONS; blank rooms keep the existing mission puzzle.
    lesson_id = models.CharField("LessonID", max_length=100, blank=True, default="")
    # lesson_id in core/exercises/exercises.json; blank rooms show no exercises.
    exercise_set_id = models.CharField(max_length=100, blank=True, default="")

    def clean(self):
        super().clean()
        if self.next_room_id and self.next_room.mission_id != self.mission_id:
            raise ValidationError({"next_room": "Next room must belong to the same mission."})


class RoomState(models.Model):
    room = models.OneToOneField(
        RoomDefinition, primary_key=True, on_delete=models.CASCADE,
        related_name="room_state",
    )
    tutorial_read = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    # LessonID and requirements persist across retries; mission reset clears them.
    encounter_state = models.JSONField(default=dict, blank=True)
