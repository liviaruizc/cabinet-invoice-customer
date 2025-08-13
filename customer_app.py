import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER, landscape
import tempfile
from datetime import datetime
import urllib.parse
import openpyxl

# --- Classes ---

class CartManager:
    def __init__(self):
        if 'cart' not in st.session_state:
            st.session_state.cart = []

    def add_item(self, item_name, item_type, qty, base_price, retail_price):
        savings = retail_price - base_price * qty
        markup_percent = st.session_state.get('markup_percent', 0.0)
        final_price = base_price * (1 + markup_percent / 100)

        total = qty * final_price
        st.session_state.cart.append({
            "type": item_type,
            "item": item_name,
            "qty": qty,
            "retail price": retail_price,
            "base_price": base_price,
            "savings": savings,
            "final_price": round(final_price, 2),
            "total": round(total, 2)

        })

    def clear_cart(self):
        st.session_state.cart = []

    def get_cart(self):
        return st.session_state.cart

    def get_totals(self):
        subtotal = sum(item["total"] for item in st.session_state.cart)
        tax = subtotal * 0.065
        final = subtotal + tax
        return subtotal, tax, final

# -------------------------
#PDF Generator
#--------------------------


class ReceiptGenerator:
    def __init__(self, cart):
        self.cart = cart

    def create_pdf(self):
        import tempfile
        from PIL import Image

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            c = canvas.Canvas(tmp.name, pagesize=landscape(LETTER))
            width, height = landscape(LETTER)
            y = height - 50


            # Header (logo & business info can go here)
            c.setFont('Helvetica-Bold', 14)
            c.drawString(50, y - 10, "Mike Renovations LLC")
            c.setFont('Helvetica', 10)
            c.drawString(50, y - 25, "Phone: 239-200-5772")
            c.drawString(50, y - 40, "Email: contact@mikerenovations.com")

            y -= 30
            x = 40
            # Invoice title and date
            c.setFont("Helvetica", 9)
            c.drawString(750, y, datetime.now().strftime("%Y-%m-%d %H:%M"))
            y -= 30

            # Table headers
            c.setFont("Helvetica-Bold", 10)
            c.drawString(x, y, "TYPE")
            x += len("TYPE") + 100
            c.drawString(x, y, "ITEM")
            x += len("ITEM") + 70
            c.drawString(x, y, "RETAIL PRICE")
            x += len("RETAIL PRICE") + 100
            c.drawString(x, y, "UNIT PRICE (60% OFF)")
            x += len("UNIT PRICE (60% OFF)") + 100
            c.drawString(x, y, "FINAL PRICE (with markup)")
            x += len("FINAL PRICE (with markup)") + 150
            c.drawString(x, y, "QTY")
            x += len("QTY") + 100
            c.drawString(x, y, "TOTAL $")
            y -= 15
            c.line(5, y, 780, y)
            y -= 15

            # Rows
            c.setFont("Helvetica", 9)
            total_sum = 0
            price_without_discount = 0
            original_total = 0
            for entry in self.cart:
                c.drawString(40, y, entry["type"])
                c.drawString(145, y, entry["item"][:30])
                c.drawRightString(260, y, f"${entry['retail price']:.2f}")
                c.drawRightString(390, y, f"${entry['base_price']:.2f}")
                c.drawRightString(510, y, f"${entry['final_price']:.2f}")
                c.drawRightString(640, y, str(entry["qty"]))
                c.drawRightString(760, y, f"${entry['total']:.2f}")
                y -= 18
                total_sum += entry["total"]
                price_without_discount += entry["retail price"] * entry["qty"]
                if y < 100:
                    c.showPage()
                    y = height - 50
                original_total += entry['retail price'] * entry['qty']

            # Totals section
            tax = total_sum * 0.065
            final = total_sum + tax + shipping_price + delivery_price
            savings_total = original_total - total_sum

            y -= 20
            c.setFont("Helvetica-Bold", 10)
            c.line(5, y, 780, y)
            y -= 15
            c.drawRightString(600, y, "Total Retail Price: ")
            c.drawRightString(750, y, f"${original_total:.2f}")
            y -= 15
            c.drawRightString(600, y, "You are saving:")
            c.drawRightString(750, y, f"$(-{savings_total:.2f})")
            y -= 15
            c.drawRightString(600, y, "Subtotal (with discount):")
            c.drawRightString(750, y, f"${total_sum:.2f}")
            y -= 15
            c.drawRightString(600, y, "Tax (6.5%):")
            c.drawRightString(750, y, f"${tax:.2f}")
            y -= 15
            c.drawRightString(600, y, "Shipping Fee:")
            if shipping_price == 0.00:
                c.drawRightString(750, y, "FREE")
            else:
                c.drawRightString(750, y, f"${shipping_price}")
            y-= 15
            c.drawRightString(600, y, "Delivery Fee:")
            if delivery_price == 0.00:
                c.drawRightString(750, y, "FREE")
            else:
                c.drawRightString(750, y, f"${delivery_price}")
            y-= 15
            c.drawRightString(600, y, "Final Total:")
            c.drawRightString(750, y, f"${final:.2f}")

            c.save()
            return tmp.name


