import streamlit as st
import pandas as pd
import altair as alt
import folium
from streamlit_folium import folium_static
import json
st.set_page_config(layout="wide")
@st.cache_data
def load_data():
    data = pd.read_csv('data/honeybee_colonies_2023_03_26.csv')
    return data

data = load_data()

# Add the st.cache decorator above the function definition for loading the GeoJSON data
@st.cache_data
def load_geojson_data():
    file_path = "data/us_states.json"
    with open(file_path, "r") as f:
        geojson_data = json.load(f)
    return geojson_data

geojson_data = load_geojson_data()




st.title("Honeybee Colony Inventory and Colony Loss")
#  
# Sample DataFrame (use your own data)
data = pd.read_csv('data/honeybee_colonies_2023_03_26.csv')
data = data[['Year','Period','State' ,'Inventory','Colony_Loss','Colony_loss_pct']].copy()
data['Colony_loss_pct'] = pd.to_numeric(data['Colony_loss_pct'], errors='coerce')
data['State'] = data['State'].str.title()
data_without_2022 = data[data['Year'] != 2022]

# Calculate average values for each year and state
data_grouped = data_without_2022.groupby(["Year", "State"]).agg({"Inventory": "mean", "Colony_Loss": "mean", "Colony_loss_pct": "mean"}).reset_index()

data3 = data_without_2022.sort_values(by=['State','Year'])
#data3.set_index('Period', inplace=True)
def introduction():
    
    st.header("Introduction")
    st.write("""
    
    """)
   
    # Define columns
    col1, col2 = st.columns([3, 2], gap="small")

    # Add content to the columns
    with col1:
        st.image("data/honeybee.jpg", width=550)

    with col2:
        st.write("""
        Did you know that honeybees are critical to food production in the United States? They play a crucial role in pollinating crops, and are responsible for around one-third of the food consumed in the country. In fact, honeybees are essential to the success of many important crops, including almonds, apples, blueberries, cherries, and cucumbers
        
       Unfortunately, honeybee populations have been declining due to factors like habitat loss, exposure to pesticides, diseases, and climate change. This is a cause for concern, as it could impact food production and the economy. To address this issue, conservation efforts and research into alternative pollination methods are underway to protect honeybees and ensure the continued success of US food production.
        """)
                
    

def interactive_map():
    st.header("Interactive Map")
    year = st.selectbox("Select year", data_grouped["Year"].unique())

    # Filter data for the selected year
    year_data = data_grouped[data_grouped["Year"] == year]

    # Create a base map
    m = folium.Map(location=[37.8, -96], zoom_start=4)


    # Get the GeoJSON data
    file_path = "data/us_states.json"
    with open(file_path, "r") as f:
     geojson_data = json.load(f)


    # Merge the year_data with the GeoJSON data
    for feature in geojson_data["features"]:
        state_data = year_data.loc[year_data["State"] == feature["properties"]["name"]]
        if not state_data.empty:
            feature["properties"]["Inventory"] = state_data["Inventory"].values[0]
            feature["properties"]["Colony_Loss"] = state_data["Colony_Loss"].values[0]
            feature["properties"]["Colony_loss_pct"] = f"{state_data['Colony_loss_pct'].values[0]:.2%}%"
        else:
            feature["properties"]["Inventory"] = "No data Available"
            feature["properties"]["Colony_Loss"] = "No data Available"
            feature["properties"]["Colony_loss_pct"] = "No data Available"
    # Add Choropleth layer
    choropleth = folium.Choropleth(
        geo_data=geojson_data,
        name="choropleth",
        data=year_data,
        columns=["State", "Colony_loss_pct"],
        key_on="feature.properties.name",
        fill_color="YlOrBr",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Average Colony Percent Loss",
        highlight=True
    ).add_to(m)

    # Add tooltip
    tooltip = folium.features.GeoJsonTooltip(
        fields=["name", "Inventory", "Colony_Loss", "Colony_loss_pct"],
        aliases=["State", "Average Colony Inventory", "Average Hive Loss", "Average Pct Hive Loss"],
        localize=True,
        sticky = True,
        max_width = 500
    )

    # Add GeoJson layer with tooltip to the choropleth
    folium.GeoJson(
        choropleth.geojson.data,
        name="tooltip",
        tooltip=tooltip,
        style_function=lambda x: {'color': 'black', 'weight': 0.5, 'fillOpacity': 0}
    ).add_to(m)

    # Display the map
    folium_static(m)

def line_chart():
    st.write("## Line Chart")
    variable = st.selectbox("Select variable", ["Inventory", "Colony_loss_pct"])
    states = st.multiselect("Select States", data3['State'].unique())
    if len(states) > 3:
        st.warning("Please select no more than 3 states.")
        return

    # Filter out the year 2022
    filtered_data = data3.loc[data3['Year'] != 2022]

    if len(states) > 0:
        filtered_data = filtered_data.loc[filtered_data['State'].isin(states)]

        # Aggregate the data by State and Year, computing the mean Inventory, Colony_Loss, and Colony_loss_pct
        aggregated_data = filtered_data.groupby(['State', 'Year']).agg({'Inventory': 'mean', 'Colony_Loss': 'mean', 'Colony_loss_pct': 'mean'}).reset_index()

        # Define the custom color scheme
        color_scheme = ["blue", "orange", "purple"]

        # Define y-axis title
        y_axis_title = f'Average {variable}'
        if variable == 'Colony_loss_pct':
            y_axis_title += ' (%)'

        # Create a line chart comparing the average inventory and colony loss by year for the selected states
        chart = alt.Chart(aggregated_data).mark_line().encode(
            x=alt.X('Year:N', axis=alt.Axis(title='Year')),
            y=alt.Y(f'mean({variable}):Q', axis=alt.Axis(title=y_axis_title, format='.0f' if variable == 'Inventory' else '.2%', tickCount=5)),
            color=alt.Color('State:N', scale=alt.Scale(range=color_scheme)),
            tooltip=[
                alt.Tooltip('State:N', title='State'),
                alt.Tooltip('Year:N', title='Year'),
                alt.Tooltip('mean(Inventory):Q', title='Average Inventory', format=',.0f'),
                alt.Tooltip('mean(Colony_Loss):Q', title='Average Colony Loss', format=',.0f'),
                alt.Tooltip('mean(Colony_loss_pct):Q', title='Average Percent Colony Loss', format='.2%')
            ]
        ).properties(
            width=800,
            height=400
        )

        st.altair_chart(chart)
    else:
        st.warning("Please select at least one state to display the chart.")



def more_information():
    st.header("More Information")
    st.write("""
    This section can contain more information about honeybee colonies, their impact on agriculture, or any other relevant content. You can also add external resources or links for users to explore further.
    """)
pages = {
    "Introduction": introduction,
    "Interactive Map": interactive_map,
    "Line Chart": line_chart,
    "More Information": more_information,
}

st.sidebar.title("Navigation")
selected_page = st.sidebar.radio("Select a page", list(pages.keys()))

# Display the selected page
pages[selected_page]()
