import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64
import os

# Paths
LOGO_DIR = "logos/teams"

# Team name and color mapping
TEAM_NAMES = {
    "ARI": "Arizona Cardinals", "ATL": "Atlanta Falcons", "BAL": "Baltimore Ravens", "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers", "CHI": "Chicago Bears", "CIN": "Cincinnati Bengals", "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys", "DEN": "Denver Broncos", "DET": "Detroit Lions", "GNB": "Green Bay Packers",
    "HOU": "Houston Texans", "IND": "Indianapolis Colts", "JAX": "Jacksonville Jaguars", "KAN": "Kansas City Chiefs",
    "LAC": "Los Angeles Chargers", "LAR": "Los Angeles Rams", "MIA": "Miami Dolphins", "MIN": "Minnesota Vikings",
    "NWE": "New England Patriots", "NOR": "New Orleans Saints", "NYG": "New York Giants", "NYJ": "New York Jets",
    "OAK": "Oakland Raiders", "LVR": "Las Vegas Raiders", "PHI": "Philadelphia Eagles", "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks", "SFO": "San Francisco 49ers", "TAM": "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans", "WAS": "Washington Commanders"
}

TEAM_COLORS = {
    "ARI": "#97233F", "ATL": "#A71930", "BAL": "#241773", "BUF": "#00338D", "CAR": "#0085CA",
    "CHI": "#C83803", "CIN": "#FB4F14", "CLE": "#FF3C00", "DAL": "#003594", "DEN": "#FB4F14",
    "DET": "#0076B6", "GNB": "#203731", "HOU": "#03202F", "IND": "#002C5F", "JAX": "#006778",
    "KAN": "#E31837", "LAC": "#0080C6", "LAR": "#003594", "MIA": "#008E97", "MIN": "#4F2683",
    "NWE": "#002244", "NOR": "#D3BC8D", "NYG": "#0B2265", "NYJ": "#125740", "OAK": "#A5ACAF", "LVR": "#000000",
    "PHI": "#004C54", "PIT": "#FFB612", "SEA": "#69BE28", "SFO": "#AA0000", "TAM": "#D50A0A",
    "TEN": "#4B92DB", "WAS": "#5A1414"
}

# Load data
df = pd.read_csv("draft_picks.csv")
df = df[df["round"] > 0]

# Compute impact score and context score
df["impact_score"] = df["w_av"] + (5 * df["allpro"] + 2 * df["probowls"])
df["w_av_context"] = df["w_av"] * (1 + (df["round"] / 10))
df["recognition"] = df["allpro"] + df["probowls"] > 0

# Statistics Summary
def generate_stat_summary(row):
    pos = row["position"]
    parts = []

    def safe_val(val):
        return 0 if pd.isna(val) else int(val)

    if pos == "QB":
        parts = [f"Pass Yards: {safe_val(row['pass_yards'])}", f"Pass TDs: {safe_val(row['pass_tds'])}",
                 f"Rush Yards: {safe_val(row['rush_yards'])}", f"Rush TDs: {safe_val(row['rush_tds'])}"]
    elif pos in ["RB", "FB"]:
        parts = [f"Rush Yards: {safe_val(row['rush_yards'])}", f"Rush TDs: {safe_val(row['rush_tds'])}",
                 f"Rec Yards: {safe_val(row['rec_yards'])}", f"Rec TDs: {safe_val(row['rec_tds'])}"]
    elif pos in ["WR", "TE"]:
        parts = [f"Rec Yards: {safe_val(row['rec_yards'])}", f"Rec TDs: {safe_val(row['rec_tds'])}"]
    elif pos in ["DL", "DE", "DT", "EDGE"]:
        parts = [f"Sacks: {safe_val(row['def_sacks'])}", f"Solo Tackles: {safe_val(row['def_solo_tackles'])}"]
    elif pos == "LB":
        parts = [f"Solo Tackles: {safe_val(row['def_solo_tackles'])}", f"Sacks: {safe_val(row['def_sacks'])}", f"INT: {safe_val(row['def_ints'])}"]
    elif pos in ["CB", "S", "DB"]:
        parts = [f"INT: {safe_val(row['def_ints'])}", f"Solo Tackles: {safe_val(row['def_solo_tackles'])}"]

    return " | ".join(parts)

# Page config
st.set_page_config(page_title="Team Overview", layout="wide")
st.markdown("<style>section[data-testid='stSidebar'] div.stButton > button { width: 100%; }</style>", unsafe_allow_html=True)

# Sidebar
abbrev_to_full = {k: v for k, v in TEAM_NAMES.items() if k in df["team"].unique()}
full_to_abbrev = {v: k for k, v in abbrev_to_full.items()}
selected_team_name = st.sidebar.selectbox("Select a Team", sorted(full_to_abbrev.keys()))
selected_team = full_to_abbrev[selected_team_name]

