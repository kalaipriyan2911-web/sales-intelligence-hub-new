
import streamlit as st
import pandas as pd
from db_connection import get_connection

def add_payment():

    st.header("💰 Update Payment")

    conn = get_connection()

    if st.session_state.role == "Super Admin":

        query = """
        SELECT
            sale_id,
            branch_id,
            customer_name,
            product_name,
            gross_sales,
            received_amount,
            (gross_sales - received_amount) AS pending_amount
        FROM customer_sales
        WHERE received_amount < gross_sales
        """

        sales = pd.read_sql(query, conn)

    else:

        query = """
        SELECT
            sale_id,
            branch_id,
            customer_name,
            product_name,
            gross_sales,
            received_amount,
            (gross_sales - received_amount) AS pending_amount
        FROM customer_sales
        WHERE branch_id=%s
        AND received_amount < gross_sales
        """

        sales = pd.read_sql(
            query,
            conn,
            params=(st.session_state.branch_id,)
        )

    conn.close()

    if sales.empty:

        st.info("No pending payments.")

        return

    sale_id = st.selectbox(
        "Select Sale",
        sales["sale_id"].tolist()
    )

    selected = sales[
        sales["sale_id"] == sale_id
    ].iloc[0]

    st.write("Customer:", selected["customer_name"])
    st.write("Product:", selected["product_name"])
    st.write("Gross Sales:", f"₹{selected['gross_sales']:,.2f}")
    st.write("Already Received:", f"₹{selected['received_amount']:,.2f}")
    st.write("Pending:", f"₹{selected['pending_amount']:,.2f}")

    payment_amount = st.number_input(
        "Payment Amount",
        min_value=0.0,
        max_value=float(selected["pending_amount"]),
        step=100.0
    )

    payment_method = st.selectbox(
        "Payment Method",
        ["Cash", "UPI", "Bank Transfer"]
    )

    payment_date = st.date_input(
        "Payment Date"
    )

    if st.button("Update Payment"):

        if payment_amount <= 0:

            st.error("Enter payment amount")

            return

        new_received = (
            float(selected["received_amount"])
            + payment_amount
        )

        status = (
            "Close"
            if new_received >= float(selected["gross_sales"])
            else "Open"
        )

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO payment_splits
            (
                sale_id,
                payment_date,
                amount,
                payment_method
            )
            VALUES (%s,%s,%s,%s)
            """,
            (
                int(sale_id),
                payment_date,
                payment_amount,
                payment_method
            )
        )

        cursor.execute(
            """
            UPDATE customer_sales
            SET
                received_amount=%s,
                status=%s
            WHERE sale_id=%s
            """,
            (
                new_received,
                status,
                int(sale_id)
            )
        )

        conn.commit()

        cursor.close()
        conn.close()

        st.success("Payment updated successfully!")

        st.rerun()
