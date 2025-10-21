# app.py
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import date
import plotly.express as px

# ---------------------------
# CONFIG
# ---------------------------
DB_URI = "mysql+pymysql://root:Mrbean%40123456789d@localhost:3306/foodmanagement_db"
engine = create_engine(DB_URI, pool_pre_ping=True)

st.set_page_config(
    page_title="Food Waste Management System",
    page_icon="🥡",
    layout="wide"
)

# ---------------------------
# STYLE (CSS for cards)
# ---------------------------
CARD_CSS = """
<style>
.card {
  border-radius: 10px;
  padding: 10px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  margin-bottom: 8px;
  font-size:14px;
}
.card--blue { background: linear-gradient(90deg,#f0f7ff,#e9f3ff);}
.card--green { background: linear-gradient(90deg,#f6fff5,#e6ffec);}
.card--amber { background: linear-gradient(90deg,#fff9f0,#fff3e0);}
.card--red { background: linear-gradient(90deg,#fff5f5,#ffecec);}
.small-note { color: #666; font-size: 12px; }
.header-row { display:flex; align-items:center; gap:8px; font-size:14px;}
.header-emoji { font-size:20px; }
</style>
"""
st.markdown(CARD_CSS, unsafe_allow_html=True)

# HEADER
# ---------------------------
st.title("🥡 Local Food Wastage Management System")
st.caption("Turning extra food into help — connect donors and receivers so every meal is shared, not wasted.")
st.write("")

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def run_query(sql, params=None):
    try:
        return pd.read_sql(text(sql), engine, params=params)
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

def execute_query(sql, params=None):
    try:
        with engine.begin() as conn:
            conn.execute(text(sql), params or {})
        return True
    except Exception as e:
        st.error(f"SQL execution error: {e}")
        return False

def download_df_button(df, filename):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Export CSV", csv, file_name=filename, mime="text/csv")

# ---------------------------
# SIDEBAR FILTERS
# ---------------------------
st.sidebar.header("🧭 Filters & Actions")
try:
    cities = pd.read_sql("SELECT DISTINCT City FROM providers WHERE City IS NOT NULL;", engine).City.dropna().tolist()
    providers_list = pd.read_sql("SELECT DISTINCT Name FROM providers WHERE Name IS NOT NULL;", engine).Name.dropna().tolist()
    food_types = pd.read_sql("SELECT DISTINCT Food_Type FROM food_listings WHERE Food_Type IS NOT NULL;", engine).Food_Type.dropna().tolist()
    meal_types = pd.read_sql("SELECT DISTINCT Meal_Type FROM food_listings WHERE Meal_Type IS NOT NULL;", engine).Meal_Type.dropna().tolist()
except Exception:
    cities, providers_list, food_types, meal_types = [], [], [], []

sel_city = st.sidebar.multiselect("Location", cities)
sel_provider = st.sidebar.multiselect("Provider Name", providers_list)
sel_food_type = st.sidebar.multiselect("Food Type", food_types)
sel_meal_type = st.sidebar.multiselect("Meal Type", meal_types)
if st.sidebar.button("🧹 Clear Filters"):
    sel_city = sel_provider = sel_food_type = sel_meal_type = []

# ---------------------------
# FILTERED DATA & SUMMARY
# ---------------------------
preview_sql = """
    SELECT f.Food_Name, f.Food_Type, f.Quantity, f.Expiry_Date, f.Meal_Type, p.Name AS Provider_Name, p.City, p.Contact, p.Address
    FROM food_listings f
    JOIN providers p ON f.Provider_ID = p.Provider_ID
"""
df_preview = run_query(preview_sql)

# Apply filters
if sel_city:
    df_preview = df_preview[df_preview['City'].isin(sel_city)]
if sel_provider:
    df_preview = df_preview[df_preview['Provider_Name'].isin(sel_provider)]
if sel_food_type:
    df_preview = df_preview[df_preview['Food_Type'].isin(sel_food_type)]
if sel_meal_type:
    df_preview = df_preview[df_preview['Meal_Type'].isin(sel_meal_type)]

