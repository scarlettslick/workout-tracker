import streamlit as st
import psycopg2
from datetime import date

st.set_page_config(page_title="My Goals", page_icon="🎯")

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("🎯 My Goals")

# ── LOAD DROPDOWNS FROM DATABASE ───────────────────────────
try:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM goal_types ORDER BY name;")
    goal_type_rows = cur.fetchall()
    goal_type_options = {row[1]: row[0] for row in goal_type_rows}

    cur.execute("SELECT id, name FROM goal_statuses ORDER BY name;")
    goal_status_rows = cur.fetchall()
    goal_status_options = {row[1]: row[0] for row in goal_status_rows}

    cur.close()
    conn.close()
except Exception as e:
    st.error(f"Error loading dropdown options: {e}")
    goal_type_options = {}
    goal_status_options = {}

# ── ADD GOAL FORM ──────────────────────────────────────────
st.subheader("Add a New Goal")

with st.form("add_goal_form"):
    title = st.text_input("Goal Title *", placeholder="e.g. Bench Press 225 lbs")
    description = st.text_area("Description (optional)", placeholder="e.g. Hit a 2 plate bench by summer")

    col1, col2 = st.columns(2)
    with col1:
        selected_goal_type = st.selectbox("Goal Type *", options=list(goal_type_options.keys()))
    with col2:
        selected_status = st.selectbox("Status *", options=list(goal_status_options.keys()))

    col1, col2, col3 = st.columns(3)
    with col1:
        target_value = st.number_input("Target Value", min_value=0.0, value=0.0, step=1.0)
    with col2:
        unit = st.text_input("Unit", placeholder="e.g. lbs, minutes, days")
    with col3:
        target_date = st.date_input("Target Date *", value=date.today())

    submitted = st.form_submit_button("Add Goal")

    if submitted:
        errors = []
        if not title.strip():
            errors.append("Goal title is required.")
        if target_date < date.today():
            errors.append("Target date must be today or in the future.")
        if not selected_goal_type:
            errors.append("Goal type is required.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO goals (title, description, goal_type, target_value, unit, target_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (title.strip(), description or None, selected_goal_type,
                      target_value or None, unit or None, target_date, selected_status))
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ Goal '{title}' added!")
            except Exception as e:
                st.error(f"Error: {e}")

st.markdown("---")

# ── ACTIVE GOALS ───────────────────────────────────────────
st.subheader("🟢 Active Goals")

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, description, goal_type, target_value, unit, target_date, status
        FROM goals WHERE status = 'active' ORDER BY target_date;
    """)
    active_goals = cur.fetchall()
    cur.close()
    conn.close()

    if not active_goals:
        st.info("No active goals yet. Add one above!")
    else:
        for g in active_goals:
            g_id, g_title, g_desc, g_type, g_val, g_unit, g_date, g_status = g
            with st.expander(f"🎯 {g_title} — due {g_date}"):
                st.write(f"**Type:** {g_type}")
                if g_val:
                    st.write(f"**Target:** {g_val} {g_unit or ''}")
                if g_desc:
                    st.write(f"**Description:** {g_desc}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Mark Achieved", key=f"achieve_{g_id}"):
                        try:
                            conn = get_connection()
                            cur = conn.cursor()
                            cur.execute("UPDATE goals SET status='achieved' WHERE id=%s;", (g_id,))
                            conn.commit()
                            cur.close()
                            conn.close()
                            st.success("🏆 Goal marked as achieved!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{g_id}"):
                        if f"confirm_delete_goal_{g_id}" not in st.session_state:
                            st.session_state[f"confirm_delete_goal_{g_id}"] = True
                            st.warning(f"⚠️ Are you sure you want to delete '{g_title}'? Click Delete again to confirm.")
                        else:
                            try:
                                conn = get_connection()
                                cur = conn.cursor()
                                cur.execute("DELETE FROM goals WHERE id=%s;", (g_id,))
                                conn.commit()
                                cur.close()
                                conn.close()
                                del st.session_state[f"confirm_delete_goal_{g_id}"]
                                st.success("Goal deleted.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

except Exception as e:
    st.error(f"Error loading goals: {e}")

st.markdown("---")

# ── ACHIEVED GOALS ─────────────────────────────────────────
st.subheader("🏆 Achieved Goals")

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT title, goal_type, target_value, unit, target_date
        FROM goals WHERE status = 'achieved' ORDER BY target_date DESC;
    """)
    achieved = cur.fetchall()
    cur.close()
    conn.close()

    if not achieved:
        st.info("No achieved goals yet — keep pushing!")
    else:
        for g in achieved:
            st.success(f"✅ {g[0]} — {g[1]} | Target: {g[2]} {g[3] or ''}")

except Exception as e:
    st.error(f"Error loading achieved goals: {e}")
