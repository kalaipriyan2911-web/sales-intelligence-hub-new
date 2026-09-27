
import streamlit as st
from db_connection import get_connection

def login():

    st.title("📊 Sales Intelligence Hub")
    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT user_id, username, role, branch_id
            FROM users
            WHERE username=%s AND password=%s
            """,
            (username, password)
        )

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            st.session_state.logged_in = True
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.role = user[2]
            st.session_state.branch_id = user[3]

            st.rerun()

        else:
            st.error("Invalid Username or Password")

    return False
