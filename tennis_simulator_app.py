import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from math import log, floor

# Load player surface stats directly from GitHub
@st.cache_data
def load_stats():
    url = "https://raw.githubusercontent.com/antonysamios-source/Monte5/main/player_surface_stats_master.csv"
    df = pd.read_csv(url)
    return df

stats_df = load_stats()

# App Layout
st.set_page_config(layout="wide")
st.title("🎾 Tennis Monte Carlo Simulator + Betting Tracker")

col1, col2, col3 = st.columns([2, 2, 3])

with col1:
    st.subheader("Player A")
    player_a = st.selectbox("Select Player A", sorted(stats_df['player'].unique()), key="player_a")
    sets_a = st.number_input("Sets Won", min_value=0, max_value=5, value=0, key="sets_a")
    games_a = st.number_input("Games in Current Set", min_value=0, max_value=7, value=0, key="games_a")
    points_a = st.number_input("Points", min_value=0, max_value=4, value=0, key="points_a")

with col2:
    st.subheader("Player B")
    player_b = st.selectbox("Select Player B", sorted(stats_df['player'].unique()), key="player_b")
    sets_b = st.number_input("Sets Won", min_value=0, max_value=5, value=0, key="sets_b")
    games_b = st.number_input("Games in Current Set", min_value=0, max_value=7, value=0, key="games_b")
    points_b = st.number_input("Points", min_value=0, max_value=4, value=0, key="points_b")

with col3:
    st.subheader("Match Settings & Odds")
    surface = st.selectbox("Surface", ["Hard", "Clay", "Grass"], key="surface")
    format_sets = st.radio("Match Format (Best of)", [3, 5], key="format")
    server = st.radio("Who is Serving?", [player_a, player_b], key="server")
    bankroll = st.number_input("Your Bankroll (\u00a3)", min_value=10.0, value=1000.0, step=10.0)
    odds_a = st.number_input(f"Betfair Odds {player_a}", value=2.0, step=0.01, key="odds_a")
    odds_b = st.number_input(f"Betfair Odds {player_b}", value=2.0, step=0.01, key="odds_b")
    kelly_fraction = st.slider("Kelly Multiplier", 0.0, 1.0, 0.5, 0.1, key="kelly")
    commission = st.slider("Betfair Commission (%)", 0.0, 10.0, 5.0, 0.5, key="commission")
    toggle_pressure = st.checkbox("Use Pressure Point Logic", value=True)

# Score logic
score_str = ["0", "15", "30", "40", "Ad"]
def get_point_str(pa, pb):
    if pa >= 4 or pb >= 4:
        if abs(pa - pb) >= 2:
            return f"Game {'A' if pa > pb else 'B'}"
        elif pa == pb:
            return "40-40"
        elif pa > pb:
            return "Ad A"
        else:
            return "Ad B"
    else:
        return f"{score_str[pa]} - {score_str[pb]}"

point_score = get_point_str(points_a, points_b)
st.markdown(f"### Scoreboard \n**{player_a}** {sets_a}-{sets_b} **{player_b}**\n\nGames: {games_a}-{games_b} | Points: {point_score}")

# Get stats per surface
def get_player_stats(player):
    row = stats_df[(stats_df['player'] == player) & (stats_df['surface'] == surface)]
    if row.empty:
        return 0.60, 0.35  # Defaults
    return float(row['serve_win'].values[0]), float(row['return_win'].values[0])

sa_serve, sa_return = get_player_stats(player_a)
sb_serve, sb_return = get_player_stats(player_b)

# Pressure multiplier logic
def pressure_adjustment(pa, pb):
    if not toggle_pressure:
        return 1.0
    if (pa, pb) in [(30, 40), (40, 30), (40, 40)] or pa >= 4 or pb >= 4:
        return 1.10  # 10% boost under pressure
    return 1.0

# Monte Carlo simulation
@st.cache_data(show_spinner=False)
def simulate_win_probs(server, simulations=100000):
    win_a, win_b = 0, 0
    for _ in range(simulations):
        pa, pb = points_a, points_b
        while True:
            if server == player_a:
                win_prob = sa_serve * pressure_adjustment(pa, pb)
            else:
                win_prob = (1 - sb_return) * pressure_adjustment(pa, pb)
            if np.random.rand() < win_prob:
                pa += 1
            else:
                pb += 1
            if pa >= 4 and pa - pb >= 2:
                win_a += 1
                break
            elif pb >= 4 and pb - pa >= 2:
                win_b += 1
                break
    return win_a / simulations, win_b / simulations

if st.button("Run Simulation"):
    prob_a, prob_b = simulate_win_probs(server)
    st.success(f"Simulated Probability {player_a}: {prob_a*100:.2f}% | {player_b}: {prob_b*100:.2f}%")

    imp_a = 1 / odds_a
    imp_b = 1 / odds_b
    ev_a = prob_a - imp_a
    ev_b = prob_b - imp_b

    stake_a = max(2.0, floor((bankroll * kelly_fraction * ev_a) / (1 - odds_a))) if ev_a > 0 else 0
    stake_b = max(2.0, floor((bankroll * kelly_fraction * ev_b) / (1 - odds_b))) if ev_b > 0 else 0

    st.info(f"Expected Value A: {ev_a:.4f}, Stake: \u00a3{stake_a:.2f}")
    st.info(f"Expected Value B: {ev_b:.4f}, Stake: \u00a3{stake_b:.2f}")

    st.metric("Recommended Bet", f"{'Back ' + player_a if stake_a > 0 else 'Back ' + player_b if stake_b > 0 else 'No Bet'}")

# Requirements.txt info (separately requested)
requirements = """
pandas
numpy
streamlit
matplotlib
seaborn
"""
with open("/mnt/data/requirements.txt", "w") as f:
    f.write(requirements)

st.sidebar.download_button("Download requirements.txt", "/mnt/data/requirements.txt")

