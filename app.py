import streamlit as st
import scipy.stats as stats
import pandas as pd
import numpy as np
import json
import os

st.set_page_config(page_title="Value Bot v7.1 PRO", layout="wide")

# =========================================================
# THE PITCH EDITION: ČISTÉ ČERNÉ POZADÍ + FIXNUTÝ SWITCHER
# =========================================================
st.markdown("""
    <style>
    /* Natvrdo vynutí scrollování na hlavní stránce */
    html, body, [data-testid="stAppViewContainer"], .main, .stApp {
        overflow-y: scroll !important;
    }
    ::-webkit-scrollbar {
        width: 14px !important;
        display: block !important;
        background-color: #000000 !important;
    }
    ::-webkit-scrollbar-track {
        background: #000000 !important; 
    }
    ::-webkit-scrollbar-thumb {
        background-color: #22c55e !important;
        border-radius: 10px !important;
        border: 3px solid #000000 !important;
    }
    
    /* --- DESIGN v7.1 THE PITCH --- */
    .stApp {
        background-color: #000000 !important; 
        background-image: 
            url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MCIgaGVpZ2h0PSI4MCIgdmlld0JveD0iMCAwIDQwIDQwIj48ZyBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiMyMmM1NWUiIGZpbGwtb3BhY2l0eT0iMC4wMyI+PHBhdGggZD0iTTAgMGg0MHY0MEgwVjB6bTIwIDIwaDIwdjIwSDIwVjIwek0wIDIwaDIwdjIwSDBWMjB6bTIwIDBIMHYyMGgyMFYyMHoiLz48L2c+PC9nPjwvc3ZnPg==');
        color: #e6edf3;
    }

    /* Karty s historií jako lajny na hřišti */
    [data-testid="stExpander"] {
        background-color: rgba(10, 10, 10, 0.9) !important;
        border-radius: 16px !important;
        border: 2px solid rgba(34, 197, 94, 0.4) !important;
        box-shadow: 0 0 15px rgba(34, 197, 94, 0.1);
        margin-bottom: 25px;
    }
    
    /* Hlavní tlačítko */
    button[kind="primary"] {
        background: linear-gradient(135deg, #22c55e 0%, #15803d 100%) !important;
        color: white !important;
        font-weight: 800 !important;
        border: none !important;
        border-radius: 12px !important;
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.4);
    }
    button[kind="primary"]:hover {
        transform: scale(1.02);
        box-shadow: 0 0 30px rgba(34, 197, 94, 0.7);
    }

    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 2px solid rgba(34, 197, 94, 0.3) !important;
    }

    .ev-success { color: #22c55e !important; font-weight: bold !important; text-shadow: 0 0 5px rgba(34, 197, 94, 0.5); }
    .ev-trash { color: #ef4444 !important; font-weight: bold !important; }
    .stNumberInput { margin-bottom: -15px; }

    /* --- 🌟 KOMPLETNÍ FIX MODERÍHO SWITCHERU 🌟 --- */
    /* Schováme hnusné kulaté rádio tečky */
    div[data-testid="stRadio"]     div[data-testid="stMarkdownContainer"] p {
        font-size: 16px !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        gap: 15px !important;
        background-color: #0a0a0a !important;
        border: 2px solid rgba(34, 197, 94, 0.5) !important;
        padding: 8px !important;
        border-radius: 50px !important;
        width: 55% !important;
        margin: 0 auto 20px auto !important;
        box-shadow: 0 0 20px rgba(34, 197, 94, 0.15);
    }

    /* Styl pro samotné labely tlačítek */
    div[data-testid="stRadio"] > div[role="radiogroup"] > label {
        flex: 1 !important;
        background-color: transparent !important;
        border-radius: 40px !important;
        padding: 10px 20px !important;
        text-align: center !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        cursor: pointer !important;
        transition: all 0.25s ease !important;
        border: 1px solid transparent !important;
    }

    /* Schování nativního Streamlit puntíku */
    div[data-testid="stRadio"] > div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    /* AKTIVNÍ: Standardní liga (Neonově zelená) */
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:first-child[data-checked="true"] {
        background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        box-shadow: 0 0 15px rgba(34, 197, 94, 0.5) !important;
    }

    /* AKTIVNÍ: World Cup (Zlatá) */
    div[data-testid="stRadio"] > div[role="radiogroup"] > label:last-child[data-checked="true"] {
        background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 50%, #f59e0b 100%) !important;
        color: #000000 !important;
        font-weight: 800 !important;
        box-shadow: 0 0 20px rgba(245, 158, 11, 0.6) !important;
    }
    </style>
""", unsafe_allow_html=True)

if "show_results" not in st.session_state: st.session_state.show_results = False
if "ticket" not in st.session_state: st.session_state.ticket = []

st.markdown("<h1 style='text-align: center; color: white;'>⚽ Value Bot v7.1 PRO</h1>", unsafe_allow_html=True)

