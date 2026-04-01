from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Optional


PRIORITY_RANK = {
    "high": 3,
    "medium": 2,
    "low": 1,
}


@dataclass
class Task:
    """Represents a single pet care task."""

    title: str
    duration_minutes: int
    priority: str
    due_time: str
    frequency: str = "once"
    notes: str = ""
    due_date: date = field(default_factory=date.today)
    completed: bool = False

    def mark_complete(self) -> None:
        """Marks the task as completed."""
        self.completed = True

    def recurrence_copy(self) -> Optional["Task"]:
        """Creates the next occurrence of a recurring task."""
        if self.frequency == "daily":
            next_date = self.due_date + timedelta(days=1)
        elif self.frequency == "weekly":
            next_date = self.due_date + timedelta(weeks=1)
        else:
            return None

        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            due_time=self.due_time,
            frequency=self.frequency,
            notes=self.notes,
            due_date=next_date,
            completed=False,
        )

    def priority_score(self) -> int:
        """Returns a numeric score for task priority."""
        return PRIORITY_RANK.get(self.priority.lower(), 1)

    def time_key(self) -> datetime:
        """Returns a sortable datetime for the task."""
        return datetime.strptime(self.due_time, "%H:%M")

    def to_dict(self, pet_name: str) -> dict:
        """Converts the task into a dictionary for display."""
        return {
            "pet": pet_name,
            "task": self.title,
            "time": self.due_time,
            "duration": self.duration_minutes,
            "priority": self.priority,
            "frequency": self.frequency,
            "completed": self.completed,
            "reason": f"{self.priority.title()} priority task for {pet_name}",
        }


@dataclass
class Pet:
    """Stores pet details and task list."""

    name: str
    species: str
    age: int = 0
    preferences: str = ""
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Adds a task to the pet."""
        self.tasks.append(task)

    def get_tasks_for_date(self, target_date: Optional[date] = None) -> List[Task]:
        """Returns tasks due on a specific date."""
        target_date = target_date or date.today()
        return [task for task in self.tasks if task.due_date == target_date]

    def incomplete_tasks_for_date(self, target_date: Optional[date] = None) -> List[Task]:
        """Returns incomplete tasks due on a specific date."""
        target_date = target_date or date.today()
        return [
            task for task in self.tasks
            if task.due_date == target_date and not task.completed
        ]


@dataclass
class Owner:
    """Manages the owner and all pets."""

    name: str
    time_available_minutes: int = 120
    preferences: str = ""
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Adds a pet to the owner."""
        self.pets.append(pet)

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Finds a pet by name."""
        for pet in self.pets:
            if pet.name.lower() == pet_name.lower():
                return pet
        return None

    def get_all_tasks_for_date(self, target_date: Optional[date] = None) -> List[tuple[Pet, Task]]:
        """Returns all tasks across all pets for a date."""
        target_date = target_date or date.today()
        all_tasks = []
        for pet in self.pets:
            for task in pet.get_tasks_for_date(target_date):
                all_tasks.append((pet, task))
        return all_tasks


class Scheduler:
    """Builds and manages a daily pet care plan."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def sort_tasks(self, pet_task_pairs: List[tuple[Pet, Task]]) -> List[tuple[Pet, Task]]:
        """Sorts tasks by time first, then by higher priority."""
        return sorted(
            pet_task_pairs,
            key=lambda pair: (pair[1].time_key(), -pair[1].priority_score(), pair[0].name.lower())
        )

    def filter_tasks(
        self,
        pet_task_pairs: List[tuple[Pet, Task]],
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> List[tuple[Pet, Task]]:
        """Filters tasks by pet name and/or completion status."""
        filtered = pet_task_pairs

        if pet_name is not None:
            filtered = [pair for pair in filtered if pair[0].name.lower() == pet_name.lower()]

        if completed is not None:
            filtered = [pair for pair in filtered if pair[1].completed == completed]

        return filtered

    def detect_conflicts(
        self,
        pet_task_pairs: List[tuple[Pet, Task]]
    ) -> List[str]:
        """Detects same-time task conflicts."""
        conflicts = []
        seen = {}

        for pet, task in pet_task_pairs:
            key = (task.due_date, task.due_time)
            seen.setdefault(key, []).append((pet, task))

        for (_, task_time), items in seen.items():
            if len(items) > 1:
                names = ", ".join(f"{pet.name}: {task.title}" for pet, task in items)
                conflicts.append(f"Conflict at {task_time} -> {names}")

        return conflicts

    def generate_daily_plan(self, target_date: Optional[date] = None) -> dict:
        """Generates a daily schedule constrained by available time."""
        target_date = target_date or date.today()

        pairs = self.owner.get_all_tasks_for_date(target_date)
        pairs = self.filter_tasks(pairs, completed=False)
        pairs = self.sort_tasks(pairs)

        selected = []
        skipped = []
        used_minutes = 0
        max_minutes = self.owner.time_available_minutes

        for pet, task in pairs:
            if used_minutes + task.duration_minutes <= max_minutes:
                selected.append((pet, task))
                used_minutes += task.duration_minutes
            else:
                skipped.append((pet, task))

        conflicts = self.detect_conflicts(selected)

        explanation = []
        for pet, task in selected:
            explanation.append(
                f"{task.due_time} - {task.title} for {pet.name} was chosen because it is "
                f"{task.priority} priority and fits within the owner's available time."
            )

        if skipped:
            explanation.append(
                f"{len(skipped)} task(s) were skipped because the owner only has "
                f"{max_minutes} minutes available today."
            )

        return {
            "selected": selected,
            "skipped": skipped,
            "used_minutes": used_minutes,
            "max_minutes": max_minutes,
            "conflicts": conflicts,
            "explanation": explanation,
        }

    def mark_task_complete(self, pet_name: str, task_title: str, target_date: Optional[date] = None) -> bool:
        """Marks a task complete and creates the next recurring task if needed."""
        target_date = target_date or date.today()
        pet = self.owner.get_pet(pet_name)

        if pet is None:
            return False

        for task in pet.tasks:
            if (
                task.title.lower() == task_title.lower()
                and task.due_date == target_date
                and not task.completed
            ):
                task.mark_complete()
                next_task = task.recurrence_copy()
                if next_task is not None:
                    pet.add_task(next_task)
                return True

        return False