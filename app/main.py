import sys
import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.ai_engine import EVSalesPredictor, ask_copilot

st.set_page_config(page_title="EV Market Intelligence — Italy & Turin", page_icon="⚡", layout="wide")

DB_PATH = "data/processed/ev_italy.db"


@st.cache_data
def load_tables():
    conn = sqlite3.connect(DB_PATH)
    models = pd.read_sql("SELECT * FROM fact_bev_models", conn)
    powertrain = pd.read_sql("SELECT * FROM fact_powertrain", conn)
    channels = pd.read_sql("SELECT * FROM fact_channels", conn)
    geo = pd.read_sql("SELECT * FROM fact_geo_ev", conn)
    conn.close()
    return models, powertrain, channels, geo


st.sidebar.title("⚡ EV Intelligence 2026")
st.sidebar.markdown("**Focus:** Mercato Italia & Polo Torino")
groq_key = st.sidebar.text_input("Groq API Key (opzionale per LLM live)", type="password", help="Lascia vuoto per usare il motore esperto integrato a costo zero.")
st.sidebar.info("Dati ufficiali UNRAE (Ott 2026) & Motus-E 2026.")

st.title("⚡ EV Market Intelligence & AI Sales Copilot")
st.markdown("Analisi predittiva delle vendite di veicoli elettrici (BEV), gap infrastrutturale e simulatore commerciale per concessionari e flotte (Focus **Torino & Piemonte**).")

if not os.path.exists(DB_PATH):
    st.error("⚠️ Database non trovato! Esegui prima `python src/etl_pipeline.py` nel terminale.")
    st.stop()

df_models, df_powertrain, df_channels, df_geo = load_tables()

col1, col2, col3, col4 = st.columns(4)
col1.metric("BEV Italia (10 Mesi 2026)", "110.379", "+63,3% YoY")
col2.metric("Quota BEV (Ott 2026)", "6,1%", "7,8% sui 10 mesi")
col3.metric("Colonnine Provincia Torino", "4.498", "+52,0% YoY (3ª in Italia)")
col4.metric("1° Modello BEV Italia", "Leapmotor T03", "21,4% market share")

tab1, tab2, tab3 = st.tabs(["📊 Market & Paradosso Torino", "🎛️ Simulatore 'What-If' Dealer", "🤖 AI Sales Copilot (Torino)"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Top 10 Modelli BEV in Italia (Gen–Ott 2026)")
        fig_models = px.bar(
            df_models.head(10).sort_values("imm_10m_2026"),
            x="imm_10m_2026",
            y="modello",
            color="fascia_prezzo",
            orientation="h",
            text="imm_10m_2026",
            labels={"imm_10m_2026": "Immatricolazioni", "modello": "Modello", "fascia_prezzo": "Fascia Prezzo"}
        )
        st.plotly_chart(fig_models, use_container_width=True)

    with c2:
        st.subheader("Il Paradosso Infrastrutturale: Colonnine vs Quota BEV")
        fig_geo = px.scatter(
            df_geo,
            x="colonnine_per_1000_ab",
            y="quota_bev_pct",
            size="imm_bev_10m_2026",
            color="area_geo",
            text="provincia",
            labels={
                "colonnine_per_1000_ab": "Colonnine ogni 1.000 abitanti",
                "quota_bev_pct": "Quota Mercato BEV (%)",
                "area_geo": "Area Geografica"
            }
        )
        fig_geo.update_traces(textposition="top center")
        st.plotly_chart(fig_geo, use_container_width=True)

    st.subheader("Dettaglio Provinciale (Focus Torino vs Top Province)")
    st.dataframe(df_geo, use_container_width=True)

with tab2:
    st.subheader("Simulatore Elasticità al Prezzo & Infrastruttura (Con Guardrail di Margine)")
    predictor = EVSalesPredictor(DB_PATH)

    sc1, sc2 = st.columns([1, 2])
    with sc1:
        prov_sel = st.selectbox("Seleziona Provincia", df_geo["cod_prov"].tolist(), index=0)
        modello_sel = st.selectbox("Modello di riferimento", df_models["modello"].tolist(), index=0)
        prezzo_base = int(df_models[df_models["modello"] == modello_sel]["prezzo_listino"].iloc[0])
        st.caption(f"Prezzo listino base: **€ {prezzo_base:,}**")

        sconto_eur = st.slider("Sconto / Promo Dealer (€)", min_value=0, max_value=4500, value=1000, step=250)
        inc_colonnine = st.slider("Crescita Colonnine Locali (%)", min_value=0, max_value=50, value=10, step=5)

    with sc2:
        res = predictor.simulate_scenario(prov_sel, prezzo_base, sconto_eur, inc_colonnine)
        m1, m2, m3 = st.columns(3)
        m1.metric("Vendite Base (Trimestre)", f"{res['vendite_base_trimestre']} auto")
        m2.metric("Vendite Previste (Trimestre)", f"{res['vendite_previste_trimestre']} auto", f"+{res['auto_aggiuntive']} auto")
        m3.metric("Margine Netto Totale", f"€ {res['margine_totale_trimestre']:,}", f"€ {res['margine_netto_unitario']}/auto")

        if res["alert_margine"]:
            st.error("🚨 ALERT GUARDRAIL: Lo sconto supera il margine lordo medio del concessionario (7,5%). Operazione in perdita!")
        else:
            st.success(f"✅ Scenario sostenibile a {res['provincia']}: sconto del {res['sconto_pct']}% con margine positivo.")

with tab3:
    st.subheader("Assistente Strategico Commerciale (Normative Torino & Dati UNRAE 2026)")
    domanda = st.text_input(
        "Fai una domanda strategica (es. 'Come convinco un cliente a Torino a comprare un'auto elettrica?' oppure 'Quali modelli spingere in stock?')",
        value="Come convinco un cliente a Torino a comprare un'auto elettrica sfruttando le regole locali?"
    )
    if st.button("Chiedi al Copilot IA"):
        with st.spinner("Analisi dati UNRAE e normative Torino in corso..."):
            risposta = ask_copilot(domanda, api_key=groq_key)
            st.markdown(risposta)