# --- THE MASTER SWITCHER (Přidáno horizontal=True pro řádkové vykreslení) ---
selected_mode = st.radio(
    label="Mód aplikace",
    options=["Standard Liga (1X2)", "🏆 World Cup Edition (Elo)"],
    label_visibility="collapsed",
    horizontal=True,
    key="master_mode"
)
wc_mode = (selected_mode == "🏆 World Cup Edition (Elo)")

if wc_mode:
    st.markdown("<h3 style='text-align: center; color: #fbbf24;'>🌍 Turnajový Mód Aktivní</h3>", unsafe_allow_html=True)
    st.markdown("""
        <style>
        [data-testid="stExpander"] { border: 2px solid rgba(245, 158, 11, 0.6) !important; box-shadow: 0 0 15px rgba(245, 158, 11, 0.1); }
        div[data-testid="stRadio"] > div[role="radiogroup"] { border: 2px solid #f59e0b !important; }
        </style>
    """, unsafe_allow_html=True)
    
    c_wc = st.columns([2, 1, 2])
    with c_wc[1]:
        playoff_mode = st.toggle("🏆 Vyřazovací část (Zvyšuje Under & Remízu)", value=False)
else:
    playoff_mode = False

st.divider()

# --- 1. FUNKCE PRO PAMĚŤ BANKROLLU ---
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
    except ValueError: return float(default_val)

# =========================================================
# 🎟️ TIKET A BANKROLL (SIDEBAR VLEVO)
# =========================================================
with st.sidebar:
    st.header("💰 Bankroll Management")
    saved_bank = load_bankroll()
    bankroll = st.number_input("Tvůj celkový bankroll (Kč)", min_value=0, value=int(saved_bank), step=500, key="bankroll_input")
    if bankroll != saved_bank: save_bankroll(bankroll)
        
    kelly_options = {0.125: "1/8 Kelly", 0.25: "1/4 Kelly", 0.5: "1/2 Kelly", 1.0: "Full Kelly"}
    kelly_fraction = st.selectbox("Agresivita sázek", options=list(kelly_options.keys()), format_func=lambda x: kelly_options[x], index=1)

    st.divider()
    st.header("🎟️ Můj Tiket (SOLO)")

    if len(st.session_state.ticket) == 0:
        st.caption("Zatím žádné sázky. Klikni na ➕ u libovolného trhu.")
    else:
        total_stake = 0; total_potential_return = 0
        n_sim = 1000; sim_results = np.zeros(n_sim)

        for idx, bet in enumerate(st.session_state.ticket):
            with st.container():
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    st.markdown(f"**{bet['label']}**")
                    st.caption(f"Kurz: {bet['odds']:.2f} | Sázka: {bet['stake']} Kč | Návrat: **{bet['return_czk']} Kč** (+{bet['profit_czk']} Kč)")
                with col_del:
                    if st.button("🗑️", key=f"del_bet_{idx}"):
                        st.session_state.ticket.pop(idx); st.rerun()

            total_stake += bet["stake"]; total_potential_return += bet["return_czk"]
            outcomes = np.random.choice([bet['stake'] * (bet['odds'] - 1), -bet['stake']], size=n_sim, p=[bet['prob'], 1-bet['prob']])
            sim_results += outcomes

        st.divider()
        total_profit = total_potential_return - total_stake
        profit_pct = (total_profit / total_stake * 100) if total_stake > 0 else 0

        col_s, col_r = st.columns(2)
        with col_s: st.metric("💸 Celkový vklad", f"{total_stake} Kč")
        with col_r: st.metric("💰 Potenciální výnos", f"{int(total_potential_return)} Kč", delta=f"+{int(total_profit)} Kč ({profit_pct:.1f}%)" if total_profit > 0 else f"{int(total_profit)} Kč")

        prob_in_plus = np.sum(sim_results > 0) / n_sim
        st.metric("Šance na PLUS ze série sázek", f"{prob_in_plus*100:.1f}%")

        avg_ev = np.mean([bet["ev"] for bet in st.session_state.ticket]) * 100
        if avg_ev > 5: st.success(f"📈 Průměrné EV tiketu: +{avg_ev:.1f}%")
        elif avg_ev > 0: st.warning(f"⚠️ Průměrné EV tiketu: +{avg_ev:.1f}%")
        else: st.error(f"❌ Průměrné EV tiketu: {avg_ev:.1f}%")

        if st.button("🗑️ Vymazat celý tiket", use_container_width=True):
            st.session_state.ticket = []; st.rerun()

