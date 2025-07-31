import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from PIL import Image

# -Page Config
st.set_page_config(page_title="Team Draft Efficiency", layout="wide")

# Load data
df = pd.read_csv("draft_picks.csv")
df = df[(df["round"] > 0) & (df["round"] <= 6)]

# Sidebar
st.sidebar.header("Filters")
years = list(range(2024, 2010 - 1, -1))

selected_year = st.sidebar.selectbox("Year", years, index=years.index(2019))

df = df[df["season"] == selected_year]

# Map logos
logo_dir = "logos/teams"
team_logos = {f.split(".")[0]: os.path.join(logo_dir, f) for f in os.listdir(logo_dir) if f.endswith(".png")}

# Cache images to try to increase loading times
@st.cache_resource
def load_logo_images(team_logos):
    return {team: Image.open(path) for team, path in team_logos.items() if os.path.exists(path)}

logo_images = load_logo_images(team_logos)
df = df[df["team"].isin(logo_images.keys())]

# Compute averages
team_stats = df.groupby("team").agg(avg_round=("round", "mean"), avg_wav=("w_av", "mean")).reset_index()
team_stats = team_stats[team_stats["team"].isin(logo_images.keys())]
team_stats["logo_img"] = team_stats["team"].map(logo_images)

# Create quadrants and limit to 6 rounds
x_range = [1, 6]
y_range = [0, team_stats["avg_wav"].max() * 1.1]
x_mid = sum(x_range) / 2
y_mid = sum(y_range) / 2

# Scatter plot
fig = px.scatter(
    team_stats,
    x="avg_round",
    y="avg_wav",
    title=f"NFL Draft Efficiency by Team ({selected_year})",
    labels={"avg_round": "Average Draft Round", "avg_wav": "Average Weighted AV"},
    template="plotly_dark",
    opacity=0
)

# Add logos
for _, row in team_stats.iterrows():
    picks = df[df["team"] == row["team"]]
    hover_text = "<br>".join([
        f"{r['pfr_player_name']}: Pick {int(r['pick']) if pd.notnull(r['pick']) else 'N/A'}, "
        f"Round {int(r['round']) if pd.notnull(r['round']) else 'N/A'}, "
        f"W_AV {int(r['w_av']) if pd.notnull(r['w_av']) else 'N/A'}"
        for _, r in picks.iterrows()
    ])
    
    fig.add_trace(
        go.Scatter(
            x=[row["avg_round"]],
            y=[row["avg_wav"]],
            mode="markers",
            marker=dict(opacity=0),
            hovertext=hover_text,
            hoverinfo="text",
            showlegend=False
        )
    )

    fig.add_layout_image(
        dict(
            source=row["logo_img"],
            x=row["avg_round"],
            y=row["avg_wav"],
            xref="x",
            yref="y",
            sizex=0.35,
            sizey=(y_range[1] - y_range[0]) * 0.05,
            xanchor="center",
            yanchor="middle",
            sizing="contain",
            layer="above",
            name=row["team"]
        )
    )

# Quadrants lines
fig.add_shape(type="line", x0=x_mid, x1=x_mid, y0=y_range[0], y1=y_range[1],
              line=dict(color="white", dash="dash"))
fig.add_shape(type="line", x0=x_range[0], x1=x_range[1], y0=y_mid, y1=y_mid,
              line=dict(color="white", dash="dash"))

# Quadrant labels
fig.add_annotation(text="High Pick, High Return", x=x_mid - 1.5, y=y_mid + 1.5, showarrow=False, font=dict(color="white"))
fig.add_annotation(text="High Pick, Low Return", x=x_mid - 1.5, y=y_mid - 1.5, showarrow=False, font=dict(color="white"))
fig.add_annotation(text="Late Pick, High Return", x=x_mid + 1.5, y=y_mid + 1.5, showarrow=False, font=dict(color="white"))
fig.add_annotation(text="Low Pick, Low Return", x=x_mid + 1.5, y=y_mid - 1.5, showarrow=False, font=dict(color="white"))

# Graph styling
fig.update_layout(
    xaxis_title="Average Draft Round",
    yaxis_title="Average Weighted AV",
    plot_bgcolor="#111827",
    paper_bgcolor="#111827",
    font_color="#E5E7EB",
    height=700,
    margin=dict(l=40, r=40, t=60, b=40),
    showlegend=False
)

# Final output
st.markdown("## Team Draft Efficiency")
st.markdown("Each team’s draft efficiency is shown by average round vs. weighted career value (W_AV).")
st.plotly_chart(fig, use_container_width=True)
