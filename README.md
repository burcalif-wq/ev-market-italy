# ⚡ EV Market Intelligence & AI Sales Copilot (Italy & Turin Focus)

An end-to-end **Data Analytics, Machine Learning, and Generative AI** project designed to analyze the adoption of Battery Electric Vehicles (BEVs) in Italy, uncover regional infrastructure bottlenecks (with a deep dive into **Turin and Piedmont**), and provide automotive dealers with a predictive "What-If" sales simulator.

---

## 🎯 Why This Project? (Business Context)

In 2026, the Italian electric vehicle market presents a stark paradox: while public charging infrastructure has rapidly expanded past **88,000 charging points** nationwide (with Piedmont ranking second in Italy with over 9,000 points and Turin ranking third among Italian provinces), BEV market share remains stalled around **6–7%** due to the absence of direct purchase incentives for private buyers and high upfront vehicle prices.

Automotive manufacturers, leasing companies, and dealerships—especially in historic automotive hubs like **Turin**—can no longer rely on traditional sales forecasting. They need data-driven tools to understand how **local charging density, price discounts, and total cost of ownership (TCO)** impact EV demand.

## 🚀 Project Objectives

1. **Automated Data Pipeline (ETL):** Extract, clean, and unify official monthly BEV registration reports (**UNRAE**) with public charging infrastructure census data (**Motus-E**) and vehicle technical specifications (battery kWh, WLTP range, list price).
2. **Geospatial & Market Analysis (BI):** Quantify the correlation between charging point density and EV adoption across Italian provinces, highlighting the gap between Turin/Piedmont and top-performing hubs like Milan/Lombardy.
3. **Predictive Modeling (ML):** Build a regression model (**XGBoost / Scikit-Learn**) to estimate **price elasticity of demand** and forecast quarterly EV sales based on dealer discounts, vehicle range, and local charging growth.
4. **Specialized AI Sales Copilot (RAG):** Develop a Retrieval-Augmented Generation assistant (**LangChain + ChromaDB**) trained on Italian automotive tax regulations, Turin ZTL/parking exemptions, and EV vs. ICE Total Cost of Ownership (TCO) data to generate actionable commercial strategies.
5. **Interactive Decision App:** Deploy a **Streamlit** web application allowing Sales Managers to run "What-If" pricing simulations and query market data in natural language.

---

## 🏗️ Repository Architecture

```text
ev-market-italy/
├── data/
│   ├── raw/                  # Original UNRAE & Motus-E PDF/CSV reports
│   └── processed/            # Cleaned datasets & SQLite database (ev_italy.db)
├── notebooks/
│   ├── 01_eda_market.ipynb   # Exploratory Data Analysis & regional correlations
│   └── 02_ml_modeling.ipynb  # Feature engineering & XGBoost training
├── src/
│   ├── etl_pipeline.py       # PDF table extraction & data normalization
│   ├── ml_forecast.py        # Sales & price elasticity prediction module
│   └── rag_assistant.py      # LangChain RAG pipeline for commercial insights
├── app/
│   └── main.py               # Streamlit Web App (BI + Simulator + AI Copilot)
├── docs/                     # Regulatory PDFs, Turin ZTL rules & TCO guides for RAG
├── requirements.txt          # Python dependencies
└── README.md