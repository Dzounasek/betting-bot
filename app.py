import streamlit as st
import scipy.stats as stats
import pandas as pd
import numpy as np
import json
import os

st.set_page_config(page_title="Value Bot v7.0 THE PITCH", layout="wide")

# =========================================================
# THE PITCH EDITION: ČERNÉ POZADÍ + FOTBALOVÝ NEON DESIGN
# =========================================================
st.markdown("""
    <style>
    /* Scrollování a schování nativního posuvníku */
    html, body, [data-testid="stAppViewContainer"], .main, .stApp {
        overflow-y: scroll !important;
    }
    ::-webkit-scrollbar { width: 12px !important; background-color: #050505 !important; }
    ::-webkit-scrollbar-thumb { background-color: #22c55e !important; border-radius: 10px !important; }
    
    /* --- ZÁKLADNÍ POZADÍ (Černá + jemné fotbalové čáry) --- */
    .stApp {
        background-color: #050505 !important;
        /* Vloží reálnou fotku temného stadionu s trávníkem a překryje ji tmavým filtrem, aby nerušila text */
        background-image: linear-gradient(rgba(5, 5, 5, 0.85), rgba(5, 5, 5, 0.92)), url("https://images.unsplash.com/photo-1518605368461-1ee7c5320d7e?q=80&w=2000&auto=format&fit=crop");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        color: #e6edf3;
    }

    /* --- KARTY (EXPANDERY) --- */
    [data-testid="stExpander"] {
        background-color: rgba(10, 10, 10, 0.85) !important;
        border-radius: 16px !important;
        border: 2px solid rgba(34, 197, 94, 0.4) !important;
        box-shadow: 0 0 15px rgba(34, 197, 94, 0.1);
        margin-bottom: 25px;
    }
    
    /* --- HLAVNÍ TLAČÍTKO --- */
    button[kind="primary"] {
        background: linear-gradient(135deg, #22c55e 0%, #15803d 100%) !important;
        color: white !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 12px !important;
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.4);
        padding: 10px !important;
    }
    button[kind="primary"]:hover {
        transform: scale(1.02);
        box-shadow: 0 0 30px rgba(34, 197, 94, 0.7);
    }

    /* --- LEVÝ PANEL (SIDEBAR) --- */
    [data-testid="stSidebar"] {
        background-color: #020202 !important;
        border-right: 2px solid rgba(34, 197, 94, 0.3) !important;
    }

    /* --- BARVY PRO VALUE A TRASH --- */
    .ev-success { color: #22c55e !important; font-weight: bold !important; text-shadow: 0 0 5px rgba(34, 197, 94, 0.5); }
    .ev-trash { color: #ef4444 !important; font-weight: bold !important; }
    
    .stNumberInput, .stTextInput { margin-bottom: -15px; }
    h1, h2, h3, p, label { color: #ffffff !important; }

    /* =======================================================
       OPRAVA RADIO PŘEPÍNAČE (MASTER SWITCHER)
       ======================================================= */
    /* Nucení Streamlitu dát to do jednoho řádku s mezerou */
    div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        gap: 20px !important;
        width: 100% !important;
        margin-bottom: 30px !important;
    }

    /* Styl samotných tlačítek v přepínači */
    div[role="radiogroup"] > label {
        background-color: rgba(20, 20, 20, 0.8) !important;
        border: 2px solid #333 !important;
        border-radius: 40px !important;
        padding: 15px 30px !important;
        cursor: pointer !important;
        min-width: 250px !important; /* Zabrání zalamování textu */
        text-align: center !important;
        transition: all 0.3s ease !important;
    }

    /* Skrytí ošklivých Streamlit puntíků */
    div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    /* Zvětšení fontu uvnitř tlačítek */
    div[role="radiogroup"] > label p {
        font-size: 18px !important;
        font-weight: bold !important;
        margin: 0 !important;
    }

    /* EFEKT PŘI AKTIVACI (Highlight na základě výběru se řeší níže přes st.markdown) */
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACE SESSION STATE ---
if "show_results" not in st.session_state: st.session_state.show_results = False
if "ticket" not in st.session_state: st.session_state.ticket = []

st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>⚽ Value Bot v7.0 PRO</h1>", unsafe_allow_html=True)

# --- THE MASTER SWITCHER ---
# Streamlit horizontal=True zajistí, že to CSS výše uchopí správně do flexboxu
c_space1, c_radio, c_space2 = st.columns([1, 4, 1])
with c_radio:
    selected_mode = st.radio(
        label="Mód aplikace",
        options=["Standard Liga (1X2)", "🏆 World Cup Edition (Elo)"],
        label_visibility="collapsed",
        horizontal=True,
        key="master_mode"
    )

wc_mode = (selected_mode == "🏆 World Cup Edition (Elo)")

# --- DYNAMICKÉ OBRAZOVÉ ZMĚNY PODLE MÓDU ---
if wc_mode:
    st.markdown("<h3 style='text-align: center; color: #fbbf24; margin-bottom: 30px;'>🌍 Turnajový Mód Aktivní</h3>", unsafe_allow_html=True)
    st.markdown("""
        <style>
        /* Přebarvení aktivního tlačítka na Zlatou */
        div[role="radiogroup"] > label:last-child {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
            border-color: #fbbf24 !important;
            box-shadow: 0 0 20px rgba(245, 158, 11, 0.4) !important;
        }
        div[role="radiogroup"] > label:last-child p { color: #000 !important; }
        
        /* Přebarvení karet a posuvníku do Zlaté */
        [data-testid="stExpander"] { border-color: rgba(245, 158, 11, 0.5) !important; box-shadow: 0 0 15px rgba(245, 158, 11, 0.1); }
        ::-webkit-scrollbar-thumb { background-color: #fbbf24 !important; }
        .stApp { background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" opacity="0.04" stroke="%23fbbf24" fill="none" stroke-width="0.5"><circle cx="50" cy="50" r="20"/><path d="M 0 50 L 100 50 M 50 0 L 50 100"/></svg>'); }
        </style>
    """, unsafe_allow_html=True)
    
    c_wc1, c_wc2, c_wc3 = st.columns([1, 2, 1])
    with c_wc2:
        playoff_mode = st.toggle("🏆 Vyřazovací část (Zvyšuje Under & Remízu)", value=False)
else:
    playoff_mode = False
    st.markdown("""
        <style>
        /* Přebarvení aktivního tlačítka na Zelenou */
        div[role="radiogroup"] > label:first-child {
            background: linear-gradient(135deg, #22c55e 0%, #15803d 100%) !important;
            border-color: #4ade80 !important;
            box-shadow: 0 0 20px rgba(34, 197, 94, 0.4) !important;
        }
        div[role="radiogroup"] > label:first-child p { color: #000 !important; }
        </style>
    """, unsafe_allow_html=True)

st.divider()

# --- NÁZVY TÝMŮ ---
label_h = "Tým A" if wc_mode else "Domácí"
label_a = "Tým B" if wc_mode else "Hosté"

# --- PAMĚŤ BANKROLLU ---
BANKROLL_FILE = "bankroll_settings.json"
def load_bankroll():
    if os.path.exists(BANKROLL_FILE):
        try:
            with open(BANKROLL_FILE, "r") as f:
                return json.load(f).get("bankroll", 10000)
        except: return 10000
    return 10000

def save_bankroll(val):
    with open(BANKROLL_FILE, "w") as f:
        json.dump({"bankroll": val}, f)

def smart_float_input(label, default_val, key):
    val_str = st.text_input(label, value=str(default_val), key=key)
    try: return float(val_str.replace(",", "."))
    except: return float(default_val)

# --- SIDEBAR: TIKET A BANKROLL ---
with st.sidebar:
    st.header("💰 Bankroll")
    saved_bank = load_bankroll()
    bankroll = st.number_input("Celkový bankroll (Kč)", min_value=0, value=int(saved_bank), step=500, key="bankroll_input")
    if bankroll != saved_bank: save_bankroll(bankroll)
        
    kelly_options = {0.125: "1/8 Kelly", 0.25: "1/4 Kelly", 0.5: "1/2 Kelly", 1.0: "Full Kelly"}
    kelly_fraction = st.selectbox("Agresivita sázek", options=list(kelly_options.keys()), format_func=lambda x: kelly_options[x], index=1)

    st.divider()
    st.header("🎟️ Můj Tiket")
    if len(st.session_state.ticket) == 0:
        st.caption("Klikni na ➕ u trhu.")
    else:
        total_stake = 0; total_potential_return = 0
        for idx, bet in enumerate(st.session_state.ticket):
            with st.container():
                c_i, c_d = st.columns([5, 1])
                with c_i:
                    st.markdown(f"**{bet['label']}**")
                    st.caption(f"Kurz: {bet['odds']:.2f} | Vklad: {bet['stake']} Kč")
                with c_d:
                    if st.button("🗑️", key=f"del_bet_{idx}"):
                        st.session_state.ticket.pop(idx); st.rerun()
            total_stake += bet["stake"]; total_potential_return += bet["return_czk"]
        
        st.divider()
        st.metric("💸 Vklad", f"{total_stake} Kč")
        st.metric("💰 Návrat", f"{int(total_potential_return)} Kč")
        
        avg_ev = np.mean([b["ev"] for b in st.session_state.ticket]) * 100
        if avg_ev > 0: st.success(f"EV: +{avg_ev:.1f}%")
        else: st.error(f"EV: {avg_ev:.1f}%")
        
        if st.button("Vymazat tiket", use_container_width=True):
            st.session_state.ticket = []; st.rerun()

# --- VSTUPY HISTORIE ---
def match_history_input(team_label):
    st.subheader(f"Historie: {team_label}")
    data = {"gf": [], "ga": [], "xg": [], "xga": []}
    weights = [0.35, 0.25, 0.20, 0.13, 0.07]
    for i in range(5):
        label = "Nejnovější zápas" if i == 0 else f"Před {i+1} koly"
        st.markdown(f"**{label}**")
        c1, c2, c3, c4 = st.columns(4)
        with c1: gf = st.number_input("Góly", 0, value=1, key=f"{team_label}_gf_{i}")
        with c2: ga = st.number_input("Góly proti", 0, value=1, key=f"{team_label}_ga_{i}")
        with c3: xg = smart_float_input("xG", 1.2, key=f"{team_label}_xg_{i}")
        with c4: xga = smart_float_input("xG proti", 1.0, key=f"{team_label}_xga_{i}")
        data["gf"].append(gf); data["ga"].append(ga); data["xg"].append(xg); data["xga"].append(xga)
        if i < 4: st.divider()
    return {k: sum(v * w for v, w in zip(data[k], weights)) for k in data}

c_h, c_a = st.columns(2)
rank_h = 15; rank_a = 45

with c_h:
    with st.expander(f"🏠 HISTORIE: {label_h.upper()}", expanded=True):
        if wc_mode: 
            rank_h = st.number_input(f"FIFA Žebříček ({label_h})", 1, 200, 15)
            st.divider()
        home_data = match_history_input(label_h)
with c_a:
    with st.expander(f"🚀 HISTORIE: {label_a.upper()}", expanded=True):
        if wc_mode: 
            rank_a = st.number_input(f"FIFA Žebříček ({label_a})", 1, 200, 45)
            st.divider()
        away_data = match_history_input(label_a)

if st.button("MAGICKÝ VÝPOČET VALUE", type="primary", use_container_width=True):
    st.session_state.show_results = True

if st.session_state.show_results:
    home_lambda = ((home_data["xg"] * 0.75 + home_data["gf"] * 0.25) + (away_data["xga"] * 0.75 + away_data["ga"] * 0.25)) / 2
    away_lambda = ((away_data["xg"] * 0.75 + away_data["gf"] * 0.25) + (home_data["xga"] * 0.75 + home_data["ga"] * 0.25)) / 2

    if wc_mode:
        rank_diff = rank_a - rank_h 
        adj_factor_a = max(0.7, min(1.3, 1.0 + (rank_diff * 0.005)))
        adj_factor_b = max(0.7, min(1.3, 1.0 - (rank_diff * 0.005)))
        home_lambda *= adj_factor_a
        away_lambda *= adj_factor_b
        rho = -0.12 if playoff_mode else -0.05
    else:
        rho = -0.05

    max_g = 8
    prob_matrix = np.zeros((max_g, max_g))
    for i in range(max_g):
        for j in range(max_g):
            p = stats.poisson.pmf(i, home_lambda) * stats.poisson.pmf(j, away_lambda)
            if i == 0 and j == 0: p *= (1 - home_lambda * away_lambda * rho)
            elif i == 0 and j == 1: p *= (1 + home_lambda * rho)
            elif i == 1 and j == 0: p *= (1 + away_lambda * rho)
            elif i == 1 and j == 1: p *= (1 - rho)
            prob_matrix[i, j] = max(0, p)

    prob_matrix /= prob_matrix.sum()
    p_home = np.sum(np.tril(prob_matrix, -1)); p_draw = np.sum(np.diag(prob_matrix)); p_away = np.sum(np.triu(prob_matrix, 1))
    p_1x = p_home + p_draw; p_x2 = p_draw + p_away; p_12 = p_home + p_away
    p_dnb1 = p_home / (p_home + p_away) if (p_home + p_away) > 0 else 0.001
    p_dnb2 = p_away / (p_home + p_away) if (p_home + p_away) > 0 else 0.001
    p_btts_yes = np.sum(prob_matrix[1:, 1:]); p_btts_no = 1 - p_btts_yes
    
    def get_over(thr): return np.sum([prob_matrix[i,j] for i in range(max_g) for j in range(max_g) if i+j > thr])
    
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
    st.markdown(f"<h2 style='text-align: center;'>🎯 Predikce Skóre: {most_likely[0]} : {most_likely[1]}</h2>", unsafe_allow_html=True)
    st.divider()

    def display_market(label, prob):
        prob = max(min(prob, 0.999), 0.001)
        c1, c2, c3, c4 = st.columns([2, 1, 2, 0.5])
        with c1:
            st.write(f"**{label}**")
            st.caption(f"Model: {1/prob:.2f} ({prob*100:.1f}%)")
        with c2:
            odds = smart_float_input("Kurz", 1.0, key=f"o_{label}")
        with c3:
            if odds > 1.0:
                ev = (prob * odds) - 1
                kelly_f = max(0, (prob * odds - 1) / (odds - 1)) * kelly_fraction
                stake = bankroll * kelly_f
                if ev > 0.05: st.markdown(f"<span class='ev-success'>🔥 VALUE +{ev*100:.1f}%</span><br>Vsadit: **{int(stake)} Kč**", unsafe_allow_html=True)
                elif ev > 0: st.markdown(f"<span class='ev-success'>✅ OK +{ev*100:.1f}%</span><br>Vsadit: **{int(stake)} Kč**", unsafe_allow_html=True)
                else: st.markdown(f"<span class='ev-trash'>❌ Trash {ev*100:.1f}%</span>", unsafe_allow_html=True)
            else: ev = -1; stake = 0
        with c4:
            st.write(""); st.write("")
            if odds > 1.0 and ev > 0:
                already = label in [b["label"] for b in st.session_state.ticket]
                if st.button("✅" if already else "➕", key=f"add_{label}", disabled=already):
                    st.session_state.ticket.append({"label": label, "prob": prob, "odds": odds, "stake": int(stake), "return_czk": int(stake * odds), "ev": ev})
                    st.rerun()

    tab1, tab2, tab3 = st.tabs(["🏆 Zápas & Ostatní", "⚽ Góly v Zápase", "🥅 Góly Týmů"])
    with tab1:
        c_1, c_2 = st.columns(2)
        with c_1:
            st.subheader("1X2 & Dvojitá šance")
            display_market(f"Výhra {label_h} (1)", p_home); display_market("Remíza (X)", p_draw); display_market(f"Výhra {label_a} (2)", p_away); st.divider()
            display_market(f"Neprohra {label_h} (1X)", p_1x); display_market(f"Neprohra {label_a} (X2)", p_x2); display_market("Kdokoli vyhraje (12)", p_12)
        with c_2:
            st.subheader("Sázky bez remízy (DNB) & BTTS")
            display_market(f"DNB 1 ({label_h})", p_dnb1); display_market(f"DNB 2 ({label_a})", p_dnb2); st.divider()
            display_market("BTTS (Ano)", p_btts_yes); display_market("BTTS (Ne)", p_btts_no)
    with tab2:
        c_1, c_2 = st.columns(2)
        with c_1:
            st.subheader("Over (Více než)")
            display_market("Over 0.5", p_o05); display_market("Over 1.5", p_o15); display_market("Over 2.5", p_o25); display_market("Over 3.5", p_o35); display_market("Over 4.5", p_o45)
        with c_2:
            st.subheader("Under (Méně než)")
            display_market("Under 0.5", p_u05); display_market("Under 1.5", p_u15); display_market("Under 2.5", p_u25); display_market("Under 3.5", p_u35); display_market("Under 4.5", p_u45)
    with tab3:
        c_1, c_2 = st.columns(2)
        with c_1:
            st.subheader(f"{label_h} Góly")
            display_market(f"{label_h} Over 0.5", p_h_o05); display_market(f"{label_h} Under 0.5", p_h_u05); st.divider()
            display_market(f"{label_h} Over 1.5", p_h_o15); display_market(f"{label_h} Under 1.5", p_h_u15); st.divider()
            display_market(f"{label_h} Over 2.5", p_h_o25); display_market(f"{label_h} Under 2.5", p_h_u25)
        with c_2:
            st.subheader(f"{label_a} Góly")
            display_market(f"{label_a} Over 0.5", p_a_o05); display_market(f"{label_a} Under 0.5", p_a_u05); st.divider()
            display_market(f"{label_a} Over 1.5", p_a_o15); display_market(f"{label_a} Under 1.5", p_a_u15); st.divider()
            display_market(f"{label_a} Over 2.5", p_a_o25); display_market(f"{label_a} Under 2.5", p_a_u25)
