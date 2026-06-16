import streamlit as st
import scipy.stats as stats
import pandas as pd
import numpy as np
import json
import os

st.set_page_config(page_title="Value Bot v6.0 WC", layout="wide")

# --- AGRESIVNÍ CSS PRO VYNUCENÍ POSUVNÍKU ---
st.markdown("""
    <style>
    /* Natvrdo vynutí scrollování na hlavní stránce */
    html, body, [data-testid="stAppViewContainer"], .main, .stApp {
        overflow-y: scroll !important;
    }
    
    /* Zviditelnění a nastylování posuvníku pro WebKit (Chrome, Safari, Edge) */
    ::-webkit-scrollbar {
        width: 18px !important;
        display: block !important;
        background-color: #0e1117 !important; /* Tmavé pozadí */
    }
    ::-webkit-scrollbar-track {
        background: #161b22 !important; 
    }
    ::-webkit-scrollbar-thumb {
        background-color: #666666 !important; /* Světlejší šedá, ať je hned vidět */
        border-radius: 10px !important;
        border: 3px solid #161b22 !important; /* Aby nebyl úplně nalepený na kraji */
    }
    ::-webkit-scrollbar-thumb:hover {
        background-color: #888888 !important; /* Při najetí myší ještě zesvětlá */
    }
    </style>
""", unsafe_allow_html=True)

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

# Tiket: seznam sázek
if "ticket" not in st.session_state:
    st.session_state.ticket = []

# --- SIDEBAR: MONEY MANAGEMENT & TIKET ---
with st.sidebar:
    st.header("💰 Bankroll Management")
    
    saved_bank = load_bankroll()
    bankroll = st.number_input("Tvůj celkový bankroll (Kč)", min_value=0, value=int(saved_bank), step=500, key="bankroll_input")
    
    if bankroll != saved_bank:
        save_bankroll(bankroll)
        
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

    st.divider()
    st.header("🎟️ Můj Tiket (SOLO)")

    if len(st.session_state.ticket) == 0:
        st.caption("Zatím žádné sázky. Klikni na ➕ u libovolného trhu.")
    else:
        total_stake = 0
        total_potential_return = 0

        for idx, bet in enumerate(st.session_state.ticket):
            with st.container():
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    st.markdown(f"**{bet['label']}**")
                    st.caption(
                        f"Kurz: {bet['odds']:.2f} | Sázka: {bet['stake']} Kč | "
                        f"Návrat: **{bet['return_czk']} Kč** (+{bet['profit_czk']} Kč)"
                    )
                with col_del:
                    if st.button("🗑️", key=f"del_bet_{idx}", help="Odstranit sázku"):
                        st.session_state.ticket.pop(idx)
                        st.rerun()

            total_stake += bet["stake"]
            total_potential_return += bet["return_czk"]

        st.divider()

        total_profit = total_potential_return - total_stake
        profit_pct = (total_profit / total_stake * 100) if total_stake > 0 else 0

        col_s, col_r = st.columns(2)
        with col_s:
            st.metric("💸 Celkový vklad", f"{total_stake} Kč")
        with col_r:
            st.metric(
                "💰 Potenciální výnos",
                f"{int(total_potential_return)} Kč",
                delta=f"+{int(total_profit)} Kč ({profit_pct:.1f}%)" if total_profit > 0 else f"{int(total_profit)} Kč"
            )

        # Riziko: pravděpodobnostní shrnutí (počet sázek, průměrné EV)
        avg_ev = np.mean([bet["ev"] for bet in st.session_state.ticket]) * 100
        if avg_ev > 5:
            st.success(f"📈 Průměrné EV tiketu: +{avg_ev:.1f}% — vypadá to dobře!")
        elif avg_ev > 0:
            st.warning(f"⚠️ Průměrné EV tiketu: +{avg_ev:.1f}% — hraniční value.")
        else:
            st.error(f"❌ Průměrné EV tiketu: {avg_ev:.1f}% — tiket je ve ztrátě!")

        if st.button("🗑️ Vymazat celý tiket", use_container_width=True):
            st.session_state.ticket = []
            st.rerun()

# --- HLAVNÍ STRÁNKA VPRAVO ---
st.title("⚽ Value Bot v6.0 PRO 🏆 World Cup Edition")
st.markdown("Opravený pevný posuvník pro Mac, vylepšená predikce skóre a turnajový mód.")

# --- WORLD CUP NASTAVENÍ ---
st.markdown("### 🌍 Nastavení turnaje")
c_wc1, c_wc2 = st.columns(2)
with c_wc1:
    wc_mode = st.toggle("Aktivovat World Cup Mód (Neutrální půda, FIFA Žebříček)", value=False)
