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

# --- FONCTIONS AUXILIAIRES ---
def calcul_rente_ai_pilier1(salaire):
    if salaire <= 14100:
        return 0
    elif salaire <= 28200:
        return 14100
    elif salaire <= 84600:
        return salaire * 0.35  # approximation
    else:
        return 29400  # rente AI max échelle 44

def rente_avs_standard():
    return 30240  # rente AVS individuelle maximale mise à jour 2025  # rente AVS individuelle maximale

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
        rente_avs = 0  # pas versée directement au conjoint mais base pour calcul

        rente_enfant = enfants * (rente_avs_deces * 0.4)
        if situation == "Marié(e)":
            rente_veuve = rente_avs_deces * 0.8  # si conditions remplies (avec enfant ou +45 ans)

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

# --- GRAPHIQUE ---
st.header("3️⃣ Visualisation graphique")

fig = go.Figure()

if cas == "Invalidité - Maladie":
    fig.add_trace(go.Bar(name='AI (1er pilier)', x=['Invalidité - Maladie'], y=[rente_ai_p1]))
    fig.add_trace(go.Bar(name='LPP (2e pilier)', x=['Invalidité - Maladie'], y=[rente_lpp]))
    fig.add_trace(go.Bar(name='Enfants (AI)', x=['Invalidité - Maladie'], y=[rente_enfant]))

elif cas == "Invalidité - Accident":
    fig.add_trace(go.Bar(name='AI (1er pilier)', x=['Invalidité - Accident'], y=[rente_ai_p1]))
    fig.add_trace(go.Bar(name='LPP (2e pilier)', x=['Invalidité - Accident'], y=[rente_lpp]))
    fig.add_trace(go.Bar(name='LAA (enfants)', x=['Invalidité - Accident'], y=[rente_enfant]))

elif cas == "Décès - Maladie":
    fig.add_trace(go.Bar(name='Rente de veuve (AVS + LPP)', x=['Décès - Maladie'], y=[rente_veuve]))
    fig.add_trace(go.Bar(name='Rente enfants (AVS + LPP)', x=['Décès - Maladie'], y=[rente_enfant]))

elif cas == "Décès - Accident":
    fig.add_trace(go.Bar(name='Rente de veuve (LAA + AVS + LPP)', x=['Décès - Accident'], y=[rente_veuve]))
    fig.add_trace(go.Bar(name='Rente enfants (LAA + AVS + LPP)', x=['Décès - Accident'], y=[rente_enfant]))

elif cas == "Vieillesse":
    fig.add_trace(go.Bar(name='AVS', x=['Vieillesse'], y=[rente_avs]))
    fig.add_trace(go.Bar(name='LPP', x=['Vieillesse'], y=[rente_lpp]))

fig.add_trace(go.Bar(name='Lacune', x=[cas], y=[lacune]))
fig.add_trace(go.Bar(name='Besoin total', x=[cas], y=[besoin_client]))

fig.update_layout(
    barmode='stack',
    title='Répartition des prestations selon le cas',
    yaxis_title='Montants annuels (CHF)',
    legend_title='Sources de prestations',
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
st.info("⚠️ Ce calculateur applique les barèmes RAMD, LPP, AVS, LAA de manière simplifiée. Pour une planification complète, veuillez consulter un conseiller en prévoyance.")
