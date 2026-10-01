from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# Map levels live in core/static/core/map/levels.js (MAP_LEVELS has 10 entries).
MAP_LEVEL_COUNT = 10


class Mission(models.Model):
    """A run out of camp: a small tree of Nodes the player walks through."""

    title = models.CharField(max_length=120)
    summary = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    start_node = models.ForeignKey(
        "Node", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title

    def clean(self):
        if self.start_node_id and self.start_node.mission_id != self.pk:
            raise ValidationError({"start_node": "Start node must belong to this mission."})


class Node(models.Model):
    """One stop in a mission: a scene, an optional code challenge, and Left/Right choices.

    A node with a map_level is a challenge: its choices appear only after the
    player solves that map level. A node with no choices ends the mission.
    """

    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="nodes")
    title = models.CharField(max_length=120)
    scene = models.TextField(help_text="What the close-up picture shows.")
    image_url = models.CharField(max_length=300, blank=True)
    prompt = models.TextField(help_text="What the player is asked to do here.")
    map_level = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(MAP_LEVEL_COUNT)],
        help_text="Map level the player must solve before choosing. Leave blank for story-only nodes.",
    )
    success_text = models.TextField(blank=True, help_text="Shown after the challenge is solved.")

    class Meta:
        ordering = ["mission", "id"]

    def __str__(self):
        return f"{self.mission}: {self.title}"

    @property
    def is_challenge(self):
        return self.map_level is not None

    @property
    def is_end(self):
        return not self.choices.exists()

    def to_dict(self):
        return {
            "id": self.id,
            "mission": self.mission_id,
            "title": self.title,
            "scene": self.scene,
            "image_url": self.image_url,
            "prompt": self.prompt,
            "challenge": {"type": "map", "level": self.map_level} if self.is_challenge else None,
            "success_text": self.success_text,
            "choices": [choice.to_dict() for choice in self.choices.all()],
            "is_end": self.is_end,
        }


class Choice(models.Model):
    LEFT = "left"
    RIGHT = "right"
    SIDES = [(LEFT, "Left"), (RIGHT, "Right")]

    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="choices")
    side = models.CharField(max_length=5, choices=SIDES)
    label = models.CharField(max_length=120)
    next_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="incoming_choices")

    class Meta:
        ordering = ["node", "side"]
        constraints = [models.UniqueConstraint(fields=["node", "side"], name="one_choice_per_side")]

    def __str__(self):
        return f"{self.node.title} -> {self.get_side_display()}: {self.label}"

    def clean(self):
        if self.node_id and self.next_node_id and self.node.mission_id != self.next_node.mission_id:
            raise ValidationError({"next_node": "Next node must be in the same mission."})

    def to_dict(self):
        return {"id": self.id, "side": self.side, "label": self.label, "next_node": self.next_node_id}
