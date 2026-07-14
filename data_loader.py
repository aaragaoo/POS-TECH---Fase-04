"""
Camada de acesso a dados do dashboard analitico de obesidade.

A fonte dos dados e controlada por uma unica configuracao (DATA_SOURCE),
para que trocar de CSV para a API do backend (quando estiver pronta) nao
exija nenhuma mudanca no dashboard.py -- ele sempre consome o DataFrame
ja normalizado devolvido por `load_obesity_data()`.

Como trocar para a API depois que o backend estiver no ar:
1. Em `.streamlit/secrets.toml` (ou nas variaveis de ambiente do Streamlit
   Cloud), defina:
       DATA_SOURCE = "api"
       API_BASE_URL = "https://<sua-api-no-render>.onrender.com"
2. Redeploy. Nao e necessario alterar dashboard.py.

Enquanto o backend nao esta pronto, o padrao e DATA_SOURCE="csv", que le o
arquivo Obesity.csv (a base de treinamento usada no estudo).
"""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

CSV_PATH = Path(__file__).parent / "Obesity.csv"

# Ordem de severidade usada em todos os graficos do dashboard
OBESITY_ORDER = [
    "Insufficient_Weight",
    "Normal_Weight",
    "Overweight_Level_I",
    "Overweight_Level_II",
    "Obesity_Type_I",
    "Obesity_Type_II",
    "Obesity_Type_III",
]

# Rotulos em portugues para exibicao (mantendo o valor original como chave)
OBESITY_LABELS_PT = {
    "Insufficient_Weight": "Abaixo do peso",
    "Normal_Weight": "Peso normal",
    "Overweight_Level_I": "Sobrepeso I",
    "Overweight_Level_II": "Sobrepeso II",
    "Obesity_Type_I": "Obesidade I",
    "Obesity_Type_II": "Obesidade II",
    "Obesity_Type_III": "Obesidade III",
}

# Mapeamento dos campos da API (nomes em portugues, ver README do backend)
# para o schema do CSV original, para que o resto do app funcione igual
# independente da fonte.
API_FIELD_MAP = {
    "idade": "Age",
    "come_vegetaiis": "FCVC",
    "refeicoes_diariamente": "NCP",
    "come_entre_refeicao": "CAEC",
    "litro_agua": "CH2O",
    "frequencia_semanal_atvidade_fisica": "FAF",
    "horas_dispositivo_eletronico": "TUE",
    "consome_bebida_alcoolica": "CALC",
    "historico_familiar": "family_history",
    "alimentos_calorico": "FAVC",
    "meio_transporte": "MTRANS",
    "obesity": "Obesity",
    "fuma": "SMOKE",
    "monitora_calorias": "SCC",
}

_CAEC_CALC_NORMALIZE = {
    "no": "no",
    "sometimes": "Sometimes",
    "somentimes": "Sometimes",  # typo presente no contrato da API
    "frequently": "Frequently",
    "always": "Always",
}

_MTRANS_NORMALIZE = {
    "automobile": "Automobile",
    "public_transportation": "Public_Transportation",
    "walking": "Walking",
    "motorbike": "Motorbike",
    "bike": "Bike",
}

# Colunas que so existem no CSV de treinamento (a API nao coleta/retorna)
CSV_ONLY_COLUMNS = ["Height", "Weight"]
# Colunas que so existem quando os dados vem da API (log de predicoes)
API_ONLY_COLUMNS = ["id", "created_at"]

FULL_SCHEMA = [
    "Gender", "Age", "Height", "Weight", "family_history", "FAVC", "FCVC",
    "NCP", "CAEC", "SMOKE", "CH2O", "SCC", "FAF", "TUE", "CALC", "MTRANS",
    "Obesity",
]


def _get_setting(name: str, default=None):
    """Le config de st.secrets (Streamlit Cloud) e cai para env var / default."""
    try:
        if hasattr(st, "secrets") and name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name, default)


def get_data_source() -> str:
    return str(_get_setting("DATA_SOURCE", "csv")).strip().lower()


def _load_from_csv() -> pd.DataFrame:
    return pd.read_csv(CSV_PATH)


def _load_from_api() -> pd.DataFrame:
    base_url = _get_setting("API_BASE_URL", "http://localhost:8000")
    url = f"{str(base_url).rstrip('/')}/api/v1/obesity-records"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    records = payload.get("data", payload) if isinstance(payload, dict) else payload
    df = pd.DataFrame(records)

    if df.empty:
        return df

    df = df.rename(columns=API_FIELD_MAP)

    if "Gender" not in df.columns and "sexo_biologico" in df.columns:
        df["Gender"] = df["sexo_biologico"].map({1: "Male", 2: "Female"})
        df = df.drop(columns=["sexo_biologico"])

    for col in ["CAEC", "CALC"]:
        if col in df.columns:
            normalized = df[col].astype(str).str.lower().map(_CAEC_CALC_NORMALIZE)
            df[col] = normalized.fillna(df[col])

    if "MTRANS" in df.columns:
        normalized = df["MTRANS"].astype(str).str.lower().map(_MTRANS_NORMALIZE)
        df["MTRANS"] = normalized.fillna(df["MTRANS"])

    for col in ["family_history", "FAVC", "SMOKE", "SCC"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.lower()

    if "created_at" in df.columns:
        df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    for col in ["Age", "FCVC", "NCP", "CH2O", "FAF", "TUE"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


@st.cache_data(ttl=300, show_spinner="Carregando dados...")
def load_obesity_data() -> pd.DataFrame:
    """Retorna o DataFrame normalizado, de onde quer que os dados venham."""
    source = get_data_source()
    df = _load_from_api() if source == "api" else _load_from_csv()

    if "Height" in df.columns and "Weight" in df.columns:
        df["BMI"] = df["Weight"] / (df["Height"] ** 2)

    if "Obesity" in df.columns:
        df["Obesity"] = pd.Categorical(df["Obesity"], categories=OBESITY_ORDER, ordered=True)

    return df


def missing_columns(df: pd.DataFrame) -> list[str]:
    """Colunas do schema completo que a fonte atual nao fornece (ex: API sem Height/Weight)."""
    return [c for c in FULL_SCHEMA if c not in df.columns]
