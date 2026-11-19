import sqlite3
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

DB_PATH = "data/processed/ev_italy.db"

TORINO_KNOWLEDGE_BASE = """
CONTESTO MERCATO EV ITALIA & TORINO (DATI REALI OTTOBRE 2026 - UNRAE / MOTUS-E):
1. Mercato Nazionale (10 mesi 2026): 110.379 auto elettriche (BEV) immatricolate (quota 7,8% sui 10 mesi, 6,1% ad ottobre 2026).
2. Top Modelli BEV in Italia (10 mesi 2026):
   - 1° Leapmotor T03: 23.640 unità (21,4% del mercato BEV, prezzo listino ~18.900€)
   - 2° Tesla Model Y: 5.757 unità (5,2%, listino ~42.990€)
   - 3° Dacia Spring: 5.692 unità (5,2%, listino ~17.900€)
   - 4° BYD Dolphin Surf: 5.542 unità (5,0%, listino ~22.900€)
   - 5° Tesla Model 3: 5.101 unità (4,6%, listino ~39.990€)
3. Il Paradosso di Torino e del Piemonte:
   - Il Piemonte è la 2ª regione in Italia per infrastrutture di ricarica (9.003 punti) e Torino è la 3ª provincia italiana (4.498 punti di ricarica, +52% anno su anno, pari a 2,04 colonnine ogni 1.000 abitanti).
   - Nonostante l'ottima rete di ricarica (quasi pari a Milano che ha 2,28 colonnine/1.000 ab.), Torino ha una quota BEV più bassa (~6,7% contro il 10,5% di Milano).
4. Normative e Vantaggi Fiscali Reali 2026 a Torino e in Piemonte:
   - BOLLO AUTO PIEMONTE: Esenzione totale A VITA (permanente, non solo 5 anni) per i veicoli 100% elettrici (BEV) residenti in Piemonte. Risparmio medio di 250-400€/anno per sempre.
   - ZTL CENTRALE TORINO: Permesso Blu A gratuito per veicoli elettrici puri (si pagano solo 32€ di imposte di bollo per 2 anni, valido anche per non residenti a Torino).
   - STRISCE BLU TORINO (ATTENZIONE): A differenza di Milano o Roma, a Torino i veicoli elettrici PAGANO la sosta sulle strisce blu (salvo sospensione estiva ad agosto). Un venditore non deve mai promettere strisce blu gratis a Torino!
   - CANALE AZIENDALE / NOLEGGIO: Oltre il 42% del mercato auto passa da persone giuridiche/noleggio; le Plug-in Hybrid (PHEV) sono cresciute del +80,7% ad ottobre 2026 grazie ai fringe benefit aziendali.
"""