with c_wc2:
    if wc_mode:
        playoff_mode = st.toggle("🏆 Vyřazovací část (Zvyšuje šanci na remízu a Under)", value=False)
    else:
        playoff_mode = False

st.divider()

# --- 3. FUNKCE PRO VSTUP DAT ---
def match_history_input(team_label):
    data = {"gf": [], "ga": [], "xg": [], "xga": []}
    
    weights = [0.35, 0.25, 0.20, 0.13, 0.07]
    
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

# --- 4. AI KOMENTÁŘ (Nové upravené limity pro favority) ---
def get_ai_commentary(p_home, p_draw, p_away, p_over, wc_mode, playoff_mode):
    t1 = "Tým A" if wc_mode else "Domácí"
    t2 = "Tým B" if wc_mode else "Hosté"

    comments = []
    # Změněné limity podle naší dohody (Jasný favorit nad 70%, Favorit nad 55%, Lehký nad 45%)
    if p_home > 0.70: comments.append(f"🔥 {t1} je tady naprosto jasný favorit. Papírově by to měli přejet rozdílem třídy.")
    elif p_home > 0.55: comments.append(f"🏠 {t1} má kvalitu na své straně a měli by to urvat.")
    elif p_home > 0.45: comments.append(f"🏟️ {t1} má mírnou výhodu, ale žádná tutovka to není.")
    elif p_away > 0.70: comments.append(f"🔥 {t2} je absolutní favorit, cokoliv jiného než výhra bude obrovský šok.")
    elif p_away > 0.55: comments.append(f"🚀 {t2} má vyšší kvalitu a měl by zápas ovládnout.")
    elif p_away > 0.45: comments.append(f"🚌 {t2} je lehkým favoritem, ale bude to boj.")
    elif p_draw > 0.33: 
        if playoff_mode: comments.append("🤝 Tady to smrdí prodloužením. Taktická bitva a nikdo neudělá první chybu.")
        else: comments.append("🤝 Tohle smrdí těžkou taktickou bitvou, remíza visí ve vzduchu.")
    else: comments.append("⚖️ Brutálně vyrovnaný zápas. Tady může vyhrát úplně kdokoliv.")

    if p_over > 0.60: comments.append("🥅 Model cítí ofenzivní hody, měly by padat góly.")
    elif p_over < 0.40: 
        if playoff_mode: comments.append("💤 Klasický turnajový beton v play-off. Očekávám hodně málo gólů.")
        else: comments.append("💤 Žádnou divočinu nečekej, spíš underový zápas.")
    return " ".join(comments)

# --- HLAVNÍ FORMULÁŘ ---
c_h, c_a = st.columns(2)
rank_h = 15; rank_a = 45 # Defaultní hodnoty

