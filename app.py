import streamlit as st
import scipy.stats as stats
import pandas as pd
import numpy as np
import json
import os

st.set_page_config(page_title="Value Bot v5.4", layout="wide")

st.title("⚽ Betting Bot v5.4 PRO + Kelly")
st.markdown("Plná nálož trhů. Spolehlivé live aktualizace pro mobil.")

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
    val_str = st.text_input(label, value=str(default_val), key=key)
    try:
        return float(val_str.replace(",", "."))
    except ValueError:
        return float(default_val)

# --- INICIALIZACE SESSION STATE ---
if "show_results" not in st.session_state:
    st.session_state.show_results = False

# --- SIDEBAR: MONEY MANAGEMENT ---
with st.sidebar:
    st.header("💰 Bankroll Management")
    
    saved_bank = load_bankroll()
    # Přidán klíč (key) pro bankroll
    bankroll = st.number_input("Tvůj celkový bankroll (Kč)", min_value=0, value=int(saved_bank), step=500, key="bankroll_input")
    
    if bankroll != saved_bank:
        save_bankroll(bankroll)
        
    # Výměna slideru za spolehlivější selectbox s jasnými popisky
    kelly_options = {
        0.125: "1/8 Kelly (Konzervativní)",
        0.25: "1/4 Kelly (Standard - Doporučeno)",
        0.5: "1/2 Kelly (Agresivní)",
        1.0: "Full Kelly (Riskantní)"
    }
    
    kelly_fraction = st.selectbox(
        "Agresivita sázek",
        options=list(kelly_options.keys()),
        format_func=lambda x: kelly_options[x],
        index=1,
        key="kelly_selectbox"
    )

# --- 3. FUNKCE PRO VSTUP DAT ---
def match_history_input(team_label):
    st.subheader(f"Historie: {team_label}")
    data = {"gf": [], "ga": [], "xg": [], "xga": []}
    
    weights = [0.35, 0.25, 0.20, 0.13, 0.07] # Time Decay
    
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
    st.session_state.show_results = True