# --- Load and preprocess data ---
@st.cache_data
def load_data():
    df = pd.read_excel("cabinets_price.xlsx")
    df['TYPES_clean'] = df['TYPES'].str.strip().str.lower()
    return df

df = load_data()
types = df['TYPES_clean'].unique()
pretty_names = [t.title() for t in types]
pretty_to_clean = dict(zip(pretty_names, types))

#-------------------
# Markup
params = st.query_params()
markup_percent = float(params.get("markup", [0.0][0]))
st.session_state.markup_percent = markup_percent

# --- Streamlit UI ---

shipping_options = [0.00, 100.00, 200.00, 300.00, 400.00]
delivery_options = [0.00, 100.00, 200.00, 300.00, 400.00]


st.title("🧰 Cabinet Order System")

cart = CartManager()

selected_type = st.selectbox("Select cabinet type", pretty_names)

filtered_df = df[df['TYPES_clean'] == pretty_to_clean[selected_type]]

selected_item = st.selectbox("Select an item", filtered_df['ITEM'].tolist())
quantity = st.number_input("Quantity", min_value=1, value=1)

if st.button("Add to Cart"):
    item = filtered_df[filtered_df['ITEM'] == selected_item].iloc[0]
    cart.add_item(
        item_name=item['ITEM'],
        item_type=selected_type,
        qty=quantity,
        base_price=item['PRICE WITH DISCOUNT'],
        retail_price=item['ORIGINAL PRICE'],
    )
if st.button("Clear Cart"):
    cart.clear_cart()

shipping_price = st.selectbox(
    "Select shipping price",
    options=shipping_options,
    format_func=lambda x: "FREE" if x == 0 else f"${x:,.2f}"
)
st.session_state.shipping_price = shipping_price

delivery_price = st.selectbox(
    "Select delivery price",
    options=delivery_options,
    format_func=lambda x: "FREE" if x == 0 else f"${x:,.2f}"
)
st.session_state.delivery_price = delivery_price

# Show cart
cart_items = cart.get_cart()
if cart_items:
    st.subheader("🛒 Cart")
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

    st.dataframe(df_display, use_container_width=True)

else:
    st.info("Cart is empty")



# Generate PDF receipt
if st.button("Generate PDF Invoice"):
    if cart_items:
        invoice = ReceiptGenerator(cart_items)
        pdf_path = invoice.create_pdf()
        with open(pdf_path, "rb") as f:
            st.download_button("📄 Download Invoice", f, file_name="invoice.pdf", mime="application/pdf")
    else:
        st.warning("Your cart is empty!")


