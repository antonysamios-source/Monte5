import streamlit as st
import pandas as pd
import numpy as np
import requests
from io import StringIO

# --- Load Player Stats Data from GitHub ---
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/antonysamios-source/Monte5/main/player_surface_stats_master.csv"
    response = requests.get(url)
    return pd.read_csv(StringIO(response.text))

stats_df = load_data()

# --- Streamlit Config ---
st.set_page_config(layout="wide")
st.title("🎾 Tennis In-Play Betting Simulator")

col1, col2 = st.columns(2)
with col1:
    st.header("Player A")
    player_a = st.selectbox("Select Player A", sorted(stats_df["player"].unique()), key="player_a")
    sets_a = st.number_input("Sets Won", 0, 5, 0, key="sets_a")
    games_a = st.number_input("Games (Current Set)", 0, 7, 0, key="games_a")
    points_a = st.number_input("Points", 0, 4, 0, key="points_a")

with col2:
    st.header("Player B")
    player_b = st.selectbox("Select Player B", sorted(stats_df["player"].unique()), index=1, key="player_b")
    sets_b = st.number_input("Sets Won", 0, 5, 0, key="sets_b")
    games_b = st.number_input("Games (Current Set)", 0, 7, 0, key="games_b")
    points_b = st.number_input("Points", 0, 4, 0, key="points_b")

# --- Match Settings ---
st.subheader("Match Settings")
col3, col4, col5 = st.columns(3)
with col3:
    surface = st.selectbox("Surface", ["Hard", "Clay", "Grass"])
with col4:
    match_format = st.radio("Match Format", [3, 5], horizontal=True)
with col5:
    server = st.radio("Who is serving?", [player_a, player_b])

# --- Bankroll & Odds ---
st.subheader("Odds & Toggles")
bankroll = st.number_input("Your Bankroll (£)", value=1000.0, step=10.0)
col6, col7, col8 = st.columns(3)
with col6:
    odds_a = st.number_input(f"Odds for {player_a}", value=2.0, key="odds_a")
with col7:
    odds_b = st.number_input(f"Odds for {player_b}", value=2.0, key="odds_b")
with col8:
    kelly_toggle = st.radio("Kelly Fraction", ["Full Kelly", "Half Kelly"], horizontal=True)

# --- Helper Functions ---
def get_stat(player, surface, col):
    row = stats_df[(stats_df["player"] == player) & (stats_df["surface"] == surface)]
    return row[col].values[0] if not row.empty else 0.5

def calc_ev(prob, odds):
    return (prob * odds) - 1

def kelly_stake(prob, odds, bankroll, kelly_fraction):
    b = odds - 1
    q = 1 - prob
    stake_frac = (b * prob - q) / b
    stake_frac = max(stake_frac, 0)
    stake_frac = stake_frac if kelly_fraction == "Full Kelly" else stake_frac / 2
    stake = bankroll * stake_frac
    return round(max(stake, 2.0), 2)  # Enforce £2.00 minimum

# --- Calculate Win Percentages ---
pA_serve = get_stat(player_a, surface, "serve_win_pct")
pB_serve = get_stat(player_b, surface, "serve_win_pct")

# Simplified implied win probability
implied_prob_a = round((pA_serve + (1 - pB_serve)) / 2, 4)
implied_prob_b = round(1 - implied_prob_a, 4)

st.markdown(f"**Implied Probability**: `{player_a}` = `{implied_prob_a*100:.2f}%`, `{player_b}` = `{implied_prob_b*100:.2f}%`")

# --- Expected Value ---
ev_a = calc_ev(implied_prob_a, odds_a)
ev_b = calc_ev(implied_prob_b, odds_b)
st.markdown(f"**Expected Value (EV)**: `{player_a}` = `{ev_a:.3f}`, `{player_b}` = `{ev_b:.3f}`")

# --- Kelly Stakes ---
stake_a = kelly_stake(implied_prob_a, odds_a, bankroll, kelly_toggle)
stake_b = kelly_stake(implied_prob_b, odds_b, bankroll, kelly_toggle)

# --- Trade Suggestions ---
st.subheader("💵 Trade Suggestions")
if ev_a > 0:
    st.success(f"🟢 Back {player_a} with £{stake_a} (EV: {ev_a:.3f})")
else:
    st.warning(f"🔴 No +EV back opportunity for {player_a}")

if ev_b > 0:
    st.success(f"🟢 Back {player_b} with £{stake_b} (EV: {ev_b:.3f})")
else:
    st.warning(f"🔴 No +EV back opportunity for {player_b}")

# --- Placeholder for Future Features ---
st.markdown("---")
st.info("📊 Position tracking, dynamic Monte Carlo simulations, hedging logic, and real-time Betfair odds integration will be added soon!")

# --- UI Styling ---
st.markdown("""
<style>
div.block-container { padding-top: 2rem; }
.stRadio > div { flex-direction: row !important; }
.stNumberInput label { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)
