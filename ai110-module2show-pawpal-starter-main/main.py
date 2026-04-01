from datetime import date

from pawpal_system import Owner, Pet, Task, Scheduler


def print_schedule(plan: dict) -> None:
    print("\n=== TODAY'S SCHEDULE ===")
    print(f"Used time: {plan['used_minutes']} / {plan['max_minutes']} minutes\n")

    if not plan["selected"]:
        print("No tasks selected for today.")
    else:
        for pet, task in plan["selected"]:
            print(
                f"{task.due_time} | {pet.name} | {task.title} | "
                f"{task.duration_minutes} min | {task.priority}"
            )

    if plan["conflicts"]:
        print("\n=== CONFLICT WARNINGS ===")
        for warning in plan["conflicts"]:
            print(f"- {warning}")

    if plan["skipped"]:
        print("\n=== SKIPPED TASKS ===")
        for pet, task in plan["skipped"]:
            print(
                f"- {task.title} for {pet.name} skipped "
                f"({task.duration_minutes} min, {task.priority})"
            )

    print("\n=== EXPLANATION ===")
    for line in plan["explanation"]:
        print(f"- {line}")


def main() -> None:
    owner = Owner(name="Jordan", time_available_minutes=60, preferences="Morning care first")

    mochi = Pet(name="Mochi", species="dog", age=3, preferences="Loves walks")
    luna = Pet(name="Luna", species="cat", age=2, preferences="Needs calm routine")

    owner.add_pet(mochi)
    owner.add_pet(luna)

    today = date.today()

    mochi.add_task(Task("Morning walk", 20, "high", "08:00", "daily", due_date=today))
    mochi.add_task(Task("Breakfast", 10, "high", "07:30", "daily", due_date=today))
    luna.add_task(Task("Medication", 5, "high", "08:00", "daily", due_date=today))
    luna.add_task(Task("Play session", 25, "medium", "09:00", "once", due_date=today))

    scheduler = Scheduler(owner)
    plan = scheduler.generate_daily_plan(today)
    print_schedule(plan)


if __name__ == "__main__":
    main()