class EVSalesPredictor:
    """Modello ML leggero per stimare l'impatto di sconti e colonnine sulle vendite provinciali."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.model = Ridge(alpha=1.0)
        self.scaler = StandardScaler()
        self.is_trained = False

    def load_data(self):
        conn = sqlite3.connect(self.db_path)
        df_geo = pd.read_sql("SELECT * FROM fact_geo_ev", conn)
        df_models = pd.read_sql("SELECT * FROM fact_bev_models", conn)
        conn.close()
        return df_geo, df_models

    def train(self):
        df_geo, _ = self.load_data()
        X = df_geo[["colonnine_per_1000_ab", "popolazione_2026", "crescita_ricarica_yoy_pct"]].values
        y = (df_geo["imm_bev_10m_2026"] / 10.0).values
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_trained = True

    def simulate_scenario(self, cod_prov, prezzo_medio_auto, sconto_euro, incremento_colonnine_pct):
        if not self.is_trained:
            self.train()

        df_geo, _ = self.load_data()
        row = df_geo[df_geo["cod_prov"] == cod_prov].iloc[0]

        base_monthly = row["imm_bev_10m_2026"] / 10.0
        base_quarterly = base_monthly * 3.0

        nuove_colonnine = row["punti_ricarica_2026"] * (1 + incremento_colonnine_pct / 100.0)
        nuova_densita = (nuove_colonnine / row["popolazione_2026"]) * 1000.0
        X_new = np.array([[nuova_densita, row["popolazione_2026"], row["crescita_ricarica_yoy_pct"]]])
        pred_monthly_infra = max(base_monthly, self.model.predict(self.scaler.transform(X_new))[0])
        delta_infra_q = (pred_monthly_infra - base_monthly) * 3.0

        sconto_pct = sconto_euro / prezzo_medio_auto
        elasticita = 1.8
        delta_prezzo_q = base_quarterly * (sconto_pct * elasticita)

        totale_previsto_q = min(base_quarterly * 1.45, base_quarterly + delta_infra_q + delta_prezzo_q)
        auto_aggiuntive = round(totale_previsto_q - base_quarterly)

        margine_lordo_unitario = prezzo_medio_auto * 0.075
        margine_netto_unitario = margine_lordo_unitario - sconto_euro
        margine_totale_trimestre = round(totale_previsto_q * margine_netto_unitario)

        return {
            "provincia": row["provincia"],
            "vendite_base_trimestre": round(base_quarterly),
            "vendite_previste_trimestre": round(totale_previsto_q),
            "auto_aggiuntive": auto_aggiuntive,
            "sconto_pct": round(sconto_pct * 100, 1),
            "margine_netto_unitario": round(margine_netto_unitario),
            "margine_totale_trimestre": margine_totale_trimestre,
            "alert_margine": margine_netto_unitario < 0
        }


def ask_copilot(question, api_key=None):
    if api_key and api_key.strip():
        try:
            from langchain_groq import ChatGroq
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGroq(temperature=0.2, model_name="llama-3.3-70b-versatile", groq_api_key=api_key.strip())
            messages = [
                SystemMessage(content=f"Sei un Direttore Commerciale Automotive esperto del mercato elettrico italiano e di Torino. Rispondi in italiano in modo concreto, usando SOLO questi dati reali:\n{TORINO_KNOWLEDGE_BASE}"),
                HumanMessage(content=question)
            ]
            return llm.invoke(messages).content
        except Exception as e:
            return f"⚠️ Errore connessione API Groq ({e}). Passo alla modalità offline:\n\n" + _offline_expert_response(question)
    else:
        return _offline_expert_response(question)


def _offline_expert_response(question):
    q = question.lower()
    if "torino" in q or "piemonte" in q or "ztl" in q or "bollo" in q:
        return (
            "### 🎯 Strategia Commerciale EV per Torino & Piemonte (Dati 2026)\n\n"
            "* **La leva fiscale n.1 (Bollo a vita):** In Piemonte le auto elettriche hanno l'**esenzione permanente dal bollo auto** (non solo 5 anni come nel resto d'Italia). Su un SUV medio si risparmiano oltre **3.000€ in 10 anni**.\n"
            "* **ZTL Centrale Torino:** Il cliente ottiene il permesso **Blu A gratuito** (pagando solo 32€ di bolli per 2 anni), valido anche per chi abita in prima cintura (es. Collegno, Moncalieri, Rivoli).\n"
            "* **Attenzione alle Strisce Blu:** A Torino la sosta sulle strisce blu **resta a pagamento** anche per le elettriche. Non usarla come argomento di vendita; punta invece sul fatto che Torino ha già **4.498 punti di ricarica** (+52% rispetto al 2025), quindi l'ansia da ricarica in città è superata."
        )
    elif "modelli" in q or "prezzo" in q or "sconto" in q or "leapmotor" in q:
        return (
            "### 📊 Analisi Modelli & Prezzi BEV Italia (UNRAE 10 Mesi 2026)\n\n"
            "* **Dominio assoluto del segmento Budget (<25.000€):** La **Leapmotor T03** da sola fa il **21,4%** del mercato elettrico italiano (23.640 unità)[cite: 4], seguita da **Dacia Spring** (5.692)[cite: 4] e **BYD Dolphin Surf** (5.542)[cite: 4].\n"
            "* **Consiglio per lo stock a Torino:** Senza incentivi statali diretti ai privati, spingere SUV elettrici sopra i 45.000€ sul cliente privato ha rotazione lentissima. Concentra lo stock privato sulle citycar/compatte sotto i **25.000€** (T03, Dolphin Surf, Grande Panda EV, Citroën ë-C3) e riserva i modelli sopra i 40.000€ (Tesla Model Y, BMW iX1) al **Noleggio a Lungo Termine** e alle partite IVA."
        )
    else:
        return (
            "### 💡 Insight Rapido Mercato EV 2026\n\n"
            "* **Mercato Totale BEV (Gen–Ott 2026):** 110.379 unità (quota 7,8%)[cite: 2, 4].\n"
            "* **Opportunità Torino:** Con 4.498 colonnine attive ma una quota BEV ferma al ~6,7% (contro il 10,5% di Milano), Torino ha un potenziale inespresso di circa **+1.800 immatricolazioni BEV/anno** colmabile puntando su:\n"
            "  1. Citycar sotto i 23.000€ per i pendolari della cintura torinese.\n"
            "  2. Pacchetti Noleggio Lungo Termine + Wallbox domestica per le aziende del polo industriale torinese."
        )