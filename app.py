import streamlit as st
import scipy.stats as stats
import pandas as pd
import numpy as np
import json
import os

st.set_page_config(page_title="Value Bot v5.1", layout="wide")

st.title("⚽ Betting Bot v5.1 PRO + Kelly")
st.markdown("Optimalizováno pro mobil. Podpora čárek (,) a automatické ukládání bankrollu.")

# --- 1. FUNKCE PRO PAMĚŤ BANKROLLU ---
BANKROLL_FILE = "bankroll_settings.json"

def load_bankroll():
    if os.path.exists(BANKROLL_FILE):
        try:
            with open(BANKROLL_FILE, "r") as f:
                return json.load(f).get("bankroll", 10000)
        except:
            return 10000
    return 10000

def save_bankroll(val):
    with open(BANKROLL_FILE, "w") as f:
        json.dump({"bankroll": val}, f)

# --- 2. FUNKCE PRO ČÁRKY A TEČKY ---
def smart_float_input(label, default_val, key):
    # Uživatel může zadat text s čárkou
    val_str = st.text_input(label, value=str(default_val), key=key)
    try:
        # Převedeme případnou čárku na tečku a uděláme z toho float
        return float(val_str.replace(",", "."))
    except ValueError:
        # Pokud se zadá nesmysl (např. písmena), vrátí se defaultní hodnota
        return float(default_val)

# --- SIDEBAR: MONEY MANAGEMENT ---
with st.sidebar:
    st.header("💰 Bankroll Management")
    
    saved_bank = load_bankroll()
    bankroll = st.number_input("Tvůj celkový bankroll (Kč)", min_value=0, value=int(saved_bank), step=500)
    
    # Uložíme nový bankroll, pokud ho uživatel změní
    if bankroll != saved_bank:
        save_bankroll(bankroll)
        
    kelly_fraction = st.select_slider(
        "Agresivita (Kelly Fraction)",
        options=[0.125, 0.25, 0.5, 1.0],
        value=0.25,
        help="1/8 Kelly (konzervativní), 1/4 Kelly (standard), 1/2 Kelly (agresivní), Full Kelly (riskantní)"
    )
    st.caption("Doporučeno: 0.25 (1/4 Kelly) pro dlouhodobou udržitelnost.")

# --- 3. FUNKCE PRO VSTUP DAT ---
def match_history_input(team_label):
    st.subheader(f"Historie: {team_label}")
    data = {"gf": [], "ga": [], "xg": [], "xga": []}
    
    weights = [0.35, 0.25, 0.20, 0.13, 0.07] # Váhy pro Time Decay
    
    for i in range(5):
        label = "Dnešní forma (Nejnovější)" if i == 0 else f"Zápas před {i+1} koly"
        st.markdown(f"**{label}**")
        
        c1, c2 = st.columns(2)
        with c1:
            gf = st.number_input("Góly", min_value=0, value=1, step=1, key=f"{team_label}_gf_{i}")
        with c2:
            ga = st.number_input("Góly proti", min_value=0, value=1, step=1, key=f"{team_label}_ga_{i}")
            
        c3, c4 = st.columns(2)
        with c3:
            # Využití nové funkce pro xG, aby brala čárky
            xg = smart_float_input("xG", 1.2, key=f"{team_label}_xg_{i}")
        with c4:
            xga = smart_float_input("xG proti", 1.0, key=f"{team_label}_xga_{i}")
        
        data["gf"].append(gf)
        data["ga"].append(ga)
        data["xg"].append(xg)
        data["xga"].append(xga)
        
        if i < 4: st.divider()
            
    avg_stats = {}
    for key in data:
        avg_stats[key] = sum(val * w for val, w in zip(data[key], weights))
        
    return avg_stats

# --- 4. AI KOMENTÁŘ ---
def get_ai_commentary(p_home, p_draw, p_away, p_over, pred_score):
    comments = []
    if p_home > 0.65: comments.append("🏠 Domácí jsou dneska absolutní páni hřiště. Hosté si nejspíš přijeli jen pro výslužku.")
    elif p_away > 0.65: comments.append("🚀 Hosté jedou jako parní válec. Domácí fanoušci budou v 70. minutě hromadně odcházet na párek.")
    elif p_draw > 0.35: comments.append("🤝 Tady to smrdí remízou na sto honů. Oba týmy se budou bát víc než maturanta u tabule.")
    else: comments.append("⚖️ Bookmaker si rve vlasy, tohle je vyrovnaný jak souboj dvou hlemýžďů.")

    if p_over > 0.70: comments.append("🥅 Očekávám totální ofenzivní orgie. Brankáři tam jsou dneska jen jako kužely.")
    elif p_over < 0.35: comments.append("💤 Připrav si kafe. Tady hrozí taková nuda, že i rozhodčí u toho možná usne.")
    
    if pred_score == (0,0): comments.append("💀 Predikce 0:0? Radši běž ven se psem, ušetříš si nervy.")
    return " ".join(comments)

