import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

# Set password
PASSWORD = "ilovefulfil"

# Configure page
st.set_page_config(page_title="Fulfil Inventory Dashboard", layout="wide")

# Session state for authentication
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h2 style='text-align: center;'>🔒 Secure Dashboard Login</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Please enter the password to access the dashboard.</p>", unsafe_allow_html=True)
    password_input = st.text_input("Password", type="password")
    if st.button("Login"):
        if password_input == PASSWORD:
            st.session_state["authenticated"] = True
            st.success("Login successful! Redirecting...")
            st.rerun()
        else:
            st.error("Incorrect password. Please try again.")
else:
    st.markdown("<h1 style='text-align: center; color: #2E8B57;'>Fulfil Inventory EDA Dashboard</h1>", unsafe_allow_html=True)

    if "show_links" not in st.session_state:
        st.session_state["show_links"] = False

    def toggle_links():
        st.session_state["show_links"] = not st.session_state["show_links"]

    if st.button("Show/Hide Documentation", on_click=toggle_links):
        pass

    if st.session_state["show_links"]:
        st.markdown("<h4 style='text-align: center; color: #2E8B57;'>About this Dashboard</h4>", unsafe_allow_html=True)
        st.write("This dashboard explores Fulfil's inventory and sales data from March 25–April 12, 2020.")
        st.markdown("- For questions, contact the Fulfil Data Team.")

    # Sidebar file upload
    st.sidebar.header("Upload Data Files")
    p_lines_file = st.sidebar.file_uploader("Upload purchase_lines.csv", type="csv")
    p_header_file = st.sidebar.file_uploader("Upload purchase_header.csv", type="csv")
    products_file = st.sidebar.file_uploader("Upload product.csv", type="csv")

    if p_lines_file and p_header_file and products_file:
        p_lines = pd.read_csv(p_lines_file)
        p_header = pd.read_csv(p_header_file)
        products = pd.read_csv(products_file)

        # Clean product data
        products.columns = products.columns.str.strip().str.upper()
        if 'PRODUCT_ID' in products.columns:
            products.drop_duplicates(subset='PRODUCT_ID', keep='first', inplace=True)
            products['VOLUME'] = (
                products['HEIGHT_INCHES'] *
                products['WIDTH_INCHES'] *
                products['DEPTH_INCHES']
            )
        else:
            st.error("Missing 'PRODUCT_ID' column in product file.")

        # Standardize merge keys
        p_lines.columns = p_lines.columns.str.upper()
        p_header.columns = p_header.columns.str.upper()
        p_header['DATE'] = pd.to_datetime(p_header['PURCHASE_DATE_TIME'])

        # Merge datasets
        merged_df = pd.merge(pd.merge(p_lines, products, on="PRODUCT_ID", how="left"),
                             p_header, on="PURCHASE_ID", how="left")
        merged_df["TOTAL_VOLUME"] = merged_df["VOLUME"] * merged_df["QUANTITY"]

        # Department analysis
        st.header("📊 Departmental Analysis")
        dept_sales = merged_df.groupby("DEPARTMENT_NAME")["QUANTITY"].sum().sort_values(ascending=False).reset_index()
        fig1 = px.bar(dept_sales, x="DEPARTMENT_NAME", y="QUANTITY", title="Total Quantity Sold by Department", labels={"DEPARTMENT_NAME": "Department", "QUANTITY": "Units Sold"})
        st.plotly_chart(fig1, use_container_width=True)

        volume_by_dept = merged_df.groupby("DEPARTMENT_NAME")["TOTAL_VOLUME"].sum().sort_values(ascending=False).reset_index()
        fig2 = px.bar(volume_by_dept, x="DEPARTMENT_NAME", y="TOTAL_VOLUME", title="Total Storage Volume by Department", labels={"DEPARTMENT_NAME": "Department", "TOTAL_VOLUME": "Total Volume"})
        st.plotly_chart(fig2, use_container_width=True)

        # Hourly transaction pattern
        st.header("⏰ Hourly Transaction Pattern")
        merged_df["HOUR"] = merged_df["DATE"].dt.hour
        hourly_sales = merged_df.groupby("HOUR")["PURCHASE_ID"].nunique().reset_index(name="Transaction_Count")
        fig3 = px.line(hourly_sales, x="HOUR", y="Transaction_Count", markers=True, title="Transactions Per Hour", labels={"HOUR": "Hour of Day", "Transaction_Count": "Number of Transactions"})
        st.plotly_chart(fig3, use_container_width=True)

        # Basket size analysis
        st.header("🧺 Basket Size Analysis")
        basket_sizes = merged_df.groupby("PURCHASE_ID")["PRODUCT_ID"].count().reset_index(name="Basket_Size")
        avg_basket = basket_sizes["Basket_Size"].mean()
        st.subheader(f"Average Basket Size: {avg_basket:.2f} items")

        fig4 = px.histogram(
            basket_sizes,
            x="Basket_Size",
            nbins=50,
            title="Distribution of Basket Sizes per Transaction",
            labels={"Basket_Size": "Number of Items in Basket", "count" : "Count"}
        )
        fig4.add_vline(
            x=avg_basket,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Avg: {avg_basket:.2f}",
            annotation_position="top right"
        )
        st.plotly_chart(fig4, use_container_width=True)

    else:
        st.info("Please upload all three CSV files to begin analysis.")