# ---------------------------
# Left: Visual Overview / Cards
# ---------------------------
with st.container():
    col1, col2, col3 = st.columns([1.8, 1, 1])
    with col1:
        st.markdown('<div class="card card--blue">\
            <div class="header-row"><div class="header-emoji">📈</div>\
            <div><strong>Quick Overview</strong><div class="small-note">Live metrics & top highlights</div></div></div>\
        </div>', unsafe_allow_html=True)
        # show a couple of key metrics (fetch via SQL)
        try:
            totals = pd.read_sql("""
                SELECT 
                  (SELECT IFNULL(COUNT(*),0) FROM providers) AS providers_count,
                  (SELECT IFNULL(COUNT(*),0) FROM receivers) AS receivers_count,
                  (SELECT IFNULL(SUM(Quantity),0) FROM food_listings) AS total_quantity
            """, engine)
            row = totals.iloc[0]
            st.metric("Providers", row['providers_count'])
            st.metric("Receivers", row['receivers_count'])
            st.metric("Total Quantity (units)", row['total_quantity'])
        except Exception:
            st.info("Overview metrics currently unavailable (DB).")

    with col2:
        st.markdown('<div class="card card--green">\
            <div class="header-row"><div class="header-emoji">🥗</div>\
            <div><strong>Wastage Risk</strong><div class="small-note">Items expiring soon</div></div></div></div>', unsafe_allow_html=True)
        try:
            near_expiry = pd.read_sql("""
                SELECT Food_Name, Expiry_Date, Quantity FROM food_listings
                WHERE Expiry_Date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 3 DAY)
                ORDER BY Expiry_Date ASC LIMIT 5
            """, engine)
            if not near_expiry.empty:
                st.table(near_expiry)
            else:
                st.write("No items expiring in next 3 days.")
        except Exception:
            st.write("—")

    with col3:
        st.markdown('<div class="card card--amber">\
            <div class="header-row"><div class="header-emoji">📞</div>\
            <div><strong>Contacts</strong><div class="small-note">Top providers</div></div></div></div>', unsafe_allow_html=True)
        try:
            contacts = pd.read_sql("SELECT Name, City, Contact FROM providers LIMIT 5;", engine)
            st.table(contacts)
        except Exception:
            st.write("—")

st.write("")  # spacing


# ---------------------------
# FILTERED PREVIEW TABLE (5-6 ROWS)
# ---------------------------
st.markdown("#### Filtered Food Listings")
st.dataframe(df_preview.head(6), use_container_width=True)
download_df_button(df_preview.head(6),"filtered_preview.csv")

# ---------------------------
# COMPACT CHARTS
# ---------------------------
st.markdown("#### Visualize Filtered Data")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    if not df_preview.empty:
        food_type_count = df_preview['Food_Type'].value_counts().reset_index()
        food_type_count.columns = ['Food Type','Count']
        fig1 = px.bar(food_type_count, x='Food Type', y='Count', color='Food Type', text='Count', height=250)
        st.plotly_chart(fig1, use_container_width=True)

with chart_col2:
    if not df_preview.empty:
        provider_count = df_preview['Provider_Name'].value_counts().reset_index()
        provider_count.columns = ['Provider','Count']
        fig2 = px.pie(provider_count, names='Provider', values='Count', height=250)
        st.plotly_chart(fig2, use_container_width=True)

