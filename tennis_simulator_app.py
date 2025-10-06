import streamlit as st
import pandas as pd
import numpy as np
import random
from math import log, exp

# Load player stats
@st.cache_data
def load_stats():
    url = "https://raw.githubusercontent.com/antonysamios-source/Monte5/main/player_surface_stats_master.csv"
    return pd.read_csv(url)

stats_df = load_stats()

st.set_page_config(layout="wide")
st.title("🎾 Tennis Betting Simulator (Monte Carlo + Kelly)")

# Player Selection
col1, col2 = st.columns(2)
with col1:
    player_a = st.selectbox("Select Player A", sorted(stats_df["player"].unique()), key="player_a")
with col2:
    player_b = st.selectbox("Select Player B", sorted(stats_df["player"].unique()), key="player_b")

# Surface Selection
surface = st.selectbox("Surface", ["Hard", "Clay", "Grass"])
is_wta = st.toggle("WTA Match?", False)

# Match State
st.markdown("### Match Scoreboard")
sets_a = st.number_input(f"{player_a} Sets Won", 0, 5, key="sets_a")
games_a = st.number_input(f"{player_a} Games in Current Set", 0, 7, key="games_a")
points_a = st.number_input(f"{player_a} Points", 0, 4, key="points_a")

sets_b = st.number_input(f"{player_b} Sets Won", 0, 5, key="sets_b")
games_b = st.number_input(f"{player_b} Games in Current Set", 0, 7, key="games_b")
points_b = st.number_input(f"{player_b} Points", 0, 4, key="points_b")

# Odds Inputs
odds_a = st.number_input(f"Betfair Odds {player_a}", value=2.0, step=0.01)
odds_b = st.number_input(f"Betfair Odds {player_b}", value=2.0, step=0.01)

# Bankroll and Settings
bankroll = st.number_input("Your Bankroll (£)", value=1000.00)
use_half_kelly = st.toggle("Use Half Kelly?")
toggle_pressure = st.toggle("Apply Pressure Point Adjustments?")
commission_rate = st.slider("Betfair Commission (%)", 0.0, 10.0, value=5.0) / 100

# Function to get serve and return win % adjusted
def get_stats(player):
    row = stats_df[(stats_df["player"] == player) & (stats_df["surface"] == surface)]
    if row.empty:
        return 0.6, 0.4
    serve_win = row["serve_win_pct"].values[0]
    return_win = row["return_win_pct"].values[0]
    pressure_adj = row["pressure_performance"].values[0] if toggle_pressure else 1.0
    return serve_win * pressure_adj, return_win * pressure_adj

# Monte Carlo Simulation
def simulate_match(p1, p2, server_first, n_sim=100000):
    p1_serve, p1_return = get_stats(p1)
    p2_serve, p2_return = get_stats(p2)
    p1_wins = 0

    for _ in range(n_sim):
        p1_score = 0
        p2_score = 0
        server = server_first

        for _ in range(50):  # Simulate up to 50 games
            if server == p1:
                win_prob = p1_serve
            else:
                win_prob = 1 - p2_return

            if random.random() < win_prob:
                if server == p1:
                    p1_score += 1
                else:
                    p2_score += 1
            else:
                if server == p1:
                    p2_score += 1
                else:
                    p1_score += 1

            server = p2 if server == p1 else p1

        if p1_score > p2_score:
            p1_wins += 1

    return p1_wins / n_sim

# Determine current server
server = st.selectbox("Who is serving?", [player_a, player_b])

# Run Simulation
if st.button("Run Monte Carlo Simulation"):
    win_prob = simulate_match(player_a, player_b, server)
    implied_prob = 1 / odds_a
    expected_value = (win_prob * (odds_a - 1) - (1 - win_prob)) * (1 - commission_rate)

    kelly_fraction = ((odds_a - 1) * win_prob - (1 - win_prob)) / (odds_a - 1)
    if use_half_kelly:
        kelly_fraction /= 2

    kelly_fraction = max(kelly_fraction, 0)
    stake = max(2, round(bankroll * kelly_fraction, 2)) if kelly_fraction > 0 else 0

    st.markdown(f"### Results for {player_a}")
    st.metric("Win Probability", f"{win_prob:.2%}")
    st.metric("Implied Market Probability", f"{implied_prob:.2%}")
    st.metric("Expected Value", f"£{expected_value * bankroll:.2f}")
    st.metric("Kelly Fraction", f"{kelly_fraction:.2%}")
    st.metric("Recommended Stake", f"£{stake:.2f}")
