import streamlit as st
import plotly.graph_objects as go
from datetime import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Calculateur de Prévoyance", layout="centered")
st.title("📊 Calculateur de prévoyance suisse")
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

# Calcul des années jusqu'à la retraite
age_retraite = 65
annee_courante = datetime.now().year
age_actuel = st.slider("Votre âge actuel", min_value=18, max_value=64, value=40)
nb_annees_restantes = age_retraite - age_actuel
liste_annees = list(range(annee_courante, annee_courante + nb_annees_restantes))

# --- FONCTIONS AUXILIAIRES ---
def calcul_rente_ai_pilier1(salaire):
    if salaire <= 14100:
        return 0
    elif salaire <= 28200:
        return 14100
    elif salaire <= 84600:
        return salaire * 0.35
    else:
        return 29400

def rente_avs_standard():
    return 30240

# --- CALCUL DES PRESTATIONS SELON LE CAS ---
def calcul_prestations():
    rente_ai_p1 = 0
    rente_lpp = 0
    rente_avs = 0
    rente_veuve = 0
    rente_enfant = 0

    if cas.startswith("Invalidité"):
        rente_ai_p1 = calcul_rente_ai_pilier1(salaire)
        if certificat_lpp:
            rente_lpp = st.number_input("Montant annuel de rente LPP (CHF)", value=12000)
        else:
            rente_lpp = capital_lpp * 0.06
        rente_enfant = enfants * (rente_ai_p1 * 0.4)

    elif cas == "Décès - Maladie":
        rente_avs_deces = rente_avs_standard()
        rente_avs = 0
        rente_enfant = enfants * (rente_avs_deces * 0.4)
        if situation == "Marié(e)":
            rente_veuve = rente_avs_deces * 0.8

        if certificat_lpp:
            rente_veuve += st.number_input("Rente de veuve LPP (CHF)", value=12000)
            rente_enfant += enfants * (st.number_input("Rente orphelin LPP (CHF)", value=4000))
        else:
            rente_lpp = capital_lpp * 0.06
            rente_veuve += rente_lpp * 0.6
            rente_enfant += enfants * (rente_lpp * 0.2)

    elif cas == "Décès - Accident":
        rente_avs_deces = rente_avs_standard()
        salaire_assure = min(salaire, 148200)
        rente_enfant = enfants * (salaire_assure * 0.15 + rente_avs_deces * 0.4)
        if situation == "Marié(e)":
            rente_veuve = salaire_assure * 0.4 + rente_avs_deces * 0.8

        if not certificat_lpp:
            rente_lpp = capital_lpp * 0.06
        else:
            rente_veuve += st.number_input("Rente de veuve LPP (CHF)", value=12000)
            rente_enfant += enfants * (st.number_input("Rente orphelin LPP (CHF)", value=4000))

    elif cas == "Vieillesse":
        if certificat_lpp:
            rente_lpp = st.number_input("Rente annuelle LPP totale (CHF)", value=24000)
        else:
            rente_lpp = capital_lpp * 0.06
        rente_avs = 45360 if situation == "Marié(e)" else 30240

    total = rente_ai_p1 + rente_lpp + rente_avs + rente_veuve + rente_enfant
    return total, rente_ai_p1, rente_lpp, rente_avs, rente_veuve, rente_enfant

# --- CALCUL ---
total_prestations, rente_ai_p1, rente_lpp, rente_avs, rente_veuve, rente_enfant = calcul_prestations()
lacune = max(0, besoin_client - total_prestations)

# --- AFFICHAGE DES RÉSULTATS ---
st.header("2️⃣ Résultat de la simulation")
st.metric("Besoin du client", f"CHF {besoin_client:,.0f}")
st.metric("Prestations estimées", f"CHF {total_prestations:,.0f}")
st.metric("Lacune de couverture", f"CHF {lacune:,.0f}", delta_color="inverse")

# --- NOUVEAU GRAPHIQUE ANNUEL ---
st.header("3️⃣ Visualisation graphique annuelle jusqu'à la retraite")

y_ai = [rente_ai_p1] * nb_annees_restantes
y_lpp = [rente_lpp] * nb_annees_restantes
y_enfant = [rente_enfant] * nb_annees_restantes
y_lacune = [max(0, besoin_client - (rente_ai_p1 + rente_lpp + rente_enfant))] * nb_annees_restantes
y_total = [besoin_client] * nb_annees_restantes

fig = go.Figure()
fig.add_trace(go.Bar(name="AI (1er pilier)", x=liste_annees, y=y_ai))
fig.add_trace(go.Bar(name="LPP (2e pilier)", x=liste_annees, y=y_lpp))
fig.add_trace(go.Bar(name="Rente enfant (AI + LPP)", x=liste_annees, y=y_enfant))
fig.add_trace(go.Bar(name="Lacune", x=liste_annees, y=y_lacune))
fig.add_trace(go.Scatter(name="Besoin annuel", x=liste_annees, y=y_total, mode="lines", line=dict(color="black", dash="dash")))

fig.update_layout(
    barmode='stack',
    title="Projection annuelle des rentes jusqu'à la retraite",
    xaxis_title="Années",
    yaxis_title="Montants annuels (CHF)",
    legend_title="Sources de prestations"
)

st.plotly_chart(fig, use_container_width=True)

# --- DÉTAIL DES COMPOSANTES ---
st.subheader("📊 Détail des prestations")
st.write(f"**Rente AI (1er pilier, échelle 44) :** CHF {rente_ai_p1:,.0f}")
st.write(f"**Rente LPP (2e pilier) :** CHF {rente_lpp:,.0f}")
st.write(f"**Rente AVS (vieillesse ou base décès) :** CHF {rente_avs:,.0f}")
st.write(f"**Rente de veuve (AVS + LPP) :** CHF {rente_veuve:,.0f}")
st.write(f"**Rente enfant (AVS + LPP) :** CHF {rente_enfant:,.0f}")

# --- NOTE ---
st.info("\u26a0\ufe0f Ce calculateur applique les barèmes RAMD, LPP, AVS, LAA de manière simplifiée. Pour une planification complète, veuillez consulter un conseiller en prévoyance.")