# ---------------------------
# 15 SQL QUERIES (Tabs)
# ---------------------------
st.markdown("---")
st.markdown("#### Trend Analysis")
queries_grouped = {
    "Provider & Receiver Insights": {
        "Providers by City": "SELECT City, COUNT(*) AS Total_Providers FROM providers GROUP BY City ORDER BY Total_Providers DESC;",
        "Receivers by City": "SELECT City, COUNT(*) AS Total_Receivers FROM receivers GROUP BY City ORDER BY Total_Receivers DESC;",
        "Most Active Food Providers": """
            SELECT p.Name AS Provider_Name, COUNT(f.Food_ID) AS Total_Donations
            FROM food_listings f
            JOIN providers p ON f.Provider_ID = p.Provider_ID
            GROUP BY p.Provider_ID, p.Name
            ORDER BY Total_Donations DESC
            LIMIT 10;
        """,
        "Total Food Quantity Donated per Provider": """
            SELECT p.Name AS Provider_Name, SUM(f.Quantity) AS Total_Quantity
            FROM food_listings f
            JOIN providers p ON f.Provider_ID = p.Provider_ID
            GROUP BY p.Provider_ID, p.Name
            ORDER BY Total_Quantity DESC;
        """
    },
    "Donation & Claim Trends": {
        "Top Provider Types by Donation Volume": """
            SELECT p.Type AS Provider_Type, SUM(f.Quantity) AS Total_Quantity_Donated
            FROM food_listings f
            JOIN providers p ON f.Provider_ID = p.Provider_ID
            GROUP BY p.Type
            ORDER BY Total_Quantity_Donated DESC;
        """,
        "Top Food Items by Number of Claims": """
            SELECT f.Food_Name, COUNT(c.Claim_ID) AS Claim_Count
            FROM claims c
            JOIN food_listings f ON c.Food_ID = f.Food_ID
            GROUP BY f.Food_Name
            ORDER BY Claim_Count DESC
            LIMIT 10;
        """,
        "Average Quantity Donated per Provider Type": """
            SELECT p.Type AS Provider_Type, ROUND(AVG(f.Quantity), 2) AS Avg_Quantity
            FROM food_listings f
            JOIN providers p ON f.Provider_ID = p.Provider_ID
            GROUP BY p.Type;
        """,
        "Average Quantity Claimed per Receiver": """
            SELECT r.Name AS Receiver_Name, ROUND(AVG(f.Quantity), 2) AS Avg_Quantity_Claimed
            FROM claims c
            JOIN food_listings f ON c.Food_ID = f.Food_ID
            JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
            GROUP BY r.Receiver_ID, r.Name
            ORDER BY Avg_Quantity_Claimed DESC;
        """
    },
    "Wastage & Efficiency": {
        "Most Common Donated Food Types": """
            SELECT f.Food_Type, COUNT(f.Food_ID) AS Total_Listings
            FROM food_listings f
            GROUP BY f.Food_Type
            ORDER BY Total_Listings DESC;
        """,
        "Most Claimed Meal Types": """
            SELECT f.Meal_Type, COUNT(c.Claim_ID) AS Total_Claims
            FROM claims c
            JOIN food_listings f ON c.Food_ID = f.Food_ID
            GROUP BY f.Meal_Type
            ORDER BY Total_Claims DESC;
        """,
        "Food Near Expiry (Wastage Risk)": """
            SELECT Food_ID, Food_Name, Expiry_Date, Quantity
            FROM food_listings
            WHERE Expiry_Date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 3 DAY)
            ORDER BY Expiry_Date ASC;
        """,
        "Donation vs Claim Comparison": """
            SELECT 
                (SELECT IFNULL(SUM(Quantity),0) FROM food_listings) AS Total_Donated,
                (SELECT IFNULL(SUM(f.Quantity),0) FROM claims c JOIN food_listings f ON c.Food_ID = f.Food_ID) AS Total_Claimed;
        """
    }
}
# ---------------------------
# TABS: Run 15 Queries
# ---------------------------
tab1, tab2, tab3 = st.tabs(["Provider & Receiver","Donation & Claim","Wastage & Efficiency"])

# helper to run and render query nicely with chart fallback
def run_and_render(sql, title):
    try:
        df = pd.read_sql(sql, engine)
    except Exception as e:
        st.error(f"Query error: {e}")
        return None
    st.subheader(title)
    if df.empty:
        st.info("No data returned.")
        return df
    st.dataframe(df, use_container_width=True)
    # If first column is categorical and second numeric, show bar chart
    if df.shape[1] >= 2 and pd.api.types.is_numeric_dtype(df.iloc[:,1]):
        try:
            chart_df = df.set_index(df.columns[0]).iloc[:,0:1]
            st.bar_chart(chart_df)
        except Exception:
            pass
    return df

# populate tabs
for tab, (group_name, qdict) in zip([tab1, tab2, tab3], queries_grouped.items()):
    with tab:
        st.markdown(f"### {group_name}")
        cols = st.columns(2)
        # show each query in an expander for a clean layout
        i = 0
        for title, sql in qdict.items():
            with st.expander(f" {title}", expanded=(i < 2)):
                run_and_render(sql, title)
            i += 1

