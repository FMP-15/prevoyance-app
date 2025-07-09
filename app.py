import streamlit as st
import plotly.graph_objects as go

# --- PAGE SETUP ---
st.set_page_config(page_title="Calculateur de Prévoyance", layout="centered")
st.title("🧮 Calculateur de prévoyance suisse")
st.write("Ce simulateur estime les prestations en cas d'invalidité, décès ou retraite.")

# --- INPUTS ---
st.header("1️⃣ Informations personnelles")
salaire = st.number_input("Salaire annuel brut (CHF)", min_value=0, value=100000, step=1000)
capital_lpp = st.number_input("Capital vieillesse LPP (CHF)", min_value=0, value=200000, step=1000)
certificat_lpp = st.checkbox("Je possède un certificat LPP avec les montants exacts")

situation = st.selectbox("Situation familiale", ["Célibataire", "Marié(e)", "Concubin(e)"])
enfants = st.number_input("Nombre d'enfants à charge", min_value=0, value=1, step=1)
cas = st.selectbox("Cas à simuler", ["Invalidité - Maladie", "Invalidité - Accident", "Décès - Maladie", "Décès - Accident", "Vieillesse"])
besoin_percent = st.slider("Quel pourcentage du revenu souhaitez-vous maintenir ?", 50, 100, 90)
besoin_client = salaire * besoin_percent / 100

# --- CALCUL DES PRESTATIONS SELON LE CAS ---
def calcul_prestations():
    rente_ai = 0
    rente_lpp = 0
    rente_avs = 0
    rente_veuve = 0
    rente_enfant = 0

    if cas.startswith("Invalidité"):
        rente_ai = salaire * 0.6  # AI échelle 44
        if certificat_lpp:
            rente_lpp = st.number_input("Montant annuel de rente LPP (CHF)", value=12000)
        else:
            rente_lpp = capital_lpp * 0.06
        rente_enfant = enfants * (rente_ai * 0.4)

    elif cas == "Décès - Maladie":
        if certificat_lpp:
            rente_veuve = st.number_input("Rente de veuve LPP (CHF)", value=12000)
            rente_enfant = enfants * (st.number_input("Rente orphelin LPP (CHF)", value=4000))
        else:
            rente_lpp = capital_lpp * 0.06
            rente_veuve = rente_lpp * 0.6
            rente_enfant = enfants * (rente_lpp * 0.2)
        rente_avs = salaire * 0.8  # approximation pleine rente veuve AVS
        rente_enfant += enfants * (rente_avs * 0.4)

    elif cas == "Décès - Accident":
        salaire_assure = min(salaire, 148200)
        rente_veuve = salaire_assure * 0.4
        rente_enfant = enfants * (salaire_assure * 0.15)
        rente_avs = salaire * 0.8  # approximation
        rente_enfant += enfants * (rente_avs * 0.4)
        if not certificat_lpp:
            rente_lpp = capital_lpp * 0.06

    elif cas == "Vieillesse":
        if certificat_lpp:
            rente_lpp = st.number_input("Rente annuelle LPP totale (CHF)", value=24000)
        else:
            rente_lpp = capital_lpp * 0.06
        rente_avs = 43020 if situation == "Marié(e)" else 28680  # AVS maximale annuelle

    total = rente_ai + rente_lpp + rente_avs + rente_veuve + rente_enfant
    return total, rente_ai, rente_lpp, rente_avs, rente_veuve, rente_enfant

# --- CALCUL ---
total_prestations, rente_ai, rente_lpp, rente_avs, rente_veuve, rente_enfant = calcul_prestations()
lacune = max(0, besoin_client - total_prestations)

# --- AFFICHAGE DES RÉSULTATS ---
st.header("2️⃣ Résultat de la simulation")
st.metric("Besoin du client", f"CHF {besoin_client:,.0f}")
st.metric("Prestations estimées", f"CHF {total_prestations:,.0f}")
st.metric("Lacune de couverture", f"CHF {lacune:,.0f}", delta_color="inverse")

# --- GRAPHIQUE ---
st.header("3️⃣ Visualisation graphique")
fig = go.Figure(data=[
    go.Bar(name='Besoin', x=['Simulation'], y=[besoin_client]),
    go.Bar(name='Prestations', x=['Simulation'], y=[total_prestations]),
    go.Bar(name='Lacune', x=['Simulation'], y=[lacune])
])
fig.update_layout(barmode='group', title='Comparaison besoin vs prestations')
st.plotly_chart(fig)

# --- DÉTAIL DES COMPOSANTES ---
st.subheader("📊 Détail des prestations")
st.write(f"**Rente AI :** CHF {rente_ai:,.0f}")
st.write(f"**Rente LPP :** CHF {rente_lpp:,.0f}")
st.write(f"**Rente AVS :** CHF {rente_avs:,.0f}")
st.write(f"**Rente de veuve :** CHF {rente_veuve:,.0f}")
st.write(f"**Rente enfant :** CHF {rente_enfant:,.0f}")

# --- NOTE ---
st.info("⚠️ Ce calculateur applique les barèmes RAMD, LPP, AVS, LAA de manière simplifiée. Pour une planification complète, veuillez consulter un conseiller en prévoyance.")
