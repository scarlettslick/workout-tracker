import streamlit as st
import psycopg2

st.set_page_config(page_title="Exercise Library", page_icon="💪")

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("💪 Exercise Library")

# ── ADD EXERCISE FORM ──────────────────────────────────────
st.subheader("Add a New Exercise")

with st.form("add_exercise_form"):
    name = st.text_input("Exercise Name *")
    
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Category", ["Push", "Pull", "Legs", "Cardio", "Core", "Other"])
    with col2:
        muscle_group = st.selectbox("Muscle Group", ["Chest", "Back", "Shoulders", "Biceps", "Triceps", "Quads", "Hamstrings", "Glutes", "Calves", "Core", "Full Body", "Other"])
    
    notes = st.text_area("Notes (optional)", placeholder="e.g. Keep elbows tucked")
    submitted = st.form_submit_button("Add Exercise")

    if submitted:
        errors = []
        if not name.strip():
            errors.append("Exercise name is required.")
        if errors:
            for err in errors:
                st.error(err)
        else:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO exercises (name, category, muscle_group, notes) VALUES (%s, %s, %s, %s);",
                    (name.strip(), category, muscle_group, notes or None)
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ '{name}' added to your exercise library!")
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")

# ── SEARCH ─────────────────────────────────────────────────
st.subheader("Your Exercise Library")
search = st.text_input("Search exercises by name")

# ── EXERCISE TABLE ─────────────────────────────────────────
try:
    conn = get_connection()
    cur = conn.cursor()

    if search.strip():
        cur.execute("""
            SELECT id, name, category, muscle_group, notes
            FROM exercises
            WHERE name ILIKE %s
            ORDER BY name;
        """, (f"%{search.strip()}%",))
    else:
        cur.execute("""
            SELECT id, name, category, muscle_group, notes
            FROM exercises
            ORDER BY name;
        """)

    exercises = cur.fetchall()
    cur.close()
    conn.close()

    if not exercises:
        st.info("No exercises found.")
    else:
        for ex in exercises:
            ex_id, ex_name, ex_cat, ex_muscle, ex_notes = ex
            with st.expander(f"{ex_name} — {ex_cat} | {ex_muscle}"):
                
                # ── EDIT FORM ──
                with st.form(f"edit_{ex_id}"):
                    new_name = st.text_input("Name", value=ex_name)
                    col1, col2 = st.columns(2)
                    with col1:
                        new_cat = st.selectbox("Category", ["Push", "Pull", "Legs", "Cardio", "Core", "Other"],
                                               index=["Push", "Pull", "Legs", "Cardio", "Core", "Other"].index(ex_cat) if ex_cat in ["Push", "Pull", "Legs", "Cardio", "Core", "Other"] else 0)
                    with col2:
                        muscle_options = ["Chest", "Back", "Shoulders", "Biceps", "Triceps", "Quads", "Hamstrings", "Glutes", "Calves", "Core", "Full Body", "Other"]
                        new_muscle = st.selectbox("Muscle Group", muscle_options,
                                                  index=muscle_options.index(ex_muscle) if ex_muscle in muscle_options else 0)
                    new_notes = st.text_area("Notes", value=ex_notes or "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update = st.form_submit_button("💾 Save Changes")
                    with col2:
                        delete = st.form_submit_button("🗑️ Delete", type="secondary")

                if update:
                    if not new_name.strip():
                        st.error("Name cannot be blank.")
                    else:
                        try:
                            conn = get_connection()
                            cur = conn.cursor()
                            cur.execute("""
                                UPDATE exercises
                                SET name=%s, category=%s, muscle_group=%s, notes=%s
                                WHERE id=%s;
                            """, (new_name.strip(), new_cat, new_muscle, new_notes or None, ex_id))
                            conn.commit()
                            cur.close()
                            conn.close()
                            st.success("✅ Exercise updated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                if delete:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM exercises WHERE id=%s;", (ex_id,))
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success(f"🗑️ '{ex_name}' deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

except Exception as e:
    st.error(f"Error loading exercises: {e}")
