
import streamlit as st
import pandas as pd
import numpy as np
import time

# Load dataset from GitHub
@st.cache_data
def load_player_stats():
    url = "https://raw.githubusercontent.com/antonysamios-source/Monte5/main/player_surface_stats_master.csv"
    return pd.read_csv(url)

df = load_player_stats()

st.set_page_config(page_title="Tennis Match Simulator", layout="wide")

# Layout
col1, col2, col3 = st.columns([2, 2, 2])

with col1:
    st.markdown("### Player A")
    player_a = st.selectbox("Select Player A", sorted(df["player"].unique()))
    sets_a = st.number_input("Sets Won", 0, 5, 0, key="sets_a")
    games_a = st.number_input("Games in Current Set", 0, 7, 0, key="games_a")
    points_a = st.selectbox("Points", ["0", "15", "30", "40", "Ad"], key="points_a")

with col2:
    st.markdown("### Player B")
    player_b = st.selectbox("Select Player B", sorted(df["player"].unique()))
    sets_b = st.number_input("Sets Won", 0, 5, 0, key="sets_b")
    games_b = st.number_input("Games in Current Set", 0, 7, 0, key="games_b")
    points_b = st.selectbox("Points", ["0", "15", "30", "40", "Ad"], key="points_b")

with col3:
    st.markdown("### Match Settings")
    surface = st.selectbox("Surface", df["surface"].unique())
    best_of = st.selectbox("Match Format", [3, 5])
    server = st.radio("Who is serving?", [player_a, player_b])
    bankroll = st.number_input("Your Bankroll (£)", min_value=1.0, value=1000.0)
    st.markdown("---")
    st.markdown("### Odds & Toggles")
    odds_a = st.number_input(f"Odds for {player_a}", value=2.0)
    odds_b = st.number_input(f"Odds for {player_b}", value=2.0)
    pressure_toggle = st.checkbox("Adjust for Pressure Points", value=True)
    kelly_mode = st.selectbox("Kelly Mode", ["Full Kelly", "Half Kelly"])
    commission = st.slider("Commission (%)", 0.0, 10.0, 2.0)

# Convert point string to numerical value
def point_to_num(p):
    return {"0": 0, "15": 1, "30": 2, "40": 3, "Ad": 4}.get(p, 0)

# Probability estimation
def get_prob(player, surface):
    row = df[(df["player"] == player) & (df["surface"] == surface)]
    if not row.empty:
        sv = row.iloc[0]["svpt_won"]
        rv = row.iloc[0]["rvpt_won"]
        pp = row.iloc[0]["pressure_rating"] if pressure_toggle else 1.0
        return sv / 100, rv / 100, pp
    return 0.6, 0.4, 1.0  # fallback values

sv_a, rv_a, pp_a = get_prob(player_a, surface)
sv_b, rv_b, pp_b = get_prob(player_b, surface)

# Decide who is serving
pA_serving = server == player_a
pA_serve_win = sv_a if pA_serving else rv_a
pB_serve_win = sv_b if not pA_serving else rv_b

# Run simulation
simulate = st.button("Run Simulation")

if simulate:
    sim_placeholder = st.empty()
    progress_bar = st.progress(0)
    total_sims = 100_000
    wins_a = 0

    for i in range(total_sims):
        win_prob = pA_serve_win * pp_a
        if np.random.rand() < win_prob:
            wins_a += 1
        if i % 1000 == 0:
            progress_bar.progress(i / total_sims)

    progress_bar.progress(1.0)
    sim_placeholder.success("Simulation Complete!")

    prob_a = wins_a / total_sims
    prob_b = 1 - prob_a

    st.markdown(f"### Simulation Results:")
    st.markdown(f"- Win probability for **{player_a}**: `{prob_a:.3f}`")
    st.markdown(f"- Win probability for **{player_b}**: `{prob_b:.3f}`")

    # Kelly Formula
    def kelly(prob, odds):
        edge = (prob * odds - 1) / (odds - 1) if odds > 1 else 0
        return max(edge, 0)

    kelly_a = kelly(prob_a, odds_a)
    kelly_b = kelly(prob_b, odds_b)

    if kelly_mode == "Half Kelly":
        kelly_a /= 2
        kelly_b /= 2

    stake_a = bankroll * kelly_a
    stake_b = bankroll * kelly_b

    net_a = stake_a * (odds_a - 1) * (1 - commission / 100)
    net_b = stake_b * (odds_b - 1) * (1 - commission / 100)

    st.markdown(f"### Suggested Bets:")
    st.markdown(f"- Bet **£{stake_a:.2f}** on **{player_a}** → Net Return: **£{net_a:.2f}**")
    st.markdown(f"- Bet **£{stake_b:.2f}** on **{player_b}** → Net Return: **£{net_b:.2f}**")