st.sidebar.markdown("**Select Draft Year(s)**")
year_list = list(range(2024, 2010 - 1, -1))
selected_years = []
for year in year_list:
    if st.sidebar.checkbox(str(year), value=(year == 2020)):
        selected_years.append(year)

if not selected_years:
    st.sidebar.error("Please select at least one year.")
    st.stop()

# Filter data
df_filtered = df[df["season"].isin(selected_years)]
team_color = TEAM_COLORS.get(selected_team, "#888")
team_logo_path = os.path.join("logos/teams", f"{selected_team}.png")

# Filter team data
df_team = df_filtered[df_filtered["team"] == selected_team].copy()
df_team["total_yards"] = df_team[["rush_yards", "rec_yards", "pass_yards"]].fillna(0).sum(axis=1)
df_team["defense_impact"] = df_team[["def_solo_tackles", "def_sacks", "def_ints"]].fillna(0).sum(axis=1)
df_team["impact"] = df_team["impact_score"]
df_team["stat_summary"] = df_team.apply(generate_stat_summary, axis=1)

# Draft Grade Calculation
total_impact = df_team["impact_score"].sum()
num_players = len(df_team)
avg_round = df_team["round"].mean()

if num_players > 0:
    years_since_draft = max(1, 2024 - df_team["season"].min())
    recency_scale = min(2.0, 4 / years_since_draft)  # Boost for recent years, capped
    adjusted_impact_score = df_team["impact_score"] * recency_scale
    total_impact = adjusted_impact_score.sum()

    raw_score = 100 * (total_impact / (num_players * 15))
    penalty = (avg_round - 1) / 20
    draft_score = raw_score * (1 - penalty)
    draft_score = min(draft_score, 100)
else:
    draft_score = 0

if draft_score >= 90:
    letter_grade = "A+"
elif draft_score >= 80:
    letter_grade = "A"
elif draft_score >= 65:
    letter_grade = "B"
elif draft_score >= 50:
    letter_grade = "C"
elif draft_score >= 35:
    letter_grade = "D"
else:
    letter_grade = "F"

if draft_score >= 80:
    grade_color = "#4CAF50"
elif draft_score >= 65:
    grade_color = "#66BB6A"
elif draft_score >= 50:
    grade_color = "#FFB300"
elif draft_score >= 35:
    grade_color = "#FF9800"
else:
    grade_color = "#B71C1C"

# Team Title and Metrics Row
st.markdown(f"<h1 style='margin-bottom: 0;'>Team Draft Performance: {selected_team_name}</h1>", unsafe_allow_html=True)

col0, col1, col2, col3 = st.columns([1, 1, 1, 2])
with col0:
    st.image(team_logo_path, width=80)
    st.markdown(f"""
        <div style='margin-top: 0.5em;'>
            <div style='display: inline-block; padding: 0.4em 1.2em; background-color: {grade_color}; color: white;
                        border-radius: 10px; font-size: 16px; font-weight: bold;'>
                Draft Grade: {letter_grade} ({draft_score:.0f})
            </div>
        </div>
    """, unsafe_allow_html=True)

with col1:
    st.metric("Players Drafted", len(df_team))
with col2:
    st.metric("Avg Weighted Approximate Value", round(df_team["w_av"].mean(), 1))
with col3:
    top_player = df_team.loc[df_team["impact_score"].idxmax()]
    st.metric("Top Impact Player", f"{top_player['pfr_player_name']}")

# Top Draft Impact
st.markdown("---")
chart_col, table_col = st.columns(2)

with chart_col:
    st.markdown("### Top Draft Impact")
    fig_top = px.bar(
        df_team.sort_values("impact", ascending=False).head(8),
        x="pfr_player_name", y="impact",
        color_discrete_sequence=[team_color]
    )
    fig_top.update_layout(
        xaxis_title="Player", yaxis_title="Impact Score",
        height=450
    )
    st.plotly_chart(fig_top, use_container_width=True)

with table_col:
    st.markdown("""
        <style>
        div[data-testid="stDataFrame"] td {
            font-size: 16px;
            padding: 12px 8px;
        }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("### Top Statistical Performers")
    df_team["Pro-Bowl/All-Pro"] = df_team["recognition"].apply(lambda x: "✓" if x else "✗")
    df_table = df_team.sort_values("impact", ascending=False).head(10)
    df_table = df_table[["impact", "season", "pfr_player_name", "position", "games", "Pro-Bowl/All-Pro", "stat_summary"]]
    df_table.rename(columns={"stat_summary": "Stats"}, inplace=True)
    st.dataframe(df_table, use_container_width=True, height=450)
