# tennis_simulator_app.py
import streamlit as st
import pandas as pd
import numpy as np
import random
import math
import matplotlib.pyplot as plt

# --- Load Data from GitHub ---
DATA_URL = "https://raw.githubusercontent.com/antonysamios-source/Monte5/main/player_surface_stats_master.csv"
@st.cache_data
def load_stats():
    return pd.read_csv(DATA_URL)
stats_df = load_stats()

# --- SETTINGS ---
st.set_page_config(page_title="Tennis Monte Carlo Simulator", layout="wide")
st.title("🎾 Tennis Betting Simulator")
st.markdown("##### Live In-Match Monte Carlo Engine with EV, Kelly Strategy & Pressure Logic")

# --- HELPER FUNCTIONS ---
def kelly_stake(prob, odds, bankroll, commission, min_bet=2.0, half=False):
    k = (prob * (odds - 1) - (1 - prob)) / (odds - 1)
    k = max(k, 0)
    stake = k * bankroll / (2 if half else 1)
    return round(stake if stake >= min_bet else (min_bet if stake > 0 else 0), 2)

def simulate_game(p_win, pressure=False, pressure_adj=0.05):
    if pressure:
        p_win = min(1, p_win + (1 - p_win) * pressure_adj)
    return random.random() < p_win

def monte_sim(player_a_stats, player_b_stats, sets_target, score_state, pressure_adj=0.05):
    wins = 0
    total = 100000
    for _ in range(total):
        sa, sb = score_state['sets']
        ga, gb = score_state['games']
        serving = score_state['server']

        while sa < sets_target and sb < sets_target:
            p_serve = player_a_stats['serve'] if serving == 'A' else player_b_stats['serve']
            p_return = player_b_stats['return'] if serving == 'A' else player_a_stats['return']
            p_win = (p_serve + p_return) / 2
            pressure = (ga == 5 and gb >= 5) or (sa == sets_target - 1 and sb == sets_target - 1)
            game_won = simulate_game(p_win, pressure, pressure_adj)

            if game_won:
                if serving == 'A': ga += 1
                else: gb += 1
            else:
                if serving == 'A': gb += 1
                else: ga += 1

            # Set win condition
            if (ga >= 6 and ga - gb >= 2):
                sa += 1
                ga, gb = 0, 0
            elif (gb >= 6 and gb - ga >= 2):
                sb += 1
                ga, gb = 0, 0

            serving = 'B' if serving == 'A' else 'A'

        if sa > sb:
            wins += 1

    return round(wins / total, 4)

def get_stats(player, surface):
    df = stats_df[(stats_df['player'] == player) & (stats_df['surface'] == surface)]
    if not df.empty:
        row = df.iloc[0]
        return {'serve': row['serve_points_won_pct'], 'return': row['return_points_won_pct']}
    return {'serve': 0.60, 'return': 0.40}  # fallback

# --- USER INPUTS ---

col1, col2 = st.columns(2)
with col1:
    surface = st.selectbox("Surface", ["Hard", "Clay", "Grass"])
    gender = st.radio("Tour", ["ATP", "WTA"])
    format_sets = st.radio("Best of...", [3, 5])
    sets_to_win = format_sets // 2 + 1
with col2:
    bankroll = st.number_input("Bankroll (£)", min_value=10.0, value=1000.0, step=10.0)
    commission = st.slider("Betfair Commission %", 0, 10, 5, 1)
    half_kelly = st.checkbox("Use Half Kelly?", value=True)
    pressure_logic = st.checkbox("Enable Pressure Logic?", value=True)

# Player Selection
players = sorted(stats_df["player"].unique())
player_a = st.selectbox("Player A", players, key="pA")
player_b = st.selectbox("Player B", players, key="pB")

# Odds Inputs
col3, col4 = st.columns(2)
with col3:
    odds_a = st.number_input(f"Betfair Odds {player_a}", value=2.0)
with col4:
    odds_b = st.number_input(f"Betfair Odds {player_b}", value=2.0)

# Score Inputs
st.markdown("### 🟩 Scoreboard (Wimbledon Style)")
sc1, sc2, sc3, sc4 = st.columns(4)
sets_a = sc1.number_input(f"{player_a} Sets", 0, 5, 0)
games_a = sc2.number_input(f"{player_a} Games", 0, 7, 0)
points_a = sc3.number_input(f"{player_a} Points", 0, 4, 0)

sets_b = sc1.number_input(f"{player_b} Sets", 0, 5, 0)
games_b = sc2.number_input(f"{player_b} Games", 0, 7, 0)
points_b = sc3.number_input(f"{player_b} Points", 0, 4, 0)

server = st.radio("Who is serving?", [player_a, player_b])

# --- RUN SIM ---
if st.button("Run 100,000 Monte Carlo Simulations"):
    st.info("Running simulations, this may take a few seconds...")
    player_a_stats = get_stats(player_a, surface)
    player_b_stats = get_stats(player_b, surface)
    score = {
        'sets': (sets_a, sets_b),
        'games': (games_a, games_b),
        'server': 'A' if server == player_a else 'B'
    }

    win_prob = monte_sim(player_a_stats, player_b_stats, sets_to_win, score, pressure_adj=0.05 if pressure_logic else 0)
    stake = kelly_stake(win_prob, odds_a, bankroll, commission, half=half_kelly)

    st.success(f"Win Probability for {player_a}: {win_prob*100:.2f}%")
    if stake >= 2:
        net_profit = stake * (odds_a - 1) * (1 - commission/100)
        st.markdown(f"💸 **Suggested Stake**: £{stake}  \n📈 **Estimated Profit**: £{net_profit:.2f}")
    else:
        st.warning("⚠️ No +EV bet or minimum £2 stake not reached.")
