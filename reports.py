
import streamlit as st
import pandas as pd
from db_connection import get_connection


QUERIES = {

    "Query 1 - All Customer Sales":
    """
    SELECT *
    FROM customer_sales;
    """,

    "Query 2 - All Branches":
    """
    SELECT *
    FROM branches;
    """,

    "Query 3 - All Payment Splits":
    """
    SELECT *
    FROM payment_splits;
    """,

    "Query 4 - Open Sales":
    """
    SELECT *
    FROM customer_sales
    WHERE status = 'Open';
    """,

    "Query 5 - Total Gross Sales":
    """
    SELECT
        SUM(gross_sales) AS total_gross_sales
    FROM customer_sales;
    """,

    "Query 6 - Total Received Amount":
    """
    SELECT
        SUM(received_amount) AS total_received_amount
    FROM customer_sales;
    """,

    "Query 7 - Total Pending Amount":
    """
    SELECT
        SUM(gross_sales - received_amount) AS total_pending_amount
    FROM customer_sales;
    """,

    "Query 8 - Sales Count Per Branch":
    """
    SELECT
        b.branch_name,
        COUNT(cs.sale_id) AS total_sales
    FROM branches b
    LEFT JOIN customer_sales cs
    ON b.branch_id = cs.branch_id
    GROUP BY b.branch_id, b.branch_name;
    """,

    "Query 9 - Sales With Branch Name":
    """
    SELECT
        cs.sale_id,
        cs.customer_name,
        cs.product_name,
        cs.gross_sales,
        cs.received_amount,
        b.branch_name
    FROM customer_sales cs
    JOIN branches b
    ON cs.branch_id = b.branch_id;
    """,

    "Query 10 - Sales With Total Payment":
    """
    SELECT
        cs.sale_id,
        cs.customer_name,
        cs.gross_sales,
        cs.received_amount,
        COALESCE(SUM(ps.amount), 0) AS payment_received
    FROM customer_sales cs
    LEFT JOIN payment_splits ps
    ON cs.sale_id = ps.sale_id
    GROUP BY
        cs.sale_id,
        cs.customer_name,
        cs.gross_sales,
        cs.received_amount;
    """,

    "Query 11 - Branch Wise Gross Sales":
    """
    SELECT
        b.branch_name,
        SUM(cs.gross_sales) AS total_gross_sales
    FROM branches b
    JOIN customer_sales cs
    ON b.branch_id = cs.branch_id
    GROUP BY b.branch_id, b.branch_name;
    """,

    "Query 12 - Sales With Payment Method":
    """
    SELECT
        cs.sale_id,
        cs.customer_name,
        cs.product_name,
        cs.gross_sales,
        ps.payment_method,
        ps.amount
    FROM customer_sales cs
    JOIN payment_splits ps
    ON cs.sale_id = ps.sale_id;
    """,

    "Query 13 - Pending Greater Than 5000":
    """
    SELECT
        sale_id,
        customer_name,
        product_name,
        gross_sales,
        received_amount,
        gross_sales - received_amount AS pending_amount
    FROM customer_sales
    WHERE (gross_sales - received_amount) > 5000;
    """,

    "Query 14 - Top 3 Highest Sales":
    """
    SELECT
        sale_id,
        customer_name,
        product_name,
        gross_sales
    FROM customer_sales
    ORDER BY gross_sales DESC
    LIMIT 3;
    """,

    "Query 15 - Monthly Sales Summary":
    """
    SELECT
        YEAR(sale_date) AS year,
        MONTH(sale_date) AS month,
        SUM(gross_sales) AS total_sales,
        SUM(received_amount) AS total_received,
        SUM(gross_sales - received_amount) AS total_pending
    FROM customer_sales
    GROUP BY YEAR(sale_date), MONTH(sale_date)
    ORDER BY year, month;
    """
}


def view_sales():

    st.header("📊 Sales Reports")

    conn = get_connection()

    # ---------------- SALES DATA ----------------

    if st.session_state.role == "Super Admin":

        df = pd.read_sql(
            """
            SELECT
                cs.*,
                b.branch_name
            FROM customer_sales cs
            LEFT JOIN branches b
            ON cs.branch_id = b.branch_id
            """,
            conn
        )

    else:

        df = pd.read_sql(
            """
            SELECT
                cs.*,
                b.branch_name
            FROM customer_sales cs
            LEFT JOIN branches b
            ON cs.branch_id = b.branch_id
            WHERE cs.branch_id=%s
            """,
            conn,
            params=(st.session_state.branch_id,)
        )

    conn.close()

    # ---------------- FILTERS ----------------

    if not df.empty:

        df["pending_amount"] = (
            df["gross_sales"] - df["received_amount"]
        )

        st.subheader("🔎 Filters")

        col1, col2, col3 = st.columns(3)

        with col1:

            branches = ["All"] + sorted(
                df["branch_name"]
                .dropna()
                .unique()
                .tolist()
            )

            selected_branch = st.selectbox(
                "Branch",
                branches
            )

        with col2:

            products = ["All"] + sorted(
                df["product_name"]
                .dropna()
                .unique()
                .tolist()
            )

            selected_product = st.selectbox(
                "Product",
                products
            )

        with col3:

            statuses = [
                "All",
                "Open",
                "Close"
            ]

            selected_status = st.selectbox(
                "Status",
                statuses
            )

        filtered_df = df.copy()

        if selected_branch != "All":

            filtered_df = filtered_df[
                filtered_df["branch_name"]
                == selected_branch
            ]

        if selected_product != "All":

            filtered_df = filtered_df[
                filtered_df["product_name"]
                == selected_product
            ]

        if selected_status != "All":

            filtered_df = filtered_df[
                filtered_df["status"]
                == selected_status
            ]

        # ---------------- SUMMARY ----------------

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Sales",
            f"₹{filtered_df['gross_sales'].sum():,.0f}"
        )

        col2.metric(
            "Total Received",
            f"₹{filtered_df['received_amount'].sum():,.0f}"
        )

        col3.metric(
            "Total Pending",
            f"₹{filtered_df['pending_amount'].sum():,.0f}"
        )

        # ---------------- TABLE ----------------

        st.subheader("Sales Records")

        st.dataframe(
            filtered_df,
            use_container_width=True
        )

    # ---------------- SQL QUERIES ----------------

    st.divider()

    st.subheader("🧮 SQL Query Results")

    selected_query = st.selectbox(
        "Select SQL Query",
        list(QUERIES.keys())
    )

    st.code(
        QUERIES[selected_query],
        language="sql"
    )

    if st.button("▶ Run Selected Query"):

        conn = get_connection()

        try:

            query_result = pd.read_sql(
                QUERIES[selected_query],
                conn
            )

            st.success("Query executed successfully!")

            st.dataframe(
                query_result,
                use_container_width=True
            )

        except Exception as e:

            st.error(
                "Query Error: " + str(e)
            )

        finally:

            conn.close()