# --------------------------- 
# CRUD OPERATIONS (Aligned with your table structure)
# ---------------------------
# Sidebar Action
st.sidebar.header("⚙️ Manage Data")
crud_choice = st.sidebar.radio("Select Table", ["Providers", "Receivers", "Food Listings", "Claims"])

if crud_choice == "Claims":
    action_options = ["Create", "Read", "Update", "Delete", "Complete"]
else:
    action_options = ["Create", "Read", "Update", "Delete"]

action_choice = st.sidebar.selectbox("Action", action_options)
st.subheader(f" {crud_choice} - {action_choice}")

# --------------------------- PROVIDERS CRUD ---------------------------
if crud_choice == "Providers":
    if action_choice == "Create":
        with st.form("add_provider"):
            name = st.text_input("Provider Name")
            ptype = st.text_input("Provider Type")
            city = st.text_input("City")
            contact = st.text_input("Contact")
            address = st.text_area("Address")
            submit = st.form_submit_button(" Add Provider")
            if submit:
                execute_query("""
                    INSERT INTO providers (Name, Type, City, Contact, Address)
                    VALUES (:name, :ptype, :city, :contact, :address);
                """, {"name": name, "ptype": ptype, "city": city, "contact": contact, "address": address})
                st.success(f"Provider '{name}' added successfully!")
    
    elif action_choice == "Read":
        st.subheader("🔍 Search Providers")
        name = st.text_input("Search by Name")
        city = st.text_input("Filter by City")
        ptype = st.text_input("Filter by Provider Type")

        query = "SELECT * FROM providers WHERE 1=1"
        params = {}

        if name:
            query += " AND Name LIKE :name"
            params["name"] = f"%{name}%"
        if city:
            query += " AND City LIKE :city"
            params["city"] = f"%{city}%"
        if ptype:
            query += " AND Type LIKE :ptype"
            params["ptype"] = f"%{ptype}%"

        df = run_query(query + " ORDER BY Provider_ID DESC;", params)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            download_df_button(df, "providers_filtered.csv")
        else:
            st.info("No providers found for the given search.")
    
    elif action_choice == "Update":
        df = run_query("SELECT * FROM providers;")
        pid = st.selectbox("Select Provider ID", df["Provider_ID"])
    
    # Get current data
        current = df[df["Provider_ID"] == pid].iloc[0]
    
        name = st.text_input("Provider Name", value=current["Name"])
        ptype = st.text_input("Provider Type", value=current["Type"])
        city = st.text_input("City", value=current["City"])
        contact = st.text_input("Contact", value=current["Contact"])
        address = st.text_area("Address", value=current["Address"])
    
        if st.button("Update"):
           execute_query("""
              UPDATE providers SET Name=:name, Type=:ptype, City=:city, Contact=:contact, Address=:address
              WHERE Provider_ID=:pid;
              """, {"name": name, "ptype": ptype, "city": city, "contact": contact, "address": address, "pid": pid})
           st.success("Provider updated successfully!")

    elif action_choice == "Delete":
        df = run_query("SELECT * FROM providers;")
        pid = st.selectbox("Select Provider ID", df["Provider_ID"])
        if st.button("Delete Provider"):
            execute_query("DELETE FROM providers WHERE Provider_ID=:pid;", {"pid": pid})
            st.success("Provider deleted!")