# --- HLAVNÍ FORMULÁŘ ---
col1, col2 = st.columns(2)
with col1:
    with st.expander("🏠 HISTORIE DOMÁCÍCH", expanded=True):
        home_data = match_history_input("Domácí")
with col2:
    with st.expander("🚀 HISTORIE HOSTŮ", expanded=True):
        away_data = match_history_input("Hosté")

if st.button("MAGICKÝ VÝPOČET VALUE & KELLY", type="primary", use_container_width=True):
    # Výpočet Lambdy
    home_lambda = ((home_data["xg"] * 0.7 + home_data["gf"] * 0.3) + (away_data["xga"] * 0.7 + away_data["ga"] * 0.3)) / 2
    away_lambda = ((away_data["xg"] * 0.7 + away_data["gf"] * 0.3) + (home_data["xga"] * 0.7 + home_data["ga"] * 0.3)) / 2

    # MATICE + DIXON-COLES
    max_g = 8
    prob_matrix = np.zeros((max_g, max_g))
    rho = -0.05 
    
    for i in range(max_g):
        for j in range(max_g):
            p = stats.poisson.pmf(i, home_lambda) * stats.poisson.pmf(j, away_lambda)
            if i == 0 and j == 0: p *= (1 - home_lambda * away_lambda * rho)
            elif i == 0 and j == 1: p *= (1 + home_lambda * rho)
            elif i == 1 and j == 0: p *= (1 + away_lambda * rho)
            elif i == 1 and j == 1: p *= (1 - rho)
            prob_matrix[i, j] = max(0, p)

    prob_matrix /= prob_matrix.sum()

    # Pravděpodobnosti
    p_home = np.sum(np.tril(prob_matrix, -1))
    p_draw = np.sum(np.diag(prob_matrix))
    p_away = np.sum(np.triu(prob_matrix, 1))
    p_over25 = np.sum([prob_matrix[i, j] for i in range(max_g) for j in range(max_g) if i+j > 2.5])
    p_btts = np.sum(prob_matrix[1:, 1:])
    most_likely = np.unravel_index(np.argmax(prob_matrix), prob_matrix.shape)
    
    st.divider()
    st.info(get_ai_commentary(p_home, p_draw, p_away, p_over25, most_likely))
    st.markdown(f"<h2 style='text-align: center;'>🎯 Predikce: {most_likely[0]} : {most_likely[1]}</h2>", unsafe_allow_html=True)
    st.divider()

    # VÝSLEDKY S KELLYHO KRITÉRIEM
    def display_market(label, prob):
        c_res, c_odds, c_kelly = st.columns([2, 1, 1.5])
        with c_res:
            st.write(f"**{label}**")
            st.caption(f"Model: {1/prob:.2f} ({prob*100:.1f}%)")
        with c_odds:
            # Využití nové funkce i pro kurzy, abys mohl psát např. 1,85
            user_odds = smart_float_input("Kurz Tipsport", 1.0, key=f"odds_{label}")
        
        with c_kelly:
            if user_odds > 1.0:
                ev = (prob * user_odds) - 1
                kelly_f = (prob * user_odds - 1) / (user_odds - 1)
                fractional_kelly = kelly_f * kelly_fraction
                
                if ev > 0:
                    stake_czk = bankroll * fractional_kelly
                    st.success(f"🔥 VALUE +{ev*100:.1f}%")
                    st.write(f"💰 Vsadit: **{max(0, int(stake_czk))} Kč**")
                    st.caption(f"({fractional_kelly*100:.1f}% banku)")
                else:
                    st.error(f"❌ Trash {ev*100:.1f}%")

    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.subheader("🏆 Vítěz zápasu")
        display_market("Výhra Domácí (1)", p_home)
        display_market("Remíza (X)", p_draw)
        display_market("Výhra Hosté (2)", p_away)

    with res_col2:
        st.subheader("⚽ Góly & Ostatní")
        display_market("Over 2.5", p_over25)
        display_market("BTTS (Oba dají)", p_btts)
        display_market("Neprohra Domácí (1X)", p_home + p_draw)
