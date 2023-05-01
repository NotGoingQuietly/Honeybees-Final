import streamlit as st
import pandas as pd
import altair as alt
import folium
from streamlit_folium import folium_static
import json
import requests
st.set_page_config(layout="wide")
st.title("Honeybee Colony Inventory and Colony Loss")
#  
# Sample DataFrame (use your own data)
data = pd.read_csv('data/honeybee_colonies_2023_03_26.csv')
data = data[['Year','Period','State' ,'Inventory','Colony_Loss','Colony_loss_pct']].copy()
data['Colony_loss_pct'] = pd.to_numeric(data['Colony_loss_pct'], errors='coerce')
data['State'] = data['State'].str.title()
# Calculate average values for each year and state
data_grouped = data.groupby(["Year", "State"]).agg({"Inventory": "mean", "Colony_Loss": "mean", "Colony_loss_pct": "mean"}).reset_index()

data2 = data[['Year','Period','State' ,'Inventory','Colony_Loss']].copy()
data3 = data2.sort_values(by=['State','Year'])
data3.set_index('Period', inplace=True)
def introduction():
    st.header("Introduction")
    st.write("""
    Honeybees play a vital role in food production through their pollination services. This app uses data to explore the health of honeybee colonies in the United States.
    """)
    st.image("data/honeybee.jpg")  
                


def interactive_map():
    st.header("Interactive Map")
    year = st.selectbox("Select year", data_grouped["Year"].unique())

    # Filter data for the selected year
    year_data = data_grouped[data_grouped["Year"] == year]

    # Create a base map
    m = folium.Map(location=[37.8, -96], zoom_start=4)

    # Get the GeoJSON data
    url = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
    geojson_data = json.loads(requests.get(url).text)

    # Merge the year_data with the GeoJSON data
    for feature in geojson_data["features"]:
        state_data = year_data.loc[year_data["State"] == feature["properties"]["name"]]
        if not state_data.empty:
            feature["properties"]["Inventory"] = state_data["Inventory"].values[0]
            feature["properties"]["Colony_Loss"] = state_data["Colony_Loss"].values[0]
            feature["properties"]["Colony_loss_pct"] = state_data["Colony_loss_pct"].values[0]
        else:
            feature["properties"]["Inventory"] = None
            feature["properties"]["Colony_Loss"] = None
            feature["properties"]["Colony_loss_pct"] = None
    # Add Choropleth layer
    choropleth = folium.Choropleth(
        geo_data=geojson_data,
        name="choropleth",
        data=year_data,
        columns=["State", "Inventory"],
        key_on="feature.properties.name",
        fill_color="BuPu",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Average Colony Percent Loss",
        highlight=True
    ).add_to(m)

    # Add tooltip
    tooltip = folium.features.GeoJsonTooltip(
        fields=["name", "Inventory", "Colony_Loss", "Colony_loss_pct"],
        aliases=["State", "Average Colony Inventory", "Average Hive Loss", "Average Percentage Hive Loss"],
        localize=True,
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


import altair as alt

def bar_line_chart():
    st.write("## Bar and Line Chart")
    variable = st.selectbox("Select variable", ["Inventory", "Colony_Loss"])
    states = st.multiselect("Select States", data3['State'].unique())
    if len(states) > 3:
        st.warning("Please select no more than 3 states.")
        return

    years = st.multiselect("Select years", sorted(data3['Year'].unique()), default=sorted(data3['Year'].unique()))

    if len(states) > 0 and len(years) > 0:
        filtered_data = data3.loc[data3['Year'].isin(years) & data3['State'].isin(states)]

        # Aggregate the data by State and Year, computing the mean Inventory and Colony_Loss
        aggregated_data = filtered_data.groupby(['State', 'Year']).agg({'Inventory': 'mean', 'Colony_Loss': 'mean'}).reset_index()

        # Create a bar chart comparing the average inventory and colony loss by year for the selected states
        chart = alt.Chart(aggregated_data).mark_bar().encode(
            x=alt.X('Year:N', axis=alt.Axis(title='Year')),
            y=alt.Y(f'mean({variable}):Q', axis=alt.Axis(title=f'Average {variable}')),
            color='State:N',
            column='State:N'
        ).properties(
            width=150,
            height=300
        )

        st.altair_chart(chart)
    else:
        st.warning("Please select at least one state and one year to display the chart.")
        
def more_information():
    st.header("More Information")
    st.write("""
    This section can contain more information about honeybee colonies, their impact on agriculture, or any other relevant content. You can also add external resources or links for users to explore further.
    """)
pages = {
    "Introduction": introduction,
    "Interactive Map": interactive_map,
    "Bar/Line Chart": bar_line_chart,
    "More Information": more_information,
}

st.sidebar.title("Navigation")
selected_page = st.sidebar.radio("Select a page", list(pages.keys()))

# Display the selected page
pages[selected_page]()