# --------------------------- RECEIVERS CRUD ---------------------------
elif crud_choice == "Receivers":
    if action_choice == "Create":
        with st.form("add_receiver"):
            name = st.text_input("Receiver Name")
            rtype = st.text_input("Receiver Type")
            city = st.text_input("City")
            contact = st.text_input("Contact")
            submit = st.form_submit_button(" Add Receiver")
            if submit:
                execute_query("""
                    INSERT INTO receivers (Name, Type, City, Contact)
                    VALUES (:name, :rtype, :city, :contact);
                """, {"name": name, "rtype": rtype, "city": city, "contact": contact})
                st.success(f"Receiver '{name}' added successfully!")

    elif action_choice == "Read":
        st.subheader("🔍 Search Receivers")
        name = st.text_input("Search by Name")
        city = st.text_input("Filter by City")
        rtype = st.text_input("Filter by Receiver Type")

        query = "SELECT * FROM receivers WHERE 1=1"
        params = {}

        if name:
            query += " AND Name LIKE :name"
            params["name"] = f"%{name}%"
        if city:
            query += " AND City LIKE :city"
            params["city"] = f"%{city}%"
        if rtype:
            query += " AND Type LIKE :rtype"
            params["rtype"] = f"%{rtype}%"

        df = run_query(query + " ORDER BY Receiver_ID DESC;", params)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            download_df_button(df, "receivers_filtered.csv")
        else:
            st.info("No receivers found for the given filters.")


    elif action_choice == "Update":
        df = run_query("SELECT * FROM receivers;")
        rid = st.selectbox("Select Receiver ID", df["Receiver_ID"])
    
        current = df[df["Receiver_ID"] == rid].iloc[0]
    
        name = st.text_input("Receiver Name", value=current["Name"])
        rtype = st.text_input("Receiver Type", value=current["Type"])
        city = st.text_input("City", value=current["City"])
        contact = st.text_input("Contact", value=current["Contact"])
    
        if st.button("Update Receiver"):
            execute_query("""
               UPDATE receivers SET Name=:name, Type=:rtype, City=:city, Contact=:contact
               WHERE Receiver_ID=:rid;
               """, {"name": name, "rtype": rtype, "city": city, "contact": contact, "rid": rid})
            st.success("Receiver updated successfully!")


    elif action_choice == "Delete":
        df = run_query("SELECT * FROM receivers;")
        rid = st.selectbox("Select Receiver ID", df["Receiver_ID"])
        if st.button("Delete Receiver"):
            execute_query("DELETE FROM receivers WHERE Receiver_ID=:rid;", {"rid": rid})
            st.success("Receiver deleted!")

