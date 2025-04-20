import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import altair as alt


username = 'root'
password = ''
host = 'localhost'
port = '3306'
database = 'project'
connection_url = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
engine = create_engine(connection_url)


competitors_df = pd.read_sql("SELECT * FROM competitors", engine)
competitor_rankings_df = pd.read_sql("SELECT * FROM competitor_rankings", engine)


merged_df = pd.merge(competitors_df, competitor_rankings_df, left_on='id', right_on='competitor_id', how='inner')

st.markdown("<h1 style='text-align: center; color: #4B8BBE;'>🎾 Global Tennis Competitor Dashboard</h1>", unsafe_allow_html=True)
st.markdown("---")  

# Sidebar for 1st statement
st.sidebar.header('Summary Statistics')
st.sidebar.metric("Total Competitors", competitors_df.shape[0])
st.sidebar.metric("Countries Represented", competitors_df['country'].nunique())
st.sidebar.metric("Highest Points", competitor_rankings_df['points'].max())

# Sidebar: Filters for 2nd problem statement 
st.sidebar.title("🔍 Filter Competitors")
name_options = ['All'] + sorted(competitors_df['name'].dropna().unique().tolist())
search_name = st.sidebar.selectbox("Search by name", name_options)
country_filter = st.sidebar.selectbox("Filter by Country", ['All'] + sorted(competitors_df['country'].dropna().unique().tolist()))
rank_min, rank_max = st.sidebar.slider("Rank Range", int(merged_df['rank'].min()), int(merged_df['rank'].max()), (int(merged_df['rank'].min()), int(merged_df['rank'].max())))
points_threshold = st.sidebar.slider("Points Range", int(merged_df['points'].min()), int(merged_df['points'].max()), (int(merged_df['points'].min()), int(merged_df['points'].max())))

# for doing filtering in sidebars
filtered_df = merged_df.copy()
if search_name != 'All':
    filtered_df = filtered_df[filtered_df['name'] == search_name]

if country_filter != 'All':
    filtered_df = filtered_df[filtered_df['country'] == country_filter]
filtered_df = filtered_df[(filtered_df['rank'].between(rank_min, rank_max)) & (filtered_df['points'].between(*points_threshold))]

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🏷️ Filters", "🌟 Filtered Results", "🌐 Country-Wise Analysis", "🏆 Leaderboards"])

#Tab 1: To tell users to do some filtering
with tab1:
    st.header("Set Your Filters in Sidebar")
    st.info("Use the sidebar to filter competitors by name, country, rank, and points.")

# Tab 2: based on filtering, results of those
with tab2:
    st.header(":dart: Filtered Competitors")
    st.write(f"Showing **{filtered_df.shape[0]}** competitors based on the filters.")
    st.dataframe(filtered_df[['name', 'country', 'rank', 'points']])

    # 3rd problem statement 
    competitor_names = filtered_df['name'].dropna().unique().tolist()
    if competitor_names:
        selected_competitor = st.selectbox("Select a competitor to view details:", competitor_names, key='competitor_dropdown')
        comp_details = filtered_df[filtered_df['name'] == selected_competitor].iloc[0]
        st.subheader(f"Details for {selected_competitor}")
        st.write({
            "Name": comp_details['name'],
            "Country": comp_details['country'],
            "Rank": comp_details['rank'],
            "Movement": comp_details['movement'],
            "Competitions Played": comp_details['competitions_played'],
            "Points": comp_details['points']
        })
    else:
        st.warning("No competitors found.")

# 4th problem statement
with tab3:
    st.header("Country-Wise Analysis")
    country_df = merged_df.groupby('country').agg(
        total_competitors=('name', 'count'),
        avg_points=('points', 'mean')
    ).reset_index()

    st.write("### Competitor Stats by Country")
    st.dataframe(country_df)

    chart = alt.Chart(country_df).mark_bar().encode(
        x=alt.X('country:N', sort='-y'),
        y='total_competitors:Q',
        tooltip=['country', 'total_competitors', 'avg_points']
    ).properties(title="Total Competitors by Country", width=700)
    st.altair_chart(chart)

# 5th problem statement
with tab4:
    st.header("Top Competitors")
    top_ranks = merged_df.sort_values(by='rank').head(10)
    top_points = merged_df.sort_values(by='points', ascending=False).head(10)

    st.subheader("Top 10 by Rank")
    st.dataframe(top_ranks[['name', 'country', 'rank', 'points']])

    st.subheader("Top 10 by Points")
    st.dataframe(top_points[['name', 'country', 'points', 'rank']])

    chart_points = alt.Chart(top_points).mark_bar().encode(
        x=alt.X('name:N', sort='-y'),
        y='points:Q',
        tooltip=['name', 'points', 'rank']
    ).properties(title="Top 10 Competitors by Points", width=700)
    st.altair_chart(chart_points)

engine.dispose()
