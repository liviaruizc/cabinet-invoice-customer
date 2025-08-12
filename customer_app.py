import streamlit as st
import pandas as pd
from cabinets_web import CartManager
from cabinets_web import ReceiptGenerator
from cabinets_web import df, pretty_names, pretty_to_clean

# Get markup from URL query parameters
query_params = st.experimental_get_query_params()
markup_percent = float(query_params.get("markup", [30.0])[0])  # Default to 30 if not in URL
st.session_state.markup_percent = markup_percent

st.title("🧰 Cabinet Order System - Customer View")

cart = CartManager()

# Customer selects type and item
selected_type = st.selectbox("Select cabinet type", pretty_names)
filtered_df = df[df['TYPES_clean'] == pretty_to_clean[selected_type]]

selected_item = st.selectbox("Select an item", filtered_df['ITEM'].tolist())
quantity = st.number_input("Quantity", min_value=1, value=1)

# Add to cart
if st.button("Add to Cart"):
    item = filtered_df[filtered_df['ITEM'] == selected_item].iloc[0]
    cart.add_item(
        item_name=item['ITEM'],
        item_type=selected_type,
        qty=quantity,
        base_price=item['PRICE WITH DISCOUNT'],
        retail_price=item['ORIGINAL PRICE'],
    )

# Clear cart
if st.button("Clear Cart"):
    cart.clear_cart()

# Show cart
cart_items = cart.get_cart()
if cart_items:
    st.subheader("Cart")
    df_display = pd.DataFrame(cart_items)
    df_display = df_display.round(2)
    df_display = df_display.rename(columns={
        "retail price": "Retail Price",
        "base_price": "Base Price (60% 0ff)",
        "savings": "You Save",
        "final_price": "Final Price",
        "total": "Total"
    })
    df_display = df_display[["type", "item", "qty", "Retail Price", "Base Price (60% 0ff)", "You Save", "Final Price", "Total"]]
    st.table(df_display)
else:
    st.info("Cart is empty")

# Generate PDF
if st.button("Generate PDF Invoice"):
    if cart_items:
        invoice = ReceiptGenerator(cart_items)
        pdf_path = invoice.create_pdf()
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download Invoice", f, file_name="invoice.pdf", mime="application/pdf")
    else:
        st.warning("Your cart is empty!")
