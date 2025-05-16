import pandas as pd
import streamlit as st
import mariadb
import altair as alt

# Function to connect to MariaDB
def connect_to_mariadb():
    try:
        conn = mariadb.connect(
            host="localhost", 
            user="root", 
            password="", 
            database="project", 
            port=3306
        )
        return conn
    except mariadb.Error as err:
        st.error(f"Error: {err}")
        return None

# Function to execute SQL queries and return results
def execute_query(query, params=None):
    conn = connect_to_mariadb()
    if conn is None:
        return []
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# Sidebar Metrics 
mycursor = connect_to_mariadb().cursor(dictionary=True)

mycursor.execute("SELECT COUNT(*) AS total FROM competitors")
total_competitors = mycursor.fetchone()['total']

mycursor.execute("SELECT COUNT(DISTINCT country) AS countries FROM competitors")
countries = mycursor.fetchone()['countries']

mycursor.execute("SELECT MAX(points) AS max_points FROM competitor_rankings")
max_points = mycursor.fetchone()['max_points']

st.sidebar.header('Summary Statistics')
st.sidebar.metric("Total Competitors", total_competitors)
st.sidebar.metric("Countries Represented", countries)
st.sidebar.metric("Highest Points", max_points)

# Filters - only fetch required fields
mycursor.execute("SELECT DISTINCT name FROM competitors ORDER BY name")
names = ['All'] + [row['name'] for row in mycursor.fetchall()]

mycursor.execute("SELECT DISTINCT country FROM competitors ORDER BY country")
countries_list = ['All'] + [row['country'] for row in mycursor.fetchall() if row['country']]

search_name = st.sidebar.selectbox("Search by name", names)
country_filter = st.sidebar.selectbox("Filter by Country", countries_list)

# For slider limits (rank and points)
mycursor.execute("SELECT MIN(rank) AS min_rank, MAX(rank) AS max_rank FROM competitor_rankings")
rank_limits = mycursor.fetchone()
rank_min, rank_max = st.sidebar.slider("Rank Range", rank_limits['min_rank'], rank_limits['max_rank'], (rank_limits['min_rank'], rank_limits['max_rank']))

mycursor.execute("SELECT MIN(points) AS min_p, MAX(points) AS max_p FROM competitor_rankings")
points_limits = mycursor.fetchone()
points_min, points_max = st.sidebar.slider("Points Range", points_limits['min_p'], points_limits['max_p'], (points_limits['min_p'], points_limits['max_p']))

# Dynamic SQL Query with filters
query = """
SELECT c.name, c.country, r.rank, r.points, r.movement, r.competitions_played
FROM competitors c
JOIN competitor_rankings r ON c.id = r.competitor_id
WHERE r.rank BETWEEN %s AND %s AND r.points BETWEEN %s AND %s
"""
params = (rank_min, rank_max, points_min, points_max)

if search_name != 'All':
    query += " AND c.name = %s"
    params += (search_name,)  
if country_filter != 'All':
    query += " AND c.country = %s"
    params += (country_filter,) 

filtered_data = execute_query(query, params)

# Title
st.markdown("<h1 style='text-align: center; color: #4B8BBE;'>🎾 Global Tennis Competitor Dashboard</h1>", unsafe_allow_html=True)
st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🏷️ Filters", "🌟 Filtered Results", "🌐 Country-Wise Analysis", "🏆 Leaderboards"])

# Tab 1
with tab1:
    st.header("Set Your Filters in Sidebar")
    st.info("Use the sidebar to filter competitors by name, country, rank, and points.")

# Tab 2
with tab2:
    st.header(":dart: Filtered Competitors")
    st.write(f"Showing **{len(filtered_data)}** competitors based on the filters.")
    if filtered_data:
        st.table([{k: row[k] for k in ['name', 'country', 'rank', 'points']} for row in filtered_data])

        selected_names = [r['name'] for r in filtered_data]
        selected_name = st.selectbox("Select a competitor to view details:", selected_names)
        selected = next(r for r in filtered_data if r['name'] == selected_name)
        st.subheader(f"Details for {selected_name}")
        st.write({
            "Name": selected['name'],
            "Country": selected['country'],
            "Rank": selected['rank'],
            "Movement": selected['movement'],
            "Competitions Played": selected['competitions_played'],
            "Points": selected['points']
        })
    else:
        st.warning("No competitors found.")

# Tab 3: Country-wise aggregation (fast SQL GROUP BY)
with tab3:
    st.header("Country-Wise Analysis")
    query = """
        SELECT c.country, COUNT(*) AS total_competitors, ROUND(AVG(r.points), 2) AS avg_points
        FROM competitors c
        JOIN competitor_rankings r ON c.id = r.competitor_id
        WHERE c.country IS NOT NULL
        GROUP BY c.country
        ORDER BY total_competitors DESC
    """
    country_data = execute_query(query)

    # Convert data to DataFrame for Altair chart
    country_df = pd.DataFrame(country_data)

    st.write("### Competitor Stats by Country")
    st.table(country_df)

    # Plotting with Altair
    chart = alt.Chart(country_df).mark_bar().encode(
        x=alt.X('country:N', sort='-y'),
        y='total_competitors:Q',
        tooltip=['country', 'total_competitors', 'avg_points']
    ).properties(title="Total Competitors by Country", width=700)

    st.altair_chart(chart)

# Tab 4: Leaderboards
with tab4:
    st.header("Top Competitors")

    query_rank = """
        SELECT c.name, c.country, r.rank, r.points
        FROM competitors c
        JOIN competitor_rankings r ON c.id = r.competitor_id
        ORDER BY r.rank ASC
        LIMIT 10
    """
    top_by_rank = execute_query(query_rank)

    query_points = """
        SELECT c.name, c.country, r.rank, r.points
        FROM competitors c
        JOIN competitor_rankings r ON c.id = r.competitor_id
        ORDER BY r.points DESC
        LIMIT 10
    """
    top_by_points = execute_query(query_points)

    st.subheader("Top 10 by Rank")
    st.table(top_by_rank)

    st.subheader("Top 10 by Points")
    st.table(top_by_points)

    # Convert to DataFrame for Altair chart
    top_by_points_df = pd.DataFrame(top_by_points)

    # Plotting with Altair
    chart_points = alt.Chart(top_by_points_df).mark_bar().encode(
        x=alt.X('name:N', sort='-y'),
        y='points:Q',
        tooltip=['name', 'points', 'rank']
    ).properties(title="Top 10 Competitors by Points", width=700)

    st.altair_chart(chart_points)