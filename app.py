
import streamlit as st
import pandas as pd

from login import login
from sales import add_sale
from payments import add_payment
from reports import view_sales
from db_connection import get_connection


# ---------------- PAGE SETTINGS ----------------

st.set_page_config(
    page_title="Sales Intelligence Hub",
    page_icon="📊",
    layout="wide"
)


# ---------------- SESSION ----------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""

if "branch_id" not in st.session_state:
    st.session_state.branch_id = None


# ---------------- LOGIN ----------------

if not st.session_state.logged_in:

    login()

    st.stop()


# ---------------- SIDEBAR ----------------

st.sidebar.title("📊 Sales Intelligence Hub")

st.sidebar.write(
    "User: " + st.session_state.username
)

st.sidebar.write(
    "Role: " + st.session_state.role
)


# ---------------- BRANCH NAME ----------------

conn = get_connection()

cursor = conn.cursor()

if st.session_state.role == "Super Admin":

    branch_name = "All Branches"

else:

    cursor.execute(
        """
        SELECT branch_name
        FROM branches
        WHERE branch_id=%s
        """,
        (st.session_state.branch_id,)
    )

    branch = cursor.fetchone()

    branch_name = branch[0] if branch else "Unknown Branch"

cursor.close()
conn.close()


st.sidebar.info(
    "Branch: " + branch_name
)


# ---------------- LOGOUT ----------------

if st.sidebar.button("Logout"):

    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.session_state.branch_id = None

    st.rerun()


# ==================================================
# SUPER ADMIN
# ==================================================

if st.session_state.role == "Super Admin":

    st.title("👑 Super Admin Dashboard")

    menu = st.sidebar.radio(
        "Menu",
        [
            "Dashboard",
            "Manage Users",
            "Add Sale",
            "Update Payment",
            "Sales Reports"
        ]
    )

    # ---------------- DASHBOARD ----------------

    if menu == "Dashboard":

        conn = get_connection()

        df = pd.read_sql(
            """
            SELECT
                cs.*,
                b.branch_name
            FROM customer_sales cs
            LEFT JOIN branches b
            ON cs.branch_id=b.branch_id
            """,
            conn
        )

        conn.close()

        if not df.empty:

            df["pending_amount"] = (
                df["gross_sales"] -
                df["received_amount"]
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Total Sales",
                f"₹{df['gross_sales'].sum():,.0f}"
            )

            col2.metric(
                "Total Received",
                f"₹{df['received_amount'].sum():,.0f}"
            )

            col3.metric(
                "Total Pending",
                f"₹{df['pending_amount'].sum():,.0f}"
            )

            st.subheader("All Branch Sales")

            st.dataframe(
                df,
                use_container_width=True
            )

        else:

            st.info("No sales data available.")


    # ---------------- MANAGE USERS ----------------

    elif menu == "Manage Users":

        st.header("👤 Manage Admin Users")

        conn = get_connection()

        branches = pd.read_sql(
            "SELECT * FROM branches",
            conn
        )

        conn.close()

        st.subheader("Create New Admin")

        new_username = st.text_input(
            "Username"
        )

        new_password = st.text_input(
            "Password",
            type="password"
        )

        branch_name = st.selectbox(
            "Select Branch",
            branches["branch_name"].tolist()
        )

        selected_branch_id = int(
            branches[
                branches["branch_name"] == branch_name
            ]["branch_id"].iloc[0]
        )

        if st.button("Create Admin"):

            if new_username == "" or new_password == "":

                st.error(
                    "Username and password are required."
                )

            else:

                conn = get_connection()

                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT user_id
                    FROM users
                    WHERE username=%s
                    """,
                    (new_username,)
                )

                existing = cursor.fetchone()

                if existing:

                    st.error(
                        "Username already exists."
                    )

                else:

                    cursor.execute(
                        """
                        INSERT INTO users
                        (
                            username,
                            password,
                            branch_id,
                            role
                        )
                        VALUES
                        (%s,%s,%s,'Admin')
                        """,
                        (
                            new_username,
                            new_password,
                            selected_branch_id
                        )
                    )

                    conn.commit()

                    st.success(
                        "Admin created successfully!"
                    )

                cursor.close()
                conn.close()


        st.subheader("Existing Users")

        conn = get_connection()

        users = pd.read_sql(
            """
            SELECT
                user_id,
                username,
                branch_id,
                role
            FROM users
            """,
            conn
        )

        conn.close()

        st.dataframe(
            users,
            use_container_width=True
        )


    # ---------------- ADD SALE ----------------

    elif menu == "Add Sale":

        add_sale()


    # ---------------- PAYMENT ----------------

    elif menu == "Update Payment":

        add_payment()


    # ---------------- REPORT ----------------

    elif menu == "Sales Reports":

        view_sales()


# ==================================================
# ADMIN
# ==================================================

elif st.session_state.role == "Admin":

    st.title(
        "👤 " + branch_name + " Admin"
    )

    menu = st.sidebar.radio(
        "Menu",
        [
            "Dashboard",
            "Add Sale",
            "Update Payment",
            "Sales Reports"
        ]
    )


    # ---------------- DASHBOARD ----------------

    if menu == "Dashboard":

        conn = get_connection()

        df = pd.read_sql(
            """
            SELECT *
            FROM customer_sales
            WHERE branch_id=%s
            """,
            conn,
            params=(st.session_state.branch_id,)
        )

        conn.close()

        if not df.empty:

            df["pending_amount"] = (
                df["gross_sales"] -
                df["received_amount"]
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Branch Sales",
                f"₹{df['gross_sales'].sum():,.0f}"
            )

            col2.metric(
                "Received",
                f"₹{df['received_amount'].sum():,.0f}"
            )

            col3.metric(
                "Pending",
                f"₹{df['pending_amount'].sum():,.0f}"
            )

            st.subheader(
                branch_name + " Sales"
            )

            st.dataframe(
                df,
                use_container_width=True
            )

        else:

            st.info(
                "No sales data for this branch."
            )


    # ---------------- ADD SALE ----------------

    elif menu == "Add Sale":

        add_sale()


    # ---------------- PAYMENT ----------------

    elif menu == "Update Payment":

        add_payment()


    # ---------------- REPORT ----------------

    elif menu == "Sales Reports":

        view_sales()
