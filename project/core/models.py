from django.db import models

class Mission(models.Model):
    title=models.CharField(max_length=120)
    description=models.TextField(blank=True)
    instructions=models.TextField(blank=True)

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

    # Possible members of a puzzle class, for Jigmi to decide:
    # level = models.IntegerField()
    # available_blocks = models.JSONField(default=list)

    def __str__(self):
        return f"Puzzle for {self.mission.title}"
