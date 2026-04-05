import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import numpy as np

# --- Page Configuration ---
st.set_page_config(page_title="Nassau Candy Logistics", layout="wide")

@st.cache_data
def load_data():
    # Load your dataset
    df = pd.read_csv('Nassau Candy Distributor.csv') # Ensure filename matches
    
    # 1. Product to Factory Mapping
    factory_mapping = {
        'Wonka Bar - Nutty Crunch Surprise': 'Lot\'s O\' Nuts',
        'Wonka Bar - Fudge Mallows': 'Lot\'s O\' Nuts',
        'Wonka Bar -Scrumdiddlyumptious': 'Lot\'s O\' Nuts',
        'Wonka Bar - Milk Chocolate': 'Wicked Choccy\'s',
        'Wonka Bar - Triple Dazzle Caramel': 'Wicked Choccy\'s',
        'Laffy Taffy': 'Sugar Shack', 'SweeTARTS': 'Sugar Shack',
        'Nerds': 'Sugar Shack', 'Fun Dip': 'Sugar Shack',
        'Fizzy Lifting Drinks': 'Sugar Shack',
        'Everlasting Gobstopper': 'Secret Factory',
        'Hair Toffee': 'The Other Factory',
        'Lickable Wallpaper': 'Secret Factory',
        'Wonka Gum': 'Secret Factory',
        'Kazookles': 'The Other Factory'
    }
    
    # 2. Factory Coordinates
    factory_coords = {
        'Lot\'s O\' Nuts': [32.881893, -111.768036],
        'Wicked Choccy\'s': [32.076176, -81.088371],
        'Sugar Shack': [48.11914, -96.18115],
        'Secret Factory': [41.446333, -90.565487],
        'The Other Factory': [35.1175, -89.971107]
    }

    # 3. Data Processing
    df['Factory'] = df['Product Name'].map(factory_mapping)
    df['Order Date'] = pd.to_datetime(
    df['Order Date'],
    format='mixed',
    dayfirst=True,
    errors='coerce'
)
    df['Ship Date'] = pd.to_datetime(df['Ship Date'])
    df['Lead Time'] = (df['Ship Date'] - df['Order Date']).dt.days
    df = df[df['Lead Time'] >= 0] # Remove errors
    
    # Add coordinates to main DF
    df['lat_f'] = df['Factory'].apply(lambda x: factory_coords[x][0] if x in factory_coords else None)
    df['lon_f'] = df['Factory'].apply(lambda x: factory_coords[x][1] if x in factory_coords else None)
    
    return df

df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filter Options")
ship_mode = st.sidebar.multiselect("Select Ship Mode", options=df['Ship Mode'].unique(), default=df['Ship Mode'].unique())
selected_factory = st.sidebar.multiselect("Select Factory", options=df['Factory'].unique(), default=df['Factory'].unique())
threshold = st.sidebar.slider("Delay Threshold (Days)", 0, 10, 5)

# Filtered Data
mask = df['Ship Mode'].isin(ship_mode) & df['Factory'].isin(selected_factory)
filtered_df = df[mask]

# --- Dashboard Header ---
st.title("Candy Route Efficiency Dashboard")
st.markdown(f"Analyzing shipping performance for **Nassau Candy Distributor**")

# --- Top Metrics ---
m1, m2, m3 = st.columns(3)
m1.metric("Avg Lead Time", f"{round(filtered_df['Lead Time'].mean(), 2)} Days")
m2.metric("Total Shipments", f"{len(filtered_df)}")
m3.metric("Delay Rate", f"{round((len(filtered_df[filtered_df['Lead Time'] > threshold]) / len(filtered_df)) * 100, 1)}%")

st.divider()

# --- Visualizations ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Route Efficiency (Top 10 Fastest)")
    route_data = filtered_df.groupby(['Factory', 'State/Province'])['Lead Time'].mean().reset_index()
    route_data = route_data.sort_values('Lead Time').head(10)
    fig = px.bar(route_data, x='Lead Time', y='State/Province', color='Factory', orientation='h',
                 title="Fastest State Deliveries by Factory")
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Ship Mode Comparison")
    mode_data = filtered_df.groupby('Ship Mode')['Lead Time'].mean().reset_index()
    fig2 = px.pie(mode_data, values='Lead Time', names='Ship Mode', hole=0.4,
                  title="Average Lead Time Split")
    st.plotly_chart(fig2, use_container_width=True)

# --- Geographic Map ---
st.subheader("Geographic Shipping Map")
# For a basic visualization, we show factory locations. 
# In a full version, you'd add state centroids to draw arcs.
view_state = pdk.ViewState(latitude=39.8283, longitude=-98.5795, zoom=3, pitch=45)
layer = pdk.Layer(
    "ScatterplotLayer",
    filtered_df.dropna(subset=['lat_f', 'lon_f']),
    get_position='[lon_f, lat_f]',
    get_color='[200, 30, 0, 160]',
    get_radius=100000,
)
st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state))

# --- Raw Data Drill-down ---
if st.checkbox("Show Raw Data"):
    st.write(filtered_df)
