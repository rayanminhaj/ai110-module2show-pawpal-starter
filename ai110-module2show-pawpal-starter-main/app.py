from datetime import date
import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler


st.set_page_config(page_title="PawPal+", page_icon="🐾")

if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", 120)

owner = st.session_state.owner
scheduler = Scheduler(owner)

st.title("🐾 PawPal+")

# Add pet
st.subheader("Add Pet")
pet_name = st.text_input("Pet name")
species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Add Pet"):
    owner.add_pet(Pet(pet_name, species))
    st.success("Pet added")

# Add task
st.subheader("Add Task")

if owner.pets:
    selected_pet = st.selectbox("Select pet", [p.name for p in owner.pets])
    title = st.text_input("Task title")
    duration = st.number_input("Duration", 1, 240, 20)
    priority = st.selectbox("Priority", ["high", "medium", "low"])
    time = st.text_input("Time (HH:MM)", "08:00")
    frequency = st.selectbox("Frequency", ["once", "daily", "weekly"])

    if st.button("Add Task"):
        pet = owner.get_pet(selected_pet)
        pet.add_task(Task(title, duration, priority, time, frequency))
        st.success("Task added")

# Generate schedule
st.subheader("Generate Schedule")

if st.button("Generate"):
    plan = scheduler.generate_daily_plan(date.today())

    st.subheader("📅 Today's Schedule")
    for pet, task in plan["selected"]:
        st.success(f"⏰ {task.due_time} | {task.title} ({pet.name})")

    if plan["conflicts"]:
        for c in plan["conflicts"]:
            st.warning(c)

    st.subheader("🧠 Why this plan was chosen")
    for e in plan["explanation"]:
        st.write(e)