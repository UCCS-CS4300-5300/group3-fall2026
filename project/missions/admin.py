from django.contrib import admin

from .models import Choice, Mission, Node


class NodeInline(admin.StackedInline):
    model = Node
    extra = 0
    show_change_link = True
    fields = ["title", "map_level"]


class ChoiceInline(admin.TabularInline):
    model = Choice
    fk_name = "node"
    extra = 0
    max_num = 2


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ["title", "order", "is_active", "start_node"]
    list_editable = ["order", "is_active"]
    inlines = [NodeInline]


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ["title", "mission", "map_level"]
    list_filter = ["mission"]
    inlines = [ChoiceInline]
