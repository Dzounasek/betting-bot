import streamlit as st
import scipy.stats as stats

st.set_page_config(page_title="Value Bot", layout="centered")
st.title("⚽ Výpočet férových kurzů")
st.markdown("Zadej průměrné xG z posledních 5 zápasů. Model použije Poissonovo rozdělení pro výpočet reálné pravděpodobnosti.")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Domácí tým")
    xg_home_for = st.number_input("Průměr xG (útok domácích):", min_value=0.0, value=1.5, step=0.1)
    xg_home_against = st.number_input("Průměr xGA (obrana domácích):", min_value=0.0, value=1.0, step=0.1)

with col2:
    st.subheader("Hostující tým")
    xg_away_for = st.number_input("Průměr xG (útok hostů):", min_value=0.0, value=1.2, step=0.1)
    xg_away_against = st.number_input("Průměr xGA (obrana hostů):", min_value=0.0, value=1.3, step=0.1)

if st.button("Vypočítat kurzy", type="primary"):
    # Sloučení ofenzivní a defenzivní síly obou týmů
    exp_goals_home = (xg_home_for + xg_away_against) / 2
    exp_goals_away = (xg_away_for + xg_home_against) / 2

    prob_home = 0
    prob_draw = 0
    prob_away = 0

    # Výpočet přesných výsledků 0:0 až 5:5
    for i in range(6): 
        for j in range(6): 
            prob = stats.poisson.pmf(i, exp_goals_home) * stats.poisson.pmf(j, exp_goals_away)
            if i > j:
                prob_home += prob
            elif i == j:
                prob_draw += prob
            else:
                prob_away += prob

    # Normalizace na 100 %
    total_prob = prob_home + prob_draw + prob_away
    prob_home /= total_prob
    prob_draw /= total_prob
    prob_away /= total_prob

    odds_home = 1 / prob_home if prob_home > 0 else 0
    odds_draw = 1 / prob_draw if prob_draw > 0 else 0
    odds_away = 1 / prob_away if prob_away > 0 else 0

    st.success("✅ Výpočet byl úspěšně proveden!")
    st.markdown("### Férové kurzy (bez marže sázkovky):")
    st.info(f"**1 (Domácí):** {odds_home:.2f}  |  Šance: {prob_home*100:.1f} %")
    st.info(f"**X (Remíza):** {odds_draw:.2f}  |  Šance: {prob_draw*100:.1f} %")
    st.info(f"**2 (Hosté):** {odds_away:.2f}  |  Šance: {prob_away*100:.1f} %")
