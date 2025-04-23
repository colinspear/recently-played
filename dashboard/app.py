import streamlit as st
import pandas as pd
import altair as alt
import os

st.set_page_config(page_title="Spotify Listening Dashboard", layout="wide")
st.title("Spotify Listening Dashboard")

# --- Load data ---
@st.cache_data
def load_data() -> pd.DataFrame:
    url = os.getenv("LISTENING_CSV_URL")
    
    if url:
        try:
            return pd.read_csv(url, parse_dates=["played_at_local"])
        except Exception as e:
            st.error(f"Failed to load data from URL: {e}")
            return pd.DataFrame()
    
    local_path = "../data/processed/listening_data.csv"
    if os.path.exists(local_path):
        return pd.read_csv(local_path, parse_dates=["played_at_local"])

    st.error("No data source found. Set LISTENING_CSV_URL or provide local file.")
    return pd.DataFrame()

df = load_data()
if df.empty:
    st.stop()

# --- Timestamp ---
last_ts = df["played_at_local"].max()
st.markdown(f"**Last updated:** {last_ts.strftime('%Y-%m-%d %H:%M UTC')}")

# --- Summary stats ---
st.header("Summary Stats")
total_time = df["duration_ms"].sum() / 60000  # minutes
total_tracks = len(df)
unique_artists = df["artist_name"].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Total Listening Time (min)", f"{int(total_time):,}")
col2.metric("Total Tracks", f"{total_tracks:,}")
col3.metric("Unique Artists", f"{unique_artists:,}")

# --- Daily Listening Time: Last 7 Days vs Weekday Avg ---
st.subheader("Listening Time: Last 7 Days vs 60-Day Weekday Average")
df["date"] = pd.to_datetime(df["date"])
df["weekday"] = df["date"].dt.day_name()

df_60 = df[df["date"] >= pd.Timestamp.now() - pd.Timedelta(days=60)].copy()
df_7 = df_60[df_60["date"] >= pd.Timestamp.now() - pd.Timedelta(days=7)].copy()

df_7 = (
    df_7.groupby(["date", "weekday"])["duration_ms"]
    .sum()
    .div(60000)
    .reset_index()
    .rename(columns={"duration_ms": "minutes"})
)

weekday_counts = df_60.groupby("weekday")["date"].nunique()
weekday_totals = df_60.groupby("weekday")["duration_ms"].sum().div(60000)
weekday_avg = (weekday_totals / weekday_counts).reset_index(name="avg_minutes")

weekday_order = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
df_7["weekday"] = pd.Categorical(df_7["weekday"], categories=weekday_order, ordered=True)
weekday_avg["weekday"] = pd.Categorical(weekday_avg["weekday"], categories=weekday_order, ordered=True)

df_7 = (
    df_7.set_index("weekday")
        .reindex(weekday_order)
        .reset_index()
        .fillna({"minutes": 0})
)

df_7["source"] = "Last 7 Days"
weekday_avg["source"] = "60-Day Avg"

line = alt.Chart(df_7).mark_line(point=True).encode(
    x=alt.X("weekday", sort=weekday_order, title="Day of Week", axis=alt.Axis(labelAngle=0)),
    y=alt.Y("minutes", title="Minutes Listened"),
    color=alt.Color("source", scale=alt.Scale(scheme="category10")),
    tooltip=["date:T", "minutes"]
)

dots = alt.Chart(weekday_avg).mark_point(size=80).encode(
    x="weekday",
    y="avg_minutes",
    color=alt.Color("source", scale=alt.Scale(scheme="category10")),
    tooltip=["weekday", "avg_minutes"]
)

st.altair_chart(line + dots, use_container_width=True)

# --- Top Artists and Tracks ---
st.subheader("Top Artists and Tracks (Last 30 Days)")
recent = df[df["played_at_local"] >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=30)]

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Top Artists**")
    top_artists = recent["artist_name"].value_counts().reset_index()
    top_artists.columns = ["Artist", "Count"]
    st.dataframe(top_artists.head(10), hide_index=True)

with col2:
    st.markdown("**Top Tracks**")
    top_tracks = recent["track_name"].value_counts().reset_index()
    top_tracks.columns = ["Track", "Count"]
    st.dataframe(top_tracks.head(10), hide_index=True)

# --- Hourly Listening ---
st.subheader("Listening by Hour of Day")
full_hours = pd.DataFrame({"Hour": list(range(24))})
df_hour = df["hour"].value_counts().sort_index().reset_index()
df_hour.columns = ["Hour", "Count"]
df_hour = full_hours.merge(df_hour, on="Hour", how="left").fillna(0).astype({"Count": int})

hour_chart = alt.Chart(df_hour).mark_bar().encode(
    x=alt.X("Hour:O", sort="ascending", axis=alt.Axis(labelAngle=0)),
    y="Count:Q"
)
st.altair_chart(hour_chart, use_container_width=True)

# --- Genre Breakdown ---
st.subheader("Genre Distribution")
genres = df["genre"].value_counts().reset_index()
genres.columns = ["Genre", "Count"]
st.bar_chart(genres.head(15).set_index("Genre"))
