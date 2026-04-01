from datetime import date, timedelta

from pawpal_system import Owner, Pet, Task, Scheduler


def make_scheduler():
    owner = Owner(name="Test Owner", time_available_minutes=60)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)
    return owner, pet, Scheduler(owner)


def test_mark_complete_changes_status():
    owner, pet, scheduler = make_scheduler()
    today = date.today()

    task = Task("Feed", 10, "high", "08:00", "once", due_date=today)
    pet.add_task(task)

    result = scheduler.mark_task_complete("Mochi", "Feed", today)

    assert result is True
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Luna", species="cat")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Brush", 15, "medium", "10:00"))

    assert len(pet.tasks) == 1


def test_sorting_returns_tasks_in_chronological_order():
    owner = Owner(name="Test", time_available_minutes=120)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    today = date.today()
    pet.add_task(Task("Late Task", 10, "low", "18:00", due_date=today))
    pet.add_task(Task("Early Task", 10, "high", "07:00", due_date=today))
    pet.add_task(Task("Mid Task", 10, "medium", "12:00", due_date=today))

    scheduler = Scheduler(owner)
    tasks = scheduler.sort_tasks(owner.get_all_tasks_for_date(today))

    ordered_titles = [task.title for _, task in tasks]
    assert ordered_titles == ["Early Task", "Mid Task", "Late Task"]


def test_daily_recurrence_creates_next_day_task():
    owner, pet, scheduler = make_scheduler()
    today = date.today()

    task = Task("Morning Walk", 20, "high", "08:00", "daily", due_date=today)
    pet.add_task(task)

    scheduler.mark_task_complete("Mochi", "Morning Walk", today)

    next_day = today + timedelta(days=1)
    future_tasks = [t for t in pet.tasks if t.due_date == next_day and t.title == "Morning Walk"]

    assert len(future_tasks) == 1
    assert future_tasks[0].completed is False


def test_weekly_recurrence_creates_next_week_task():
    owner, pet, scheduler = make_scheduler()
    today = date.today()

    task = Task("Grooming", 30, "medium", "11:00", "weekly", due_date=today)
    pet.add_task(task)

    scheduler.mark_task_complete("Mochi", "Grooming", today)

    next_week = today + timedelta(weeks=1)
    future_tasks = [t for t in pet.tasks if t.due_date == next_week and t.title == "Grooming"]

    assert len(future_tasks) == 1


def test_conflict_detection_flags_duplicate_times():
    owner = Owner(name="Test", time_available_minutes=120)
    dog = Pet(name="Mochi", species="dog")
    cat = Pet(name="Luna", species="cat")
    owner.add_pet(dog)
    owner.add_pet(cat)

    today = date.today()
    dog.add_task(Task("Walk", 20, "high", "08:00", due_date=today))
    cat.add_task(Task("Medication", 5, "high", "08:00", due_date=today))

    scheduler = Scheduler(owner)
    conflicts = scheduler.detect_conflicts(owner.get_all_tasks_for_date(today))

    assert len(conflicts) == 1
    assert "08:00" in conflicts[0]


def test_schedule_respects_time_limit():
    owner = Owner(name="Test", time_available_minutes=20)
    pet = Pet(name="Mochi", species="dog")
    owner.add_pet(pet)

    today = date.today()
    pet.add_task(Task("Walk", 15, "high", "08:00", due_date=today))
    pet.add_task(Task("Play", 15, "medium", "09:00", due_date=today))

    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan(today)

    assert len(plan["selected"]) == 1
    assert len(plan["skipped"]) == 1