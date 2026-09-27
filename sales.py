
import streamlit as st
import pandas as pd
from db_connection import get_connection

PRODUCTS = [
    "Mobile Phone",
    "Laptop",
    "Smart TV",
    "Headphones",
    "Smart Watch",
    "Camera",
    "Monitor",
    "Keyboard",
    "Mouse",
    "Bluetooth Speaker"
]


def add_sale():

    st.header("➕ Add New Sale")

    conn = get_connection()

    branches = pd.read_sql(
        "SELECT branch_id, branch_name FROM branches ORDER BY branch_name",
        conn
    )

    conn.close()

    # Branch selection
    if st.session_state.role == "Super Admin":

        selected_branch = st.selectbox(
            "Select Customer Branch",
            branches["branch_name"].tolist()
        )

        branch_id = int(
            branches[
                branches["branch_name"] == selected_branch
            ]["branch_id"].iloc[0]
        )

    else:

        branch_id = st.session_state.branch_id

        selected_branch = branches[
            branches["branch_id"] == branch_id
        ]["branch_name"].iloc[0]

        st.info(
            "Customer Branch: " + selected_branch
        )

    sale_date = st.date_input(
        "Sale Date"
    )

    customer_name = st.text_input(
        "Customer Name"
    )

    mobile_number = st.text_input(
        "Mobile Number"
    )

    product_name = st.selectbox(
        "Electronic Product",
        PRODUCTS
    )

    gross_sales = st.number_input(
        "Gross Sales",
        min_value=0.0,
        step=100.0
    )

    received_amount = st.number_input(
        "Received Amount",
        min_value=0.0,
        step=100.0
    )

    if st.button("Add Sale"):

        if customer_name == "":
            st.error("Enter customer name")

        elif gross_sales <= 0:
            st.error("Enter gross sales")

        elif received_amount > gross_sales:
            st.error(
                "Received amount cannot be greater than gross sales"
            )

        else:

            status = (
                "Close"
                if received_amount >= gross_sales
                else "Open"
            )

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO customer_sales
                (
                    branch_id,
                    sale_date,
                    customer_name,
                    mobile_number,
                    product_name,
                    gross_sales,
                    received_amount,
                    status
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    branch_id,
                    sale_date,
                    customer_name,
                    mobile_number,
                    product_name,
                    gross_sales,
                    received_amount,
                    status
                )
            )

            conn.commit()

            cursor.close()
            conn.close()

            st.success(
                "Sale added successfully!"
            )

            st.rerun()
