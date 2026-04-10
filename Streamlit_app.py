import streamlit as st
import psycopg2

st.set_page_config(page_title="Workout Tracker", page_icon="🏋️")

st.set_page_config(page_title="Workout Tracker", page_icon="🏋️")

def get_connection():
    conn = psycopg2.connect(st.secrets["DB_URL"])
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SET search_path TO retool, public;")
    cur.close()
    return conn

st.title("🏋️ Personal Workout Tracker")
st.write("Welcome! Use the sidebar to navigate between pages.")

st.markdown("---")
st.subheader("📊 Your Stats")

try:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM workouts;")
    workout_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT exercise_id) FROM workout_exercises;")
    exercise_count = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(sets * reps * weight_lbs), 0)
        FROM workout_exercises;
    """)
    total_volume = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM goals WHERE status = 'active';")
    active_goals = cur.fetchone()[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Workouts", workout_count)
    col2.metric("Exercises Used", exercise_count)
    col3.metric("Total Volume (lbs)", f"{total_volume:,.0f}")
    col4.metric("Active Goals", active_goals)

    st.markdown("---")
    st.subheader("🕐 Recent Workouts")

    cur.execute("""
        SELECT w.workout_date, w.title, COUNT(we.id) AS exercises
        FROM workouts w
        LEFT JOIN workout_exercises we ON w.id = we.workout_id
        GROUP BY w.id, w.workout_date, w.title
        ORDER BY w.workout_date DESC
        LIMIT 5;
    """)
    rows = cur.fetchall()

    if rows:
        st.table([
            {
                "Date": r[0].strftime("%Y-%m-%d %H:%M"),
                "Workout": r[1] or "Untitled",
                "Exercises": r[2]
            }
            for r in rows
        ])
    else:
        st.info("No workouts logged yet. Head to Log Workout to get started!")

    cur.close()
    conn.close()

except Exception as e:
    st.error(f"Database connection error: {e}")
