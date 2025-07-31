import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
DATA_PATH = "draft_picks.csv"
CONF_PATH = "conferences.csv"
df = pd.read_csv(DATA_PATH)
conf_df = pd.read_csv(CONF_PATH)

# Create mapping from college to conference
college_to_conf = conf_df.set_index("Team")["Conference"].to_dict()
df["conference"] = df["college"].map(college_to_conf).fillna("Non-Power Conference")

# Group similar positions
# position_map = {
#     "OT": "OL", "OG": "OL", "C": "OL",
#     "P": "ST", "K": "ST",
#     "DT": "DL"
# }
# df["position"] = df["position"].replace(position_map)

# Page config
st.set_page_config(page_title="NFL Draft Landing Page", layout="wide")

# Color scheme
PRIMARY_COLOR = "#be123c"
ACCENT_COLOR = "#dc2626"
BACKGROUND_COLOR = "#0F172A"
TEXT_COLOR = "#F1F5F9"
HEATMAP_COLORS = ["#fee2e2", "#fca5a5", "#f87171", "#ef4444", "#dc2626"]

# Header
st.markdown(
    f"""
    <div style="background-color:{BACKGROUND_COLOR}; padding:2rem 2rem 1.5rem 2rem; border-left:8px solid {ACCENT_COLOR}; margin-bottom:2rem;">
        <h1 style="color:{TEXT_COLOR}; font-size:2.25rem; margin:0 0 0.25rem 0;">Data 760 - NFL Draft Data Dashboard</h1>
        <p style="color:{TEXT_COLOR}; font-size:1.05rem; margin:0;">
            Explore trends in player selection, college pipelines, and draft strategies from recent years.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Sidebar
st.sidebar.markdown("**Select Draft Year(s)**")
year_list = list(range(2025, 2009, -1))
selected_years = []
for year in year_list:
    if st.sidebar.checkbox(str(year), value=(year == 2020)):
        selected_years.append(year)

if not selected_years:
    st.sidebar.error("Please select at least one year.")
    st.stop()

df_filtered = df[df["season"].isin(selected_years)]

# Summary
st.markdown("### Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Players Drafted", len(df_filtered))
col2.metric("Colleges", df_filtered["college"].nunique())
col3.metric("Conferences", df_filtered["conference"].nunique())

# Position Breakdown
st.markdown("---")
st.subheader("Position Breakdown")

left_col, right_col = st.columns([1, 1])

with left_col:
    pos_counts = df_filtered.groupby("position").size().reset_index(name="count").sort_values("count", ascending=False)
    fig_pos = px.bar(pos_counts, x="position", y="count", title="Number of Players Drafted by Position",
                     color_discrete_sequence=[ACCENT_COLOR])
    fig_pos.update_layout(font_color=TEXT_COLOR, plot_bgcolor=BACKGROUND_COLOR, paper_bgcolor=BACKGROUND_COLOR)
    st.plotly_chart(fig_pos, use_container_width=True)

with right_col:
    pos_round = df_filtered[df_filtered["round"] != 0].groupby(["round", "position"]).size().reset_index(name="count")

    round1_sort = pos_round[pos_round["round"] == 1].sort_values("count", ascending=False)
    ordered_positions = round1_sort["position"].tolist()
    other_positions = [pos for pos in df_filtered["position"].unique() if pos not in ordered_positions]
    final_order = ordered_positions + other_positions

    fig_heat = px.imshow(
        pos_round.pivot(index="position", columns="round", values="count").reindex(final_order),
        text_auto=True,
        color_continuous_scale=HEATMAP_COLORS,
        aspect="auto",
        title="Players Drafted by Position and Round"
    )
    fig_heat.update_layout(font_color=TEXT_COLOR, plot_bgcolor=BACKGROUND_COLOR, paper_bgcolor=BACKGROUND_COLOR)
    st.plotly_chart(fig_heat, use_container_width=True)

# Colleges and Conferences
st.subheader("Top Sources of Draftees")
toggle_option = st.radio("View by:", ["College", "Conference"], horizontal=True)

if toggle_option == "College":
    top_colleges = df_filtered["college"].value_counts().reset_index()
    top_colleges.columns = ["college", "count"]
    fig = px.bar(top_colleges.head(15), x="count", y="college", orientation="h",
                 title="Top Colleges by Number of Drafted Players",
                 color_discrete_sequence=[PRIMARY_COLOR])
    fig.update_layout(font_color=TEXT_COLOR, plot_bgcolor=BACKGROUND_COLOR, paper_bgcolor=BACKGROUND_COLOR)
    st.plotly_chart(fig, use_container_width=True)
else:
    top_confs = df_filtered["conference"].value_counts().reset_index()
    top_confs.columns = ["conference", "count"]
    top_confs = top_confs[top_confs["conference"] != "Other"]

    df_filtered["conference"] = df_filtered["conference"].astype(str)
    df_filtered["college"] = df_filtered["college"].astype(str)

    hover_df = (
        df_filtered.groupby(["conference", "college"])
        .size()
        .reset_index(name="count")
    )

    hover_text_df = (
        hover_df.groupby("conference")
        .apply(lambda x: "<br>".join(f"{row['college']} ({row['count']})" for _, row in x.iterrows()))
        .reset_index(name="colleges")
    )

    top_confs = top_confs.merge(hover_text_df, on="conference", how="left")

    fig = px.bar(top_confs.head(15), x="count", y="conference", orientation="h",
                 title="Top Conferences by Number of Draftees",
                 color_discrete_sequence=[ACCENT_COLOR],
                 hover_data={"colleges": True, "count": True, "conference": False})
    fig.update_traces(hovertemplate="<b>%{y}</b><br>count=%{x}<br>%{customdata[0]}")
    fig.update_layout(font_color=TEXT_COLOR, plot_bgcolor=BACKGROUND_COLOR, paper_bgcolor=BACKGROUND_COLOR)
    st.plotly_chart(fig, use_container_width=True)