# --------------------------- FOOD LISTINGS CRUD ---------------------------
elif crud_choice == "Food Listings":
    if action_choice == "Create":
        with st.form("add_food"):
            food_name = st.text_input("Food Name")
            quantity = st.number_input("Quantity", min_value=1)
            expiry = st.date_input("Expiry Date", date.today())
            provider_id = st.number_input("Provider ID", min_value=1)
            provider_type = st.text_input("Provider Type")
            location = st.text_input("Location")
            food_type = st.text_input("Food Type")
            meal_type = st.text_input("Meal Type")
            submit = st.form_submit_button("➕ Add Food Listing")
            if submit:
                execute_query("""
                    INSERT INTO food_listings (Food_Name, Quantity, Expiry_Date, Provider_ID, Provider_Type, Location, Food_Type, Meal_Type)
                    VALUES (:fname, :qty, :expiry, :pid, :ptype, :loc, :ftype, :mtype);
                """, {"fname": food_name, "qty": quantity, "expiry": expiry, "pid": provider_id,
                      "ptype": provider_type, "loc": location, "ftype": food_type, "mtype": meal_type})
                st.success("Food listing added successfully!")

    elif action_choice == "Read":
        st.subheader("🔍 Search Food Listings")
        fname = st.text_input("Search by Food Name")
        ftype = st.text_input("Filter by Food Type")
        mtype = st.text_input("Filter by Meal Type")
        location = st.text_input("Filter by Location")

        query = """
            SELECT f.Food_ID, f.Food_Name, f.Food_Type, f.Meal_Type, f.Quantity,
               f.Expiry_Date, f.Provider_ID, p.Name AS Provider_Name, f.Location
            FROM food_listings f
            LEFT JOIN providers p ON f.Provider_ID = p.Provider_ID
            WHERE 1=1
            """
        params = {}

        if fname:
            query += " AND f.Food_Name LIKE :fname"
            params["fname"] = f"%{fname}%"
        if ftype:
            query += " AND f.Food_Type LIKE :ftype"
            params["ftype"] = f"%{ftype}%"
        if mtype:
            query += " AND f.Meal_Type LIKE :mtype"
            params["mtype"] = f"%{mtype}%"
        if location:
            query += " AND f.Location LIKE :loc"
            params["loc"] = f"%{location}%"

        df = run_query(query + " ORDER BY f.Food_ID DESC;", params)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            download_df_button(df, "food_listings_filtered.csv")
        else:
            st.info("No food listings found for the given filters.")


    elif action_choice == "Update":
        df = run_query("SELECT * FROM food_listings;")
        fid = st.selectbox("Select Food ID", df["Food_ID"])
    
        current = df[df["Food_ID"] == fid].iloc[0]
    
        food_name = st.text_input("Food Name", value=current["Food_Name"])
        quantity = st.number_input("Quantity", min_value=1, value=current["Quantity"])
        expiry = st.date_input("Expiry Date", value=current["Expiry_Date"])
        provider_type = st.text_input("Provider Type", value=current["Provider_Type"])
        location = st.text_input("Location", value=current["Location"])
        food_type = st.text_input("Food Type", value=current["Food_Type"])
        meal_type = st.text_input("Meal Type", value=current["Meal_Type"])
    
        if st.button("Update Food Listing"):
            execute_query("""
               UPDATE food_listings 
                SET Food_Name=:fname, Quantity=:qty, Expiry_Date=:expiry, Provider_Type=:ptype,
                Location=:loc, Food_Type=:ftype, Meal_Type=:mtype
                WHERE Food_ID=:fid;
                """, {"fname": food_name, "qty": quantity, "expiry": expiry, "ptype": provider_type,
                "loc": location, "ftype": food_type, "mtype": meal_type, "fid": fid})
            st.success("Food listing updated successfully!")


    elif action_choice == "Update":
        df = run_query("SELECT * FROM food_listings;")
        fid = st.selectbox("Select Food ID", df["Food_ID"])
        quantity = st.number_input("New Quantity", min_value=1)
        expiry = st.date_input("New Expiry Date")
        location = st.text_input("New Location")
        if st.button("Update Food Listing"):
            execute_query("""
                UPDATE food_listings 
                SET Quantity=:qty, Expiry_Date=:expiry, Location=:loc
                WHERE Food_ID=:fid;
            """, {"qty": quantity, "expiry": expiry, "loc": location, "fid": fid})
            st.success("Food listing updated successfully!")

    elif action_choice == "Delete":
        df = run_query("SELECT * FROM food_listings;")
        fid = st.selectbox("Select Food ID", df["Food_ID"])
        if st.button("Delete Food Listing"):
            execute_query("DELETE FROM food_listings WHERE Food_ID=:fid;", {"fid": fid})
            st.success("Food listing deleted!")

