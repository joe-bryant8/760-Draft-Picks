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
df["college_conference"] = df["college"].map(college_to_conf).fillna("Non-Power Conference")

# Group similar positions
position_map = {
    "OT": "OL", "OG": "OL", "C": "OL",
    "P": "ST", "K": "ST",
    "DT": "DL"
}
df["position_grouped"] = df["position"].replace(position_map)

# Page config
st.set_page_config(page_title="NFL Draft Landing Page", layout="wide")
st.markdown("## NFL Draft Overview", unsafe_allow_html=True)
st.markdown("Explore trends in player positions, draft rounds, colleges, and more.", unsafe_allow_html=True)

# Sidebar - Year filter (required selection, multiple allowed)
year_list = sorted([y for y in df["season"].dropna().unique() if y != 2025], reverse=True)
selected_years = st.sidebar.multiselect("Select Draft Year(s)", options=year_list, default=[year_list[0]])
if not selected_years:
    st.sidebar.error("Please select at least one year.")
    st.stop()

df_filtered = df[df["season"].isin(selected_years)]

BACKGROUND_COLOR = "#111827"
TEXT_COLOR = "#E5E7EB"
PRIMARY_COLOR = "#4F46E5"
ACCENT_COLOR = "#10B981"
HEATMAP_COLORS = px.colors.sequential.Tealgrn[::-1]

# --- Summary Metrics ---
st.markdown("### Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Players Drafted", len(df_filtered))
col2.metric("Colleges", df_filtered["college"].nunique())
col3.metric("Conferences", df_filtered["college_conference"].nunique())

# --- Position Breakdown and Round Distribution Side by Side ---
st.markdown("---")
st.subheader("Position Breakdown")

left_col, right_col = st.columns([1, 1])

with left_col:
    pos_counts = df_filtered.groupby("position_grouped").size().reset_index(name="count").sort_values("count", ascending=False)
    fig_pos = px.bar(pos_counts, x="position_grouped", y="count", title="Number of Players Drafted by Position",
                     color_discrete_sequence=[PRIMARY_COLOR])
    fig_pos.update_layout(font_color=TEXT_COLOR, plot_bgcolor=BACKGROUND_COLOR, paper_bgcolor=BACKGROUND_COLOR)
    st.plotly_chart(fig_pos, use_container_width=True)

with right_col:
    pos_round = df_filtered[df_filtered["round"] != 0].groupby(["round", "position_grouped"]).size().reset_index(name="count")

    round1_sort = pos_round[pos_round["round"] == 1].sort_values("count", ascending=False)
    ordered_positions = round1_sort["position_grouped"].tolist()
    other_positions = [pos for pos in df_filtered["position_grouped"].unique() if pos not in ordered_positions]
    final_order = ordered_positions + other_positions

    fig_heat = px.density_heatmap(pos_round, x="round", y="position_grouped", z="count", histfunc="sum",
                                  category_orders={"position_grouped": final_order, "round": [1, 2, 3, 4, 5, 6, 7]},
                                  color_continuous_scale=HEATMAP_COLORS,
                                  title="Players Drafted by Position and Round")
    fig_heat.update_layout(font_color=TEXT_COLOR, plot_bgcolor=BACKGROUND_COLOR, paper_bgcolor=BACKGROUND_COLOR,
                           xaxis=dict(dtick=1), dragmode=False)
    st.plotly_chart(fig_heat, use_container_width=True)

# --- Colleges and Conferences Toggle ---
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
    top_confs = df_filtered["college_conference"].value_counts().reset_index()
    top_confs.columns = ["college_conference", "count"]
    top_confs = top_confs[top_confs["college_conference"] != "Other"]

    df_filtered["college_conference"] = df_filtered["college_conference"].astype(str)
    df_filtered["college"] = df_filtered["college"].astype(str)

    hover_df = (
        df_filtered.groupby(["college_conference", "college"])
        .size()
        .reset_index(name="count")
    )

    hover_text_df = (
        hover_df.groupby("college_conference")
        .apply(lambda x: "<br>".join(f"{row['college']} ({row['count']})" for _, row in x.iterrows()))
        .reset_index(name="colleges")
    )

    top_confs = top_confs.merge(hover_text_df, on="college_conference", how="left")

    fig = px.bar(top_confs.head(15), x="count", y="college_conference", orientation="h",
                 title="Top Conferences by Number of Draftees",
                 color_discrete_sequence=[ACCENT_COLOR],
                 hover_data={"colleges": True, "count": True, "college_conference": False})
    fig.update_traces(hovertemplate="<b>%{y}</b><br>count=%{x}<br>%{customdata[0]}")
    fig.update_layout(font_color=TEXT_COLOR, plot_bgcolor=BACKGROUND_COLOR, paper_bgcolor=BACKGROUND_COLOR)
    st.plotly_chart(fig, use_container_width=True)