# --- VSTUPY A MATEMATIKA ---
def match_history_input(team_label):
    data = {"gf": [], "ga": [], "xg": [], "xga": []}
    weights = [0.35, 0.25, 0.20, 0.13, 0.07]
    for i in range(5):
        label = "Nejnovější zápas" if i == 0 else f"Zápas před {i+1} koly"
        st.markdown(f"**{label}**")
        
        c1, c2 = st.columns(2)
        with c1: gf = st.number_input("Góly", min_value=0, value=1, step=1, key=f"{team_label}_gf_{i}")
        with c2: ga = st.number_input("Góly proti", min_value=0, value=1, step=1, key=f"{team_label}_ga_{i}")
            
        c3, c4 = st.columns(2)
        with c3: xg = smart_float_input("xG", 1.2, key=f"{team_label}_xg_{i}")
        with c4: xga = smart_float_input("xG proti", 1.0, key=f"{team_label}_xga_{i}")
        
        data["gf"].append(gf); data["ga"].append(ga); data["xg"].append(xg); data["xga"].append(xga)
        if i < 4: st.divider()
    return {key: sum(val * w for val, w in zip(data[key], weights)) for key in data}

def get_ai_commentary(p_home, p_draw, p_away, p_over, wc_mode, playoff_mode):
    t1 = "Tým A" if wc_mode else "Domácí"
    t2 = "Tým B" if wc_mode else "Hosté"
    comments = []
    if p_home > 0.70: comments.append(f"🔥 {t1} je tady naprosto jasný favorit. Papírově by to měli přejet rozdílem třídy.")
    elif p_home > 0.55: comments.append(f"🏠 {t1} má kvalitu na své straně.")
    elif p_home > 0.45: comments.append(f"🏟️ {t1} má mírnou výhodu.")
    elif p_away > 0.70: comments.append(f"🔥 {t2} je absolutní favorit.")
    elif p_away > 0.55: comments.append(f"🚀 {t2} má vyšší kvalitu.")
    elif p_away > 0.45: comments.append(f"🚌 {t2} je lehkým favoritem.")
    elif p_draw > 0.33: 
        if playoff_mode: comments.append("🤝 Tady to smrdí prodloužením.")
        else: comments.append("🤝 Remíza visí ve vzduchu.")
    else: comments.append("⚖️ Vyrovnaný zápas.")
    return " ".join(comments)

c_h, c_a = st.columns(2)
rank_h = 15; rank_a = 45

with c_h:
    with st.expander(f"🏠 HISTORIE: {label_h.upper()}", expanded=True):
        if wc_mode: 
            rank_h = st.number_input(f"FIFA Žebříček ({label_h})", min_value=1, value=15, step=1)
            st.divider()
        home_data = match_history_input(label_h)
with c_a:
    with st.expander(f"🚀 HISTORIE: {label_a.upper()}", expanded=True):
        if wc_mode: 
            rank_a = st.number_input(f"FIFA Žebříček ({label_a})", min_value=1, value=45, step=1)
            st.divider()
        away_data = match_history_input(label_a)

if st.button("MAGICKÝ VÝPOČET VALUE & KELLY", type="primary", use_container_width=True):
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
    p_o25 = get_over(2.5)

    most_likely = np.unravel_index(np.argmax(prob_matrix), prob_matrix.shape)
    
    st.divider()
    st.info(get_ai_commentary(p_home, p_draw, p_away, p_o25, wc_mode, playoff_mode))
    st.markdown(f"<h2 style='text-align: center;'>🎯 Smart Tipovačka: {most_likely[0]} : {most_likely[1]}</h2>", unsafe_allow_html=True)
    st.divider()

    def add_to_ticket(label, prob, odds, stake, ev):
        if label in [b["label"] for b in st.session_state.ticket]: return False
        st.session_state.ticket.append({"label": label, "prob": prob, "odds": odds, "stake": int(stake), "return_czk": int(stake * odds), "profit_czk": int(stake * (odds - 1)), "ev": ev})
        return True

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
                btn_label = "✅" if already else "➕"
                if st.button(btn_label, key=f"add_{label}", disabled=already):
                    if add_to_ticket(label, prob, odds, stake, ev): st.rerun()

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
            display_market("Over 1.5", get_over(1.5)); display_market("Over 2.5", p_o25); display_market("Over 3.5", get_over(3.5))
        with c_2:
            st.subheader("Under (Méně než)")
            display_market("Under 1.5", 1-get_over(1.5)); display_market("Under 2.5", 1-p_o25); display_market("Under 3.5", 1-get_over(3.5))
    with tab3:
        c_1, c_2 = st.columns(2)
        with c_1:
            st.subheader(f"{label_h} Góly")
            display_market(f"{label_h} Over 0.5", p_h_o05); display_market(f"{label_h} Under 0.5", p_h_u05); st.divider()
            display_market(f"{label_h} Over 1.5", p_h_o15); display_market(f"{label_h} Under 1.5", p_h_u15)
        with c_2:
            st.subheader(f"{label_a} Góly")
            display_market(f"{label_a} Over 0.5", p_a_o05); display_market(f"{label_a} Under 0.5", p_a_u05); st.divider()
            display_market(f"{label_a} Over 1.5", p_a_o15); display_market(f"{label_a} Under 1.5", p_a_u15)
