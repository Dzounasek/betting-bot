import streamlit as st
import scipy.stats as stats
import pandas as pd
import numpy as np

st.set_page_config(page_title="Value Bot v3.0", layout="wide")

st.title("⚽ Betting Bot v3.0")
st.markdown("Zadej historii posledních 5 zápasů pro oba týmy. Model vypočítá pravděpodobnosti pro 10+ sázkových trhů.")

# Pomocná funkce pro vytvoření formuláře historie (optimalizováno pro mobil)
def match_history_input(team_label):
    st.subheader(f"Historie: {team_label}")
    
    data = {"gf": [], "ga": [], "xg": [], "xga": [], "poss": []}
    
    for i in range(5):
        st.markdown(f"**Zápas {i+1}**")
        
        # 1. Řádek: Výsledek (Góly)
        c1, c2 = st.columns(2)
        with c1:
            gf = st.number_input("Góly", min_value=0, value=1, step=1, key=f"{team_label}_gf_{i}")
        with c2:
            ga = st.number_input("Góly proti", min_value=0, value=1, step=1, key=f"{team_label}_ga_{i}")
            
        # 2. Řádek: xG
        c3, c4 = st.columns(2)
        with c3:
            xg = st.number_input("xG", min_value=0.0, value=1.2, step=0.1, format="%.2f", key=f"{team_label}_xg_{i}")
        with c4:
            xga = st.number_input("xG proti", min_value=0.0, value=1.0, step=0.1, format="%.2f", key=f"{team_label}_xga_{i}")
            
        # 3. Řádek: Držení míče
        c5, c6 = st.columns(2)
        with c5:
            poss = st.number_input("Držení %", min_value=0, max_value=100, value=50, step=1, key=f"{team_label}_poss_{i}")
            
        # Uložení hodnot
        data["gf"].append(gf)
        data["ga"].append(ga)
        data["xg"].append(xg)
        data["xga"].append(xga)
        data["poss"].append(poss)
        
        # Oddělovač mezi zápasy (kromě posledního)
        if i < 4:
            st.divider()
            
    # Výpočet průměrů z listů
    avg_stats = {
        "gf": sum(data["gf"]) / 5,
        "ga": sum(data["ga"]) / 5,
        "xg": sum(data["xg"]) / 5,
        "xga": sum(data["xga"]) / 5,
        "poss": sum(data["poss"]) / 5
    }
    return avg_stats

col1, col2 = st.columns(2)

with col1:
    with st.expander("🏠 HISTORIE DOMÁCÍCH", expanded=True):
        home_data = match_history_input("Domácí")

with col2:
    with st.expander("🚀 HISTORIE HOSTŮ", expanded=True):
        away_data = match_history_input("Hosté")

if st.button("VYPOČÍTAT VŠECHNY TRHY", type="primary", use_container_width=True):
    # Vážený průměr (70% xG, 30% skutečné góly) pro stanovení Lambdy
    home_lambda = ((home_data["xg"] * 0.7 + home_data["gf"] * 0.3) + (away_data["xga"] * 0.7 + away_data["ga"] * 0.3)) / 2
    away_lambda = ((away_data["xg"] * 0.7 + away_data["gf"] * 0.3) + (home_data["xga"] * 0.7 + home_data["ga"] * 0.3)) / 2

    # Matice pravděpodobností (0-7 gólů)
    max_g = 8
    prob_matrix = np.zeros((max_g, max_g))
    for i in range(max_g):
        for j in range(max_g):
            prob_matrix[i, j] = stats.poisson.pmf(i, home_lambda) * stats.poisson.pmf(j, away_lambda)

    # Nalezení nejpravděpodobnějšího přesného výsledku
    most_likely_idx = np.unravel_index(np.argmax(prob_matrix, axis=None), prob_matrix.shape)
    pred_home_goals, pred_away_goals = most_likely_idx
    highest_prob = prob_matrix[pred_home_goals, pred_away_goals]

    # 1. 1X2 Pravděpodobnosti
    p_home = np.sum(np.tril(prob_matrix, -1))
    p_draw = np.sum(np.diag(prob_matrix))
    p_away = np.sum(np.triu(prob_matrix, 1))
    
    # Normalizace
    total = p_home + p_draw + p_away
    p_home /= total; p_draw /= total; p_away /= total

    # 2. Ostatní trhy
    p_1x = p_home + p_draw
    p_x2 = p_draw + p_away
    p_12 = p_home + p_away
    
    p_dnb1 = p_home / (p_home + p_away) if (p_home + p_away) > 0 else 0
    p_dnb2 = p_away / (p_home + p_away) if (p_home + p_away) > 0 else 0
    
    p_btts_yes = np.sum(prob_matrix[1:, 1:])
    p_btts_no = 1 - p_btts_yes
    
    p_over25 = np.sum([prob_matrix[i, j] for i in range(max_g) for j in range(max_g) if i+j > 2.5])
    p_under25 = 1 - p_over25
    
    p_over15 = np.sum([prob_matrix[i, j] for i in range(max_g) for j in range(max_g) if i+j > 1.5])

    # ZOBRAZENÍ VÝSLEDKŮ
    st.divider()
    
    # Zobrazení hlavní predikce
    st.markdown(f"<h3 style='text-align: center;'>🔮 Nejpravděpodobnější výsledek: {pred_home_goals} : {pred_away_goals}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>Pravděpodobnost tohoto skóre: {highest_prob*100:.1f}%</p>", unsafe_allow_html=True)
    st.divider()

    res_col1, res_col2, res_col3 = st.columns(3)

    with res_col1:
        st.subheader("🏆 Hlavní Trhy (1X2)")
        st.metric("1 (Domácí)", f"{1/p_home:.2f}", f"{p_home*100:.1f}%")
        st.metric("X (Remíza)", f"{1/p_draw:.2f}", f"{p_draw*100:.1f}%")
        st.metric("2 (Hosté)", f"{1/p_away:.2f}", f"{p_away*100:.1f}%")

    with res_col2:
        st.subheader("🛡️ Dvojitá šance & DNB")
        st.write(f"**1X:** {1/p_1x:.2f} ({p_1x*100:.1f}%)")
        st.write(f"**X2:** {1/p_x2:.2f} ({p_x2*100:.1f}%)")
        st.write(f"**12:** {1/p_12:.2f} ({p_12*100:.1f}%)")
        st.divider()
        st.write(f"**DNB 1:** {1/p_dnb1:.2f} ({p_dnb1*100:.1f}%)")
        st.write(f"**DNB 2:** {1/p_dnb2:.2f} ({p_dnb2*100:.1f}%)")

    with res_col3:
        st.subheader("🥅 Góly & BTTS")
        st.write(f"**BTTS Ano:** {1/p_btts_yes:.2f} ({p_btts_yes*100:.1f}%)")
        st.write(f"**BTTS Ne:** {1/p_btts_no:.2f} ({p_btts_no*100:.1f}%)")
        st.divider()
        st.write(f"**Over 2.5:** {1/p_over25:.2f} ({p_over25*100:.1f}%)")
        st.write(f"**Under 2.5:** {1/p_under25:.2f} ({p_under25*100:.1f}%)")
        st.write(f"**Over 1.5:** {1/p_over15:.2f} ({p_over15*100:.1f}%)")
