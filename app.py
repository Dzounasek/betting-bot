import streamlit as st
import scipy.stats as stats
import pandas as pd
import numpy as np
import random

st.set_page_config(page_title="Value Bot v4.0", layout="wide")

st.title("⚽ Betting Bot v4.0 PRO")
st.markdown("Optimalizováno pro mobil. Model: Weighted Poisson + Dixon-Coles Adjustment.")

# 1. FUNKCE PRO VSTUP DAT (Mobilní layout, bez držení míče)
def match_history_input(team_label):
    st.subheader(f"Historie: {team_label}")
    data = {"gf": [], "ga": [], "xg": [], "xga": []}
    
    # Váhy pro Time Decay (od nejnovějšího po nejstarší)
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
            xg = st.number_input("xG", min_value=0.0, value=1.2, step=0.1, format="%.2f", key=f"{team_label}_xg_{i}")
        with c4:
            xga = st.number_input("xG proti", min_value=0.0, value=1.0, step=0.1, format="%.2f", key=f"{team_label}_xga_{i}")
        
        data["gf"].append(gf)
        data["ga"].append(ga)
        data["xg"].append(xg)
        data["xga"].append(xga)
        
        if i < 4: st.divider()
            
    # Výpočet VÁŽENÉHO průměru (Time Decay)
    avg_stats = {}
    for key in data:
        avg_stats[key] = sum(val * w for val, w in zip(data[key], weights))
        
    return avg_stats

# 2. FUNKCE PRO AI KOMENTÁŘ (Bod 7 - Funny verze)
def get_ai_commentary(p_home, p_draw, p_away, p_over, pred_score):
    comments = []
    
    # Komentář k favoritovi
    if p_home > 0.65: comments.append("🏠 Domácí jsou dneska absolutní páni hřiště. Hosté si nejspíš přijeli jen pro výslužku.")
    elif p_away > 0.65: comments.append("🚀 Hosté jedou jako parní válec. Domácí fanoušci budou v 70. minutě hromadně odcházet na párek.")
    elif p_draw > 0.35: comments.append("🤝 Tady to smrdí remízou na sto honů. Oba týmy se budou bát víc než maturanta u tabule.")
    else: comments.append("⚖️ Bookmaker si rve vlasy, tohle je vyrovnaný jak souboj dvou hlemýžďů.")

    # Komentář ke gólům
    if p_over > 0.70: comments.append("🥅 Očekávám totální ofenzivní orgie. Brankáři tam jsou dneska jen jako kužely.")
    elif p_over < 0.35: comments.append("💤 Připrav si kafe. Tady hrozí taková nuda, že i rozhodčí u toho možná usne.")
    
    # Bonusová hláška k predikci
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

if st.button("MAGICKÝ VÝPOČET VALUE", type="primary", use_container_width=True):
    # Výpočet Lambdy (70% xG, 30% góly)
    home_lambda = ((home_data["xg"] * 0.7 + home_data["gf"] * 0.3) + (away_data["xga"] * 0.7 + away_data["ga"] * 0.3)) / 2
    away_lambda = ((away_data["xg"] * 0.7 + away_data["gf"] * 0.3) + (home_data["xga"] * 0.7 + home_data["ga"] * 0.3)) / 2

    # 3. MATICE + DIXON-COLES ADJUSTMENT
    max_g = 8
    prob_matrix = np.zeros((max_g, max_g))
    # Zjednodušený rho parametr pro úpravu remíz (vylepšuje přesnost u 0:0, 1:1 atd.)
    rho = -0.05 
    
    for i in range(max_g):
        for j in range(max_g):
            p = stats.poisson.pmf(i, home_lambda) * stats.poisson.pmf(j, away_lambda)
            # Aplikace korekce pro nízké výsledky
            if i == 0 and j == 0: p *= (1 - home_lambda * away_lambda * rho)
            elif i == 0 and j == 1: p *= (1 + home_lambda * rho)
            elif i == 1 and j == 0: p *= (1 + away_lambda * rho)
            elif i == 1 and j == 1: p *= (1 - rho)
            prob_matrix[i, j] = max(0, p)

    # Normalizace po úpravě
    prob_matrix /= prob_matrix.sum()

    # Pravděpodobnosti hlavních trhů
    p_home = np.sum(np.tril(prob_matrix, -1))
    p_draw = np.sum(np.diag(prob_matrix))
    p_away = np.sum(np.triu(prob_matrix, 1))
    p_over25 = np.sum([prob_matrix[i, j] for i in range(max_g) for j in range(max_g) if i+j > 2.5])
    p_btts = np.sum(prob_matrix[1:, 1:])

    # Predikované skóre
    most_likely = np.unravel_index(np.argmax(prob_matrix), prob_matrix.shape)
    
    st.divider()
    
    # 4. AI SHRNUTÍ (Bod 7)
    st.info(get_ai_commentary(p_home, p_draw, p_away, p_over25, most_likely))

    st.markdown(f"<h2 style='text-align: center;'>🎯 Predikce: {most_likely[0]} : {most_likely[1]}</h2>", unsafe_allow_html=True)
    st.divider()

    # 5. VÝSLEDKY S VALUE TRACKEREM (Bod 5)
    def display_market(label, prob):
        c_res, c_odds = st.columns([2, 1])
        with c_res:
            st.write(f"**{label}**")
            st.caption(f"Model: {1/prob:.2f} ({prob*100:.1f}%)")
        with c_odds:
            user_odds = st.number_input("Kurz Tipsport", min_value=1.0, value=1.0, step=0.05, key=f"odds_{label}")
            ev = (prob * user_odds) - 1
            if user_odds > 1.0:
                if ev > 0.05: st.success(f"🔥 VALUE +{ev*100:.1f}%")
                elif ev > 0: st.warning(f"✅ OK +{ev*100:.1f}%")
                else: st.error(f"❌ Trash {ev*100:.1f}%")

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
