# tennis_simulator_app.py
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- Settings ---
st.set_page_config(layout="wide")
st.title("Live Tennis Trading Simulator 🎾")

# --- Load Stats File from GitHub or Upload ---
st.sidebar.header("📄 Load Player Data")

csv_file = st.sidebar.file_uploader("Upload Player Stats CSV", type="csv")
if csv_file:
    stats_df = pd.read_csv(csv_file)
else:
    stats_df = pd.read_csv("https://raw.githubusercontent.com/antonysamios-source/Monte5/main/player_surface_stats_master.csv")

# --- Helper Function to Get Stats ---
def get_player_stats(name, surface, tour):
    row = stats_df[(stats_df["player"] == name) & (stats_df["surface"] == surface) & (stats_df["tour"] == tour)]
    if row.empty:
        return 0.60, 0.35  # fallback values
    return float(row["serve_win_pct"].values[0]), float(row["return_win_pct"].values[0])

# --- UI Layout ---
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("## Scoreboard")
    player_a = st.selectbox("Player A", options=sorted(stats_df["player"].unique()), key="a")
    player_b = st.selectbox("Player B", options=sorted(stats_df["player"].unique()), key="b")
    surface = st.selectbox("Surface", ["Clay", "Grass", "Hard"])
    tour = st.radio("Tour", ["ATP", "WTA"], horizontal=True)
    server = st.radio("Who is Serving?", [player_a, player_b], horizontal=True)

    # Score inputs (compact layout)
    st.markdown("### Match Score")
    sets_a = st.number_input(f"{player_a} Sets", min_value=0, max_value=5, value=0)
    sets_b = st.number_input(f"{player_b} Sets", min_value=0, max_value=5, value=0)
    games_a = st.number_input(f"{player_a} Games", min_value=0, max_value=7, value=0)
    games_b = st.number_input(f"{player_b} Games", min_value=0, max_value=7, value=0)
    points_a = st.number_input(f"{player_a} Points", min_value=0, max_value=4, value=0)
    points_b = st.number_input(f"{player_b} Points", min_value=0, max_value=4, value=0)

    # Odds and bankroll
    odds_a = st.number_input(f"Betfair Odds {player_a}", value=2.0, step=0.01, key="odds_a")
    odds_b = st.number_input(f"Betfair Odds {player_b}", value=2.0, step=0.01, key="odds_b")
    bankroll = st.number_input("Bankroll (£)", value=1000.0)
    commission = st.slider("Betfair Commission (%)", 0.0, 10.0, 5.0)
    use_pressure = st.checkbox("Use Pressure Point Logic", value=True)
    half_kelly = st.checkbox("Use Half Kelly", value=False)

with col2:
    st.markdown("## Simulation Results")

    # Get serve/return stats
    sa_serve, sa_return = get_player_stats(player_a, surface, tour)
    sb_serve, sb_return = get_player_stats(player_b, surface, tour)

    # Adjust for who is serving
    if server == player_a:
        server_win_prob = sa_serve
        return_win_prob = sb_return
    else:
        server_win_prob = sb_serve
        return_win_prob = sa_return

    # --- Pressure Point Logic ---
    is_pressure_point = ((points_a >= 3 or points_b >= 3) or (games_a == 5 and games_b == 5))
    if use_pressure and is_pressure_point:
        server_win_prob += 0.02  # small pressure bonus

    # --- Monte Carlo Simulation ---
    st.write("Running simulation...")
    simulations = 100_000
    win_count = 0

    for _ in range(simulations):
        p = server_win_prob
        if np.random.rand() < p:
            win_count += 1

    implied_prob = win_count / simulations
    implied_odds = 1 / implied_prob if implied_prob > 0 else 1000
    st.metric("Implied Odds", f"{implied_odds:.2f}")

    # --- Expected Value and Bet Suggestion ---
    market_odds = odds_a if server == player_a else odds_b
    market_prob = 1 / market_odds
    ev = implied_prob - market_prob

    if ev > 0:
        kelly_fraction = (ev / (1 - market_prob))
        if half_kelly:
            kelly_fraction *= 0.5
        stake = max(2, kelly_fraction * bankroll)  # Min Betfair stake = £2
        st.success(f"✅ Bet suggested: £{stake:.2f} on {server}")
    else:
        st.warning("❌ No value bet available — hold position or consider lay.")

    # --- Position Tracking ---
    st.markdown("### Position Overview")
    st.write(f"**EV:** {ev:.4f}")
    st.write(f"**Implied Win %:** {implied_prob:.2%}")
    st.write(f"**Market Win %:** {market_prob:.2%}")
    st.write(f"**Bankroll After Bet:** £{bankroll - stake if ev > 0 else bankroll:.2f}")