if st.session_state.show_results:
    home_lambda = ((home_data["xg"] * 0.7 + home_data["gf"] * 0.3) + (away_data["xga"] * 0.7 + away_data["ga"] * 0.3)) / 2
    away_lambda = ((away_data["xg"] * 0.7 + away_data["gf"] * 0.3) + (home_data["xga"] * 0.7 + home_data["ga"] * 0.3)) / 2

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

    p_home = np.sum(np.tril(prob_matrix, -1))
    p_draw = np.sum(np.diag(prob_matrix))
    p_away = np.sum(np.triu(prob_matrix, 1))
    
    p_1x = p_home + p_draw
    p_x2 = p_draw + p_away
    p_12 = p_home + p_away
    p_dnb1 = p_home / (p_home + p_away) if (p_home + p_away) > 0 else 0.001
    p_dnb2 = p_away / (p_home + p_away) if (p_home + p_away) > 0 else 0.001
    
    p_btts_yes = np.sum(prob_matrix[1:, 1:])
    p_btts_no = 1 - p_btts_yes
    
    def get_over(threshold):
        return np.sum([prob_matrix[i, j] for i in range(max_g) for j in range(max_g) if i+j > threshold])
    
    p_o05 = get_over(0.5); p_u05 = 1 - p_o05
    p_o15 = get_over(1.5); p_u15 = 1 - p_o15
    p_o25 = get_over(2.5); p_u25 = 1 - p_o25
    p_o35 = get_over(3.5); p_u35 = 1 - p_o35
    p_o45 = get_over(4.5); p_u45 = 1 - p_o45
    
    p_h_o05 = np.sum(prob_matrix[1:, :]); p_h_u05 = 1 - p_h_o05
    p_h_o15 = np.sum(prob_matrix[2:, :]); p_h_u15 = 1 - p_h_o15
    p_h_o25 = np.sum(prob_matrix[3:, :]); p_h_u25 = 1 - p_h_o25
    
    p_a_o05 = np.sum(prob_matrix[:, 1:]); p_a_u05 = 1 - p_a_o05
    p_a_o15 = np.sum(prob_matrix[:, 2:]); p_a_u15 = 1 - p_a_o15
    p_a_o25 = np.sum(prob_matrix[:, 3:]); p_a_u25 = 1 - p_a_o25

    most_likely = np.unravel_index(np.argmax(prob_matrix), prob_matrix.shape)
    
    st.divider()
    st.info(get_ai_commentary(p_home, p_draw, p_away, p_o25, most_likely))
    st.markdown(f"<h2 style='text-align: center;'>🎯 Predikce: {most_likely[0]} : {most_likely[1]}</h2>", unsafe_allow_html=True)
    st.divider()

    def display_market(label, prob):
        prob = max(min(prob, 0.999), 0.001) 
        c_res, c_odds, c_kelly = st.columns([2, 1, 1.5])
        with c_res:
            st.write(f"**{label}**")
            st.caption(f"Model: {1/prob:.2f} ({prob*100:.1f}%)")
        with c_odds:
            user_odds = smart_float_input("Kurz", 1.0, key=f"odds_{label}")
        with c_kelly:
            if user_odds > 1.0:
                ev = (prob * user_odds) - 1
                kelly_f = (prob * user_odds - 1) / (user_odds - 1)
                fractional_kelly = kelly_f * kelly_fraction
                
                if ev > 0.05:
                    stake_czk = bankroll * fractional_kelly
                    st.success(f"🔥 VALUE +{ev*100:.1f}%")
                    st.write(f"💰 Vsadit: **{max(0, int(stake_czk))} Kč**")
                elif ev > 0:
                    stake_czk = bankroll * fractional_kelly
                    st.warning(f"✅ OK +{ev*100:.1f}%")
                    st.write(f"💰 Vsadit: **{max(0, int(stake_czk))} Kč**")
                else:
                    st.error(f"❌ Trash {ev*100:.1f}%")
                    
    tab1, tab2, tab3 = st.tabs(["🏆 Zápas & Ostatní", "⚽ Góly v Zápase", "🥅 Góly Týmů"])

    with tab1:
        t1_col1, t1_col2 = st.columns(2)
        with t1_col1:
            st.subheader("1X2 & Dvojitá šance")
            display_market("Výhra Domácí (1)", p_home)
            display_market("Remíza (X)", p_draw)
            display_market("Výhra Hosté (2)", p_away)
            st.divider()
            display_market("Neprohra Domácí (1X)", p_1x)
            display_market("Neprohra Hosté (X2)", p_x2)
            display_market("Kdokoli vyhraje (12)", p_12)
            
        with t1_col2:
            st.subheader("Sázky bez remízy (DNB) & BTTS")
            display_market("DNB 1 (Domácí)", p_dnb1)
            display_market("DNB 2 (Hosté)", p_dnb2)
            st.divider()
            display_market("BTTS (Ano)", p_btts_yes)
            display_market("BTTS (Ne)", p_btts_no)

    with tab2:
        t2_col1, t2_col2 = st.columns(2)
        with t2_col1:
            st.subheader("Over (Více než)")
            display_market("Over 0.5", p_o05)
            display_market("Over 1.5", p_o15)
            display_market("Over 2.5", p_o25)
            display_market("Over 3.5", p_o35)
            display_market("Over 4.5", p_o45)
        with t2_col2:
            st.subheader("Under (Méně než)")
            display_market("Under 0.5", p_u05)
            display_market("Under 1.5", p_u15)
            display_market("Under 2.5", p_u25)
            display_market("Under 3.5", p_u35)
            display_market("Under 4.5", p_u45)

    with tab3:
        t3_col1, t3_col2 = st.columns(2)
        with t3_col1:
            st.subheader("Domácí Góly")
            display_market("Domácí Over 0.5", p_h_o05)
            display_market("Domácí Under 0.5", p_h_u05)
            st.divider()
            display_market("Domácí Over 1.5", p_h_o15)
            display_market("Domácí Under 1.5", p_h_u15)
            st.divider()
            display_market("Domácí Over 2.5", p_h_o25)
            display_market("Domácí Under 2.5", p_h_u25)

        with t3_col2:
            st.subheader("Hosté Góly")
            display_market("Hosté Over 0.5", p_a_o05)
            display_market("Hosté Under 0.5", p_a_u05)
            st.divider()
            display_market("Hosté Over 1.5", p_a_o15)
            display_market("Hosté Under 1.5", p_a_u15)
            st.divider()
            display_market("Hosté Over 2.5", p_a_o25)
            display_market("Hosté Under 2.5", p_a_u25)
