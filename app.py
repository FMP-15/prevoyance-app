import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, date

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
nb_enfants = st.number_input("Nombre d'enfants à charge", min_value=0, value=1, step=1)

# Liste des dates de naissance des enfants
date_naissances = []
for i in range(int(nb_enfants)):
    date_naissances.append(st.date_input(f"Date de naissance de l'enfant {i+1}", value=date(2010, 1, 1), key=f"dob_{i}"))

enfants_en_formation = st.checkbox("Les enfants sont en formation (rente jusqu'à 25 ans)")

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

    if cas.startswith("Invalidité"):
        rente_ai_p1 = calcul_rente_ai_pilier1(salaire)
        if certificat_lpp:
            rente_lpp = st.number_input("Montant annuel de rente LPP (CHF)", value=12000)
        else:
            rente_lpp = capital_lpp * 0.06

    elif cas == "Décès - Maladie":
        rente_avs_deces = rente_avs_standard()
        rente_avs = 0
        if situation == "Marié(e)":
            rente_veuve = rente_avs_deces * 0.8

        if certificat_lpp:
            rente_veuve += st.number_input("Rente de veuve LPP (CHF)", value=12000)
        else:
            rente_lpp = capital_lpp * 0.06
            rente_veuve += rente_lpp * 0.6

    elif cas == "Décès - Accident":
        rente_avs_deces = rente_avs_standard()
        salaire_assure = min(salaire, 148200)
        if situation == "Marié(e)":
            rente_veuve = salaire_assure * 0.4 + rente_avs_deces * 0.8

        if not certificat_lpp:
            rente_lpp = capital_lpp * 0.06
        else:
            rente_veuve += st.number_input("Rente de veuve LPP (CHF)", value=12000)

    elif cas == "Vieillesse":
        if certificat_lpp:
            rente_lpp = st.number_input("Rente annuelle LPP totale (CHF)", value=24000)
        else:
            rente_lpp = capital_lpp * 0.06
        rente_avs = 45360 if situation == "Marié(e)" else 30240

    total = rente_ai_p1 + rente_lpp + rente_avs + rente_veuve
    return total, rente_ai_p1, rente_lpp, rente_avs, rente_veuve

# --- CALCUL ---
total_prestations, rente_ai_p1, rente_lpp, rente_avs, rente_veuve = calcul_prestations()

# Calcul des rentes enfants par an
today = date.today()
annee_fin_rente_enfant = []
for naissance in date_naissances:
    age = annee_courante - naissance.year
    fin_age = 25 if enfants_en_formation else 18
    annee_fin = naissance.year + fin_age
    if annee_fin > annee_courante:
        annee_fin_rente_enfant.append(annee_fin)

rente_par_enfant = calcul_rente_ai_pilier1(salaire) * 0.4 if cas.startswith("Invalidité") else 10000

y_rente_enfant = []
for annee in liste_annees:
    total_enfants_ayants_droit = sum(1 for fin in annee_fin_rente_enfant if annee <= fin)
    y_rente_enfant.append(total_enfants_ayants_droit * rente_par_enfant)

lacune = [max(0, besoin_client - (rente_ai_p1 + rente_lpp + rente_avs + rente_veuve + rente_enfant)) for rente_enfant in y_rente_enfant]

# --- AFFICHAGE DES RÉSULTATS ---
st.header("2️⃣ Résultat de la simulation")
st.metric("Besoin du client", f"CHF {besoin_client:,.0f}")
st.metric("Prestations estimées", f"CHF {total_prestations:,.0f}")

# --- VISUALISATION EN BLOCS PAR ANNÉE ---
st.header("3️⃣ Visualisation annuelle des prestations")

fig = go.Figure()
fig.add_trace(go.Bar(name="Rente AI (1er pilier)", x=liste_annees, y=[rente_ai_p1] * nb_annees_restantes))
fig.add_trace(go.Bar(name="Rente AVS", x=liste_annees, y=[rente_avs] * nb_annees_restantes))
fig.add_trace(go.Bar(name="Rente LPP (2e pilier)", x=liste_annees, y=[rente_lpp] * nb_annees_restantes))
fig.add_trace(go.Bar(name="Rente veuve", x=liste_annees, y=[rente_veuve] * nb_annees_restantes))
fig.add_trace(go.Bar(name="Rente enfant (AI/AVS/LPP)", x=liste_annees, y=y_rente_enfant))
fig.add_trace(go.Bar(name="Lacune", x=liste_annees, y=lacune))
fig.add_trace(go.Scatter(name="Besoin annuel", x=liste_annees, y=[besoin_client] * nb_annees_restantes, mode="lines", line=dict(color="black", dash="dash")))

fig.update_layout(
    barmode='stack',
    title="Projection annuelle des rentes jusqu'à la retraite",
    xaxis_title="Années",
    yaxis_title="Montants annuels (CHF)",
    legend_title="Sources de prestations"
)

st.plotly_chart(fig, use_container_width=True)

# --- DÉTAIL ---
st.subheader("📊 Détail des prestations")
st.write(f"**Rente AI (1er pilier, échelle 44) :** CHF {rente_ai_p1:,.0f}")
st.write(f"**Rente LPP (2e pilier) :** CHF {rente_lpp:,.0f}")
st.write(f"**Rente AVS :** CHF {rente_avs:,.0f}")
st.write(f"**Rente de veuve :** CHF {rente_veuve:,.0f}")

# --- NOTE ---
st.info("\u26a0\ufe0f Ce calculateur applique les barèmes RAMD, LPP, AVS, LAA de manière simplifiée. Pour une planification complète, veuillez consulter un conseiller en prévoyance.")
