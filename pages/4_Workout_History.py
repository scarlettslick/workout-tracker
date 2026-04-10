import streamlit as st
import psycopg2
from datetime import date, timedelta

st.set_page_config(page_title="Workout History", page_icon="📅")

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("📅 Workout History")

# ── SEARCH / FILTER ────────────────────────────────────────
st.subheader("Search & Filter")

col1, col2, col3 = st.columns(3)
with col1:
    search = st.text_input("Search by title", placeholder="e.g. Push Day")
with col2:
    date_from = st.date_input("From", value=date.today() - timedelta(days=30))
with col3:
    date_to = st.date_input("To", value=date.today())

st.markdown("---")

# ── WORKOUT LIST ───────────────────────────────────────────
try:
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT w.id, w.workout_date, w.title, w.notes, COUNT(we.id) as exercise_count
        FROM workouts w
        LEFT JOIN workout_exercises we ON w.id = we.workout_id
        WHERE w.workout_date::date BETWEEN %s AND %s
    """
    params = [date_from, date_to]

    if search.strip():
        query += " AND w.title ILIKE %s"
        params.append(f"%{search.strip()}%")

    query += " GROUP BY w.id, w.workout_date, w.title, w.notes ORDER BY w.workout_date DESC;"

    cur.execute(query, params)
    workouts = cur.fetchall()
    cur.close()
    conn.close()

    if not workouts:
        st.info("No workouts found for the selected filters.")
    else:
        st.write(f"**{len(workouts)} workout(s) found**")

        for w in workouts:
            w_id, w_date, w_title, w_notes, ex_count = w
            label = f"📅 {w_date.strftime('%Y-%m-%d')} — {w_title or 'Untitled'} ({ex_count} exercise{'s' if ex_count != 1 else ''})"

            with st.expander(label):
                if w_notes:
                    st.write(f"**Session notes:** {w_notes}")

                # ── EXERCISES IN THIS WORKOUT ──────────────
                try:
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("""
                        SELECT e.name, e.category, we.sets, we.reps, we.weight_lbs, we.notes
                        FROM workout_exercises we
                        JOIN exercises e ON we.exercise_id = e.id
                        WHERE we.workout_id = %s
                        ORDER BY e.name;
                    """, (w_id,))
                    exercises = cur.fetchall()
                    cur.close()
                    conn.close()

                    if exercises:
                        st.table([
                            {
                                "Exercise": ex[0],
                                "Category": ex[1],
                                "Sets": ex[2],
                                "Reps": ex[3],
                                "Weight (lbs)": ex[4] or 0,
                                "Notes": ex[5] or "—"
                            }
                            for ex in exercises
                        ])
                    else:
                        st.info("No exercises recorded for this workout.")

                except Exception as e:
                    st.error(f"Error loading exercises: {e}")

                # ── DELETE WORKOUT ─────────────────────────
                st.markdown("---")
                if st.button("🗑️ Delete this workout", key=f"del_{w_id}"):
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM workouts WHERE id=%s;", (w_id,))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success("Workout deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

except Exception as e:
    st.error(f"Error loading workouts: {e}")