label_h = "Tým A" if wc_mode else "Domácí"
label_a = "Tým B" if wc_mode else "Hosté"

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

    # Aplikace Elo úpravy, pokud je zapnutý turnajový mód
    if wc_mode:
        rank_diff = rank_a - rank_h # Kladné číslo = Tým A je papírově silnější
        adj_factor_a = max(0.7, min(1.3, 1.0 + (rank_diff * 0.005)))
        adj_factor_b = max(0.7, min(1.3, 1.0 - (rank_diff * 0.005)))
        
        home_lambda *= adj_factor_a
        away_lambda *= adj_factor_b
        
        # Brutálnější Dixon-Coles pro Playoff mód (více remíz a underů)
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

    # ==========================================
    # SMART TIPOVAČKA LOGIKA
    # ==========================================
    best_score = (0, 0)
    best_prob = 0
    
    if p_home > p_draw and p_home > p_away: 
        for i in range(1, max_g):
            for j in range(i):
                if prob_matrix[i, j] > best_prob:
                    best_prob = prob_matrix[i, j]
                    best_score = (i, j)
    elif p_away > p_home and p_away > p_draw: 
        for i in range(max_g):
            for j in range(i + 1, max_g):
                if prob_matrix[i, j] > best_prob:
                    best_prob = prob_matrix[i, j]
                    best_score = (i, j)
    else: 
        for i in range(max_g):
            if prob_matrix[i, i] > best_prob:
                best_prob = prob_matrix[i, i]
                best_score = (i, i)
    
    st.divider()
    st.info(get_ai_commentary(p_home, p_draw, p_away, p_o25, wc_mode, playoff_mode))
    st.markdown(f"<h2 style='text-align: center;'>🎯 Smart Tipovačka: {best_score[0]} : {best_score[1]}</h2>", unsafe_allow_html=True)
    st.caption("*(Model nyní garantuje, že přesný výsledek kopíruje nejpravděpodobnějšího vítěze celého zápasu (1X2), abys nepřicházel o body v soutěžích jako Tipsport Tipovačka.)*")
    st.divider()

    def add_to_ticket(label, prob, user_odds, stake_czk, ev):
        stake_int = max(0, int(stake_czk))
        return_czk = int(stake_int * user_odds)
        profit_czk = return_czk - stake_int

        existing_labels = [b["label"] for b in st.session_state.ticket]
        if label in existing_labels:
            return False, "already_exists"

        st.session_state.ticket.append({
            "label": label,
            "odds": user_odds,
            "stake": stake_int,
            "return_czk": return_czk,
            "profit_czk": profit_czk,
            "ev": ev,
            "prob": prob # Přidáno prob pro simulaci v sidebaru
        })
        return True, "added"

    def display_market(label, prob):
        prob = max(min(prob, 0.999), 0.001)
        c_res, c_odds, c_kelly, c_add = st.columns([2, 1, 2, 0.5])
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
                stake_czk = max(0, int(bankroll * fractional_kelly))
                return_czk = int(stake_czk * user_odds)
                profit_czk = return_czk - stake_czk

                if ev > 0.05:
                    st.success(f"🔥 VALUE +{ev*100:.1f}%")
                    st.write(f"💰 Vsadit: **{stake_czk} Kč** → návrat **{return_czk} Kč** (+{profit_czk} Kč)")
                elif ev > 0:
                    st.warning(f"✅ OK +{ev*100:.1f}%")
                    st.write(f"💰 Vsadit: **{stake_czk} Kč** → návrat **{return_czk} Kč** (+{profit_czk} Kč)")
                else:
                    st.error(f"❌ Trash {ev*100:.1f}%")
                    stake_czk = 0
            else:
                ev = -1.0
                stake_czk = 0
        with c_add:
            st.write("") 
            st.write("")
            if user_odds > 1.0:
                already = label in [b["label"] for b in st.session_state.ticket]
                btn_label = "✅" if already else "➕"
                btn_help = "Už na tiketu" if already else "Přidat na tiket"
                if st.button(btn_label, key=f"add_{label}", help=btn_help, disabled=already):
                    ev_val = (prob * user_odds) - 1
                    kelly_f2 = (prob * user_odds - 1) / (user_odds - 1)
                    stake2 = max(0, int(bankroll * kelly_f2 * kelly_fraction))
                    ok, reason = add_to_ticket(label, prob, user_odds, stake2, ev_val)
                    if ok:
                        st.rerun()
                
    tab1, tab2, tab3 = st.tabs(["🏆 Zápas & Ostatní", "⚽ Góly v Zápase", "🥅 Góly Týmů"])

    # Názvy trhů podle režimu WC
    t1_l1 = f"Výhra {label_h} (1)"; t1_l2 = "Remíza (X)"; t1_l3 = f"Výhra {label_a} (2)"
    t1_1x = f"Neprohra {label_h} (1X)"; t1_x2 = f"Neprohra {label_a} (X2)"
    t1_d1 = f"DNB 1 ({label_h})"; t1_d2 = f"DNB 2 ({label_a})"

    with tab1:
        t1_col1, t1_col2 = st.columns(2)
        with t1_col1:
            st.subheader("1X2 & Dvojitá šance")
            display_market(t1_l1, p_home)
            display_market(t1_l2, p_draw)
            display_market(t1_l3, p_away)
            st.divider()
            display_market(t1_1x, p_1x)
            display_market(t1_x2, p_x2)
            display_market("Kdokoli vyhraje (12)", p_12)
            
        with t1_col2:
            st.subheader("Sázky bez remízy (DNB) & BTTS")
            display_market(t1_d1, p_dnb1)
            display_market(t1_d2, p_dnb2)
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
            st.subheader(f"{label_h} Góly")
            display_market(f"{label_h} Over 0.5", p_h_o05)
            display_market(f"{label_h} Under 0.5", p_h_u05)
            st.divider()
            display_market(f"{label_h} Over 1.5", p_h_o15)
            display_market(f"{label_h} Under 1.5", p_h_u15)
            st.divider()
            display_market(f"{label_h} Over 2.5", p_h_o25)
            display_market(f"{label_h} Under 2.5", p_h_u25)

        with t3_col2:
            st.subheader(f"{label_a} Góly")
            display_market(f"{label_a} Over 0.5", p_a_o05)
            display_market(f"{label_a} Under 0.5", p_a_u05)
            st.divider()
            display_market(f"{label_a} Over 1.5", p_a_o15)
            display_market(f"{label_a} Under 1.5", p_a_u15)
            st.divider()
            display_market(f"{label_a} Over 2.5", p_a_o25)
            display_market(f"{label_a} Under 2.5", p_a_u25)
