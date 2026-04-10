import streamlit as st
import psycopg2
from datetime import datetime

st.set_page_config(page_title="Log Workout", page_icon="📝")

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("📝 Log a Workout")

# ── INITIALIZE SESSION STATE ───────────────────────────────
if "exercises_in_workout" not in st.session_state:
    st.session_state.exercises_in_workout = []

# ── WORKOUT DETAILS ────────────────────────────────────────
st.subheader("Workout Details")

workout_title = st.text_input("Workout Title (optional)", placeholder="e.g. Monday Push Day")
workout_date = st.date_input("Date", value=datetime.today())
workout_notes = st.text_area("Session Notes (optional)", placeholder="e.g. Felt strong today")

st.markdown("---")

# ── ADD EXERCISES ──────────────────────────────────────────
st.subheader("Add Exercises")

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, category FROM exercises ORDER BY name;")
    exercise_rows = cur.fetchall()
    cur.close()
    conn.close()

    exercise_options = {f"{row[1]} ({row[2]})": row[0] for row in exercise_rows}

    with st.form("add_exercise_to_workout"):
        selected_exercise = st.selectbox("Exercise", options=list(exercise_options.keys()))
        col1, col2, col3 = st.columns(3)
        with col1:
            sets = st.number_input("Sets", min_value=1, max_value=20, value=3)
        with col2:
            reps = st.number_input("Reps", min_value=1, max_value=100, value=10)
        with col3:
            weight = st.number_input("Weight (lbs)", min_value=0.0, max_value=1000.0, value=0.0, step=2.5)
        ex_notes = st.text_input("Notes (optional)", placeholder="e.g. Paused at bottom")
        add_ex = st.form_submit_button("➕ Add to Workout")

        if add_ex:
            st.session_state.exercises_in_workout.append({
                "exercise_id": exercise_options[selected_exercise],
                "exercise_name": selected_exercise,
                "sets": int(sets),
                "reps": int(reps),
                "weight": float(weight),
                "notes": ex_notes or None
            })

except Exception as e:
    st.error(f"Error loading exercises: {e}")

# ── CURRENT WORKOUT PREVIEW ────────────────────────────────
if st.session_state.exercises_in_workout:
    st.markdown("---")
    st.subheader("Current Workout")

    for i, ex in enumerate(st.session_state.exercises_in_workout):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"**{ex['exercise_name']}** — {ex['sets']} sets × {ex['reps']} reps @ {ex['weight']} lbs")
        with col2:
            if st.button("❌ Remove", key=f"remove_{i}"):
                st.session_state.exercises_in_workout.pop(i)
                st.rerun()

    st.markdown("---")

    # ── SAVE WORKOUT ───────────────────────────────────────
    if st.button("💾 Save Workout", type="primary"):
        if not st.session_state.exercises_in_workout:
            st.error("Please add at least one exercise before saving.")
        else:
            try:
                conn = get_connection()
                cur = conn.cursor()

                # Insert workout
                cur.execute("""
                    INSERT INTO workouts (workout_date, title, notes)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                """, (workout_date, workout_title or None, workout_notes or None))
                workout_id = cur.fetchone()[0]

                # Insert each exercise into junction table
                for ex in st.session_state.exercises_in_workout:
                    cur.execute("""
                        INSERT INTO workout_exercises (workout_id, exercise_id, sets, reps, weight_lbs, notes)
                        VALUES (%s, %s, %s, %s, %s, %s);
                    """, (workout_id, ex["exercise_id"], ex["sets"], ex["reps"], ex["weight"], ex["notes"]))

                conn.commit()
                cur.close()
                conn.close()

                st.success("✅ Workout saved successfully!")
                st.session_state.exercises_in_workout = []
                st.rerun()

            except Exception as e:
                st.error(f"Error saving workout: {e}")
else:
    st.info("Add at least one exercise above to build your workout.")