# --------------------------- CLAIMS CRUD ---------------------------
elif crud_choice == "Claims":
    if action_choice == "Create":
        with st.form("add_claim"):
            receiver_id = st.number_input("Receiver ID", min_value=1)
            food_id = st.number_input("Food ID", min_value=1)
            status = st.selectbox("Status", ["Pending", "Completed"])
            timestamp = st.date_input("Claim Date", date.today())
            submit = st.form_submit_button(" Create Claim")
            if submit:
                execute_query("""
                    INSERT INTO claims (Food_ID, Receiver_ID, Status, Timestamp)
                    VALUES (:fid, :rid, :status, :ts);
                """, {"fid": food_id, "rid": receiver_id, "status": status, "ts": timestamp})
                st.success("Claim created successfully!")


    elif action_choice == "Read":
        st.subheader(" Search Claims")
        status = st.selectbox("Filter by Status", ["", "Pending", "Completed"])
        receiver_name = st.text_input("Search by Receiver Name")
        food_name = st.text_input("Search by Food Name")

        query = """
            SELECT c.Claim_ID, f.Food_Name, r.Name AS Receiver_Name, c.Status, c.Timestamp
            FROM claims c
            LEFT JOIN food_listings f ON c.Food_ID = f.Food_ID
            LEFT JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
            WHERE 1=1
        """
        params = {}

        if status:
            query += " AND c.Status = :status"
            params["status"] = status
        if receiver_name:
            query += " AND r.Name LIKE :rname"
            params["rname"] = f"%{receiver_name}%"
        if food_name:
            query += " AND f.Food_Name LIKE :fname"
            params["fname"] = f"%{food_name}%"

        df = run_query(query + " ORDER BY c.Claim_ID DESC;", params)
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            download_df_button(df, "claims_filtered.csv")
        else:
            st.info("No claims found for the given filters.")


    elif action_choice == "Update":
        df = run_query("SELECT * FROM claims;")
        cid = st.selectbox("Select Claim ID", df["Claim_ID"])
    
        current = df[df["Claim_ID"] == cid].iloc[0]
    
        food_id = st.number_input("Food ID", min_value=1, value=current["Food_ID"])
        receiver_id = st.number_input("Receiver ID", min_value=1, value=current["Receiver_ID"])
        status = st.selectbox("Status", ["Pending", "Completed"], index=0 if current["Status"]=="Pending" else 1)
        timestamp = st.date_input("Timestamp", value=current["Timestamp"].date())
    
        if st.button("Update Claim"):
           execute_query("""
              UPDATE claims 
              SET Food_ID=:fid, Receiver_ID=:rid, Status=:status, Timestamp=:ts
              WHERE Claim_ID=:cid;
              """, {"fid": food_id, "rid": receiver_id, "status": status, "ts": timestamp, "cid": cid})
           st.success("Claim updated successfully!")

    elif action_choice == "Delete":
        df = run_query("SELECT * FROM claims;")
        cid = st.selectbox("Select Claim ID", df["Claim_ID"])
        if st.button("Delete Claim"):
            execute_query("DELETE FROM claims WHERE Claim_ID=:cid;", {"cid": cid})
            st.success("Claim deleted!")

    elif action_choice == "Complete":
        df_pending = run_query("""
            SELECT c.Claim_ID, f.Food_Name, r.Name AS Receiver, c.Status
            FROM claims c
            JOIN food_listings f ON c.Food_ID = f.Food_ID
            JOIN receivers r ON c.Receiver_ID = r.Receiver_ID
            WHERE c.Status <> 'Completed'
            ORDER BY c.Claim_ID DESC;
        """)
        if not df_pending.empty:
            claim_select = st.selectbox(
                "Select Claim to Mark as Completed",
                options=[f"{row.Claim_ID} - {row.Food_Name} ({row.Receiver}) [{row.Status}]" for _, row in df_pending.iterrows()]
            )
            if st.button("Mark as Completed"):
                cid = int(claim_select.split(" - ")[0])
                execute_query("UPDATE claims SET Status='Completed' WHERE Claim_ID=:cid;", {"cid": cid})
                st.success("Claim marked as Completed!")
        else:
            st.info("No pending claims found.")


# ---------------------------
# QUICK VIEW SECTION
# ---------------------------
st.markdown("---")
st.subheader("Latest Records")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.caption("Providers")
    provs = run_query("SELECT * FROM providers ORDER BY Provider_ID DESC LIMIT 10;")
    st.dataframe(provs, use_container_width=True, height=200)

with col2:
    st.caption("Receivers")
    recs = run_query("SELECT * FROM receivers ORDER BY Receiver_ID DESC LIMIT 10;")
    st.dataframe(recs, use_container_width=True, height=200)

with col3:
    st.caption("Food Listings")
    foods = run_query("SELECT * FROM food_listings ORDER BY Food_ID DESC LIMIT 10;")
    st.dataframe(foods, use_container_width=True, height=200)

with col4:
    st.caption("Claims")
    claims = run_query("SELECT * FROM claims ORDER BY Claim_ID DESC LIMIT 10;")
    st.dataframe(claims, use_container_width=True, height=200)





# ======= Contact Directory =======
st.markdown("---")
st.subheader("📞 Provider Contact Directory")
contact_view = st.radio("View", ["Card View","Table View"], horizontal=True)
try:
    provs = run_query("SELECT Name, City, Contact, Address FROM providers ORDER BY Name LIMIT 500;")
    if contact_view=="Card View":
        for _, r in provs.iterrows():
            st.markdown(f'<div class="card card--amber"><strong>{r.Name}</strong><div class="small-note">{r.City} • {r.Address}</div><div class="small-note">Contact: {r.Contact}</div></div>', unsafe_allow_html=True)
    else:
        st.dataframe(provs, use_container_width=True)
        download_df_button(provs,"providers_contacts.csv")
except:
    st.write("No contact data available.")