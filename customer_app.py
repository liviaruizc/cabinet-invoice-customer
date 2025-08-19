import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER, landscape
import tempfile
import math
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
            c.drawString(50, y - 10, "Cabinet Depot")
            c.setFont('Helvetica', 10)
            c.drawString(50, y - 25, "Email: cabinet.depot12@gmail.com")

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
            c.drawString(x, y, "FINAL PRICE")
            x += len("FINAL PRICE") + 150
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
            c.drawRightString(600, y, "Subtotal:")
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
            if selected_location == "Pick Up":
                c.drawRightString(750, y, "FREE")
            else:
                c.drawRightString(750, y, f"${delivery_price:.2f}")
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

#Cabinets image mapping
type_images = {
    "Base Cabinets": ["base_blind_corner.png", "base_cabinets.png",
                      "base_cabinets_2doors.png"],
    "1 Door": ["wall_cabinet_1_door_2_shelves.png",
               "wall_cabinet_1door_3_shelves.png",
               "wall_cabinet_1door_2_shelves.png"],
    "Wall Cabinets": ["wall_cabinet_2_doors_2_shelves.png",
                      "wall_cabinet_2_doors_3_shelves.png",
                      "wall_cabinet_2doors_2_shelves.png"],
    "3 Drawer Base": ["drawer_base.png"],
    "Sink Base Cabinets": ["sink_base.png"],
    "Glass Door": ["glass_door.png"],
    "Base Lazy Suzan": ["base_lazy_suzan.png"],
    "Base Blind Corner": ["base_blind_corner.png"],
    "Base Diagonal Corner": ["base_diagonal_corner.png"],
    "Fridge/Micro Cabinet": ["fridge_cabinet.png",
                             "fridge_cabinet2.png"],
    "Wall - Diagonal Corner": ["wall_diagonal_2_shelves.png",
                               "wall_diagonal_3_shelves.png"],
    "Pantry Cabinets": ["pantry_cabinet_single.png",
                        "pantry_cabinet_double.png"],
    "Trims And Moldings": ["quater_round_molding.png",
                           "scribe_molding.png",
                           "toe_kick.png",
                           "outside_corner_molding.png",
                           "countertop_molding.png",],
    '3/4" Panels': ["3-4_panels.png"],
    "Deco Doors": ["deco_doors.png"],
    "Wall Wine Racks": ["wine_rack.png"],
    "Wall Open End Shelves": ["wall_open_end_shelves.png"],
    "Valance": ["valance.png"],
    "Fillers": ["fillers.png"],
    "Rosette Fillers": ["rosette_filler.png"],
}

#-------------------
# Markup
query_params = st.query_params
markup_value = query_params.get("markup","0.0") #returns a string
markup_percent = float(markup_value)
st.session_state.markup_percent = markup_percent

# --- Streamlit UI ---
st.markdown(
    """
    <style>
    .header-container {
        position: relative;
        text-align: center;
        color: white;
        margin-bottom: 20px
    }
    .header-image {
        width: 100%;
        height: 250px;
        object-fit: cover;
        border-radius: 10px;
    }
    .header-text {
        position: absolute;
        top: 60%;
        left: 50%;
        transform: translate(-50%, -50%);
        font-family: 'Times New Roman', Times, serif;
        background-color:rgba(255, 255, 255, 0.4); /* semi-transparent bg for readability */
        padding: 10px 20px;
        border-radius: 5px;
    }
    
    .header-text h1 {
        margin: 0;
        font-size: 40px;
        color: black;
    }
    
    .header-text p {
        margin:5px 0 0 0;
        font-size: 16px
        color: black;
    }
    
    .header-logo {
        width: 80px;
        margin-bottom: 10px;
        border-radius: 10px;
    }
    
    a {
        color: black;
        text-decoration: none;
    }
    
    </style>
    
    <div class="header-container">
        <img src="https://scontent.ffxe1-2.fna.fbcdn.net/v/t39.30808-6/433459497_122112182360242422_80665106797432462_n.jpg?stp=cp6_dst-jpg_tt6&_nc_cat=100&ccb=1-7&_nc_sid=6ee11a&_nc_ohc=M5wYO61pOMAQ7kNvwFRBy9p&_nc_oc=AdmrG4ZigfA5D7kDbb2IcZVkfnizIOobYj_wccSWROr3kAwTkVc4AgvAxgIijSii-qc&_nc_zt=23&_nc_ht=scontent.ffxe1-2.fna&_nc_gid=nJpT5wsuOAFrLoCGV8rOaw&oh=00_AfU5ZRCdCGkBd1DbKcQqZ0_1aNDnShfylgPxhgh1_dlPJA&oe=68AA9DBF" class="header-logo"><br>
        <img src="https://craftkitchenandbath.com/wp-content/uploads/2021/02/Craft-KB-Mclean-Kitchen-9-e1614843347132.jpg" class="header-image">
        <div class="header-text">
            <h1> Cabinet Depot </h1>
            <p style="font-weight: bold; color: black; font-size: 18"> 
            Unlocking the beauty of your space.</p>
            <p <a href="mailto:cabinet.depot12@gmail.com" style="color:black;">cabinet.depot12@gmail.com</a>
            </div>
    </div>
        """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f8f8f8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


shipping_options = [0.00, 100.00, 200.00, 300.00, 400.00]
delivery_options = {"Pick Up": 0.00,
                    "Sarasota County": 400.00,
                    "Port Charlotte": 350.00,
                    "Punta Gorda": 300.00,
                    "Lee County": 200.00,
                    "Naples": 250.00,
                    "Estero/Bonita Springs": 200.00,
                    "Tampa": 500.00}


st.title("Order")

cart = CartManager()

selected_type = st.selectbox("Select cabinet type", pretty_names)

#Show all images for that type
if selected_type in type_images:
    images = type_images[selected_type]

    if len(images) == 1:
        # Show a single image with fixed width
        st.image(images[0], caption=selected_type, width=300)
    else:
    # Create columns based on number of images
        #Show 3 per row
        num_rows = math.ceil(len(images) / 3)
        for row in range(num_rows):
            row_images = images[row * 3: (row + 1) * 3]
            cols = st.columns(len(row_images))
            for col, img in zip(cols, row_images):
                with col:
                    st.image(img, caption=selected_type,use_container_width=True)

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

shipping_price = 400

selected_location = st.selectbox(
    "Select delivery type",
    options=delivery_options.keys()
)
#Get the price from dictionary
delivery_price = delivery_options[selected_location]



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

    subtotal = df_display["Total"].sum()

    # Append Shipping row
    df_display.loc[len(df_display)] = ["Shipping", "", "", "", "", "", "", shipping_price]

    # Append Delivery row
    df_display.loc[len(df_display)] = ["Delivery", "", "", "", "", "", "", delivery_price]

    # Calculate grand total
    grand_total = subtotal + delivery_price + shipping_price
    df_display.loc[len(df_display)] = ["", "Grand Total", "", "", "", "", "", grand_total]

    # Format currency columns
    currency_cols = ["Retail Price", "Base Price (60% 0ff)", "You Save", "Final Price", "Total"]
    df_display[currency_cols] = df_display[currency_cols].applymap(
        lambda x: f"${x:.2f}" if pd.notnull(x) and isinstance(x, (int, float)) else x
    )

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








