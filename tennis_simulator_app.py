import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
import time

# Load data directly from GitHub
@st.cache_data
def load_player_stats():
    url = "https://raw.githubusercontent.com/antonysamios-source/Monte5/main/player_surface_stats_2022_2024.csv"
    response = requests.get(url)
    return pd.read_csv(io.StringIO(response.text))

stats_df = load_player_stats()

# ---------------- UI ----------------

st.title("🎾 Tennis Monte Carlo Match Simulator")

col1, col2 = st.columns(2)

with col1:
    player_a = st.selectbox("Select Player A", options=sorted(stats_df["player"].unique()), key="player_a")
    sets_a = st.number_input("Sets Won", min_value=0, max_value=5, value=0, key="sets_a")
    games_a = st.number_input("Games in Current Set", min_value=0, max_value=7, value=0, key="games_a")
    points_a = st.number_input("Points", min_value=0, max_value=4, value=0, key="points_a")

with col2:
    player_b = st.selectbox("Select Player B", options=sorted(stats_df["player"].unique()), key="player_b")
    sets_b = st.number_input("Sets Won ", min_value=0, max_value=5, value=0, key="sets_b")
    games_b = st.number_input("Games in Current Set ", min_value=0, max_value=7, value=0, key="games_b")
    points_b = st.number_input("Points ", min_value=0, max_value=4, value=0, key="points_b")

st.markdown("---")

col3, col4 = st.columns(2)
with col3:
    surface = st.selectbox("Surface", options=["Hard", "Clay", "Grass"], key="surface")
    match_format = st.selectbox("Match Format", options=[3, 5], key="match_format")

with col4:
    server = st.radio("Who is serving?", options=[player_a, player_b], key="server")
    bankroll = st.number_input("Your Bankroll (£)", min_value=1.0, value=1000.0, step=1.0, key="bankroll")

st.markdown("### Odds & Toggles")

col5, col6, col7 = st.columns(3)
with col5:
    odds_a = st.number_input(f"Odds for {player_a}", min_value=1.01, value=2.0, key="odds_a")
with col6:
    odds_b = st.number_input(f"Odds for {player_b}", min_value=1.01, value=2.0, key="odds_b")
with col7:
    commission = st.slider("Commission (%)", 0.0, 10.0, value=2.0, key="commission")

st.markdown("### Simulation Settings")

col8, col9 = st.columns(2)
with col8:
    use_half_kelly = st.checkbox("Use Half-Kelly", value=True, key="half_kelly")
with col9:
    pressure_toggle = st.checkbox("Apply Pressure Point Weighting", value=True, key="pressure_toggle")

st.markdown("---")

# ---------------- Simulation Logic ----------------

def get_surface_stats(player, surface):
    row = stats_df[(stats_df["player"] == player) & (stats_df["surface"] == surface)]
    if row.empty:
        return 0.60, 0.35  # default if missing
    return float(row["serve_win_pct"]), float(row["return_win_pct"])

def simulate_match(pA_sv, pB_sv, server, sets_a, sets_b, games_a, games_b, points_a, points_b, match_format, pressure=False, n=100000):
    pA_wins = 0
    for _ in range(n):
        sets = [sets_a, sets_b]
        games = [games_a, games_b]
        points = [points_a, points_b]
        serving = 0 if server == player_a else 1

        while sets[0] < (match_format // 2 + 1) and sets[1] < (match_format // 2 + 1):
            point_winner = np.random.rand() < (pA_sv if serving == 0 else 1 - pB_sv)
            
            if pressure:
                if games[serving] >= 5 and games[1 - serving] >= 5:
                    point_winner = point_winner * 0.97 + (1 - point_winner) * 0.03  # simulate nerves
            
            points[0 if point_winner else 1] += 1

            if points[0] >= 4 and points[0] - points[1] >= 2:
                games[0] += 1
                points = [0, 0]
                serving = 1 - serving
            elif points[1] >= 4 and points[1] - points[0] >= 2:
                games[1] += 1
                points = [0, 0]
                serving = 1 - serving

            if games[0] >= 6 and games[0] - games[1] >= 2:
                sets[0] += 1
                games = [0, 0]
            elif games[1] >= 6 and games[1] - games[0] >= 2:
                sets[1] += 1
                games = [0, 0]

        if sets[0] > sets[1]:
            pA_wins += 1

    return pA_wins / n

# ---------------- Run Simulation ----------------

with st.spinner("Running Monte Carlo simulation..."):
    pA_sv, pA_rv = get_surface_stats(player_a, surface)
    pB_sv, pB_rv = get_surface_stats(player_b, surface)

    prob_a = simulate_match(
        pA_sv=pA_sv,
        pB_sv=pB_sv,
        server=server,
        sets_a=sets_a,
        sets_b=sets_b,
        games_a=games_a,
        games_b=games_b,
        points_a=points_a,
        points_b=points_b,
        match_format=match_format,
        pressure=pressure_toggle,
        n=100000
    )

st.success("✅ Simulation Complete")

# ---------------- Output ----------------

col_final1, col_final2 = st.columns(2)
with col_final1:
    st.metric(f"Probability of {player_a} Winning", f"{prob_a:.2%}")
with col_final2:
    st.metric(f"Probability of {player_b} Winning", f"{(1 - prob_a):.2%}")

# Kelly Formula
def kelly_stake(prob, odds):
    if odds <= 1:
        return 0.0
    kelly = (prob * (odds - 1) - (1 - prob)) / (odds - 1)
    return max(kelly, 0)

kelly = kelly_stake(prob_a, odds_a)
if use_half_kelly:
    kelly /= 2

stake = kelly * bankroll
stake_after_commission = stake * (1 - commission / 100)

st.markdown("### Suggested Bet")
st.info(f"Bet £{stake_after_commission:.2f} on {player_a} using {'Half-Kelly' if use_half_kelly else 'Full Kelly'}")

