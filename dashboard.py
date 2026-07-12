"""
Dashboard analitico - Estudo sobre Obesidade
Tech Challenge Fase 4 - Pos Tech FIAP (Data Analytics)

Painel de insights para apoiar a equipe medica na compreensao dos fatores
associados aos diferentes niveis de obesidade. Nao faz predicao individual
(isso e feito pelo app preditivo separado) -- aqui o foco e a leitura
agregada da base de dados.

Fonte dos dados: ver data_loader.py (hoje = Obesity.csv; depois = API do
backend, bastando trocar DATA_SOURCE em secrets/env, sem tocar neste
arquivo).
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from data_loader import (
    OBESITY_LABELS_PT,
    OBESITY_ORDER,
    get_data_source,
    load_obesity_data,
    missing_columns,
)

st.set_page_config(
    page_title="Obesidade - Painel Analitico",
    page_icon="🩺",
    layout="wide",
)

PALETTE = px.colors.sequential.OrRd
ORDER_LABELS = [OBESITY_LABELS_PT[c] for c in OBESITY_ORDER]


# --------------------------------------------------------------------------
# Dados
# --------------------------------------------------------------------------
try:
    df_raw = load_obesity_data()
except Exception as exc:  # fonte API fora do ar, csv ausente, etc.
    st.error(
        "Nao foi possivel carregar os dados. "
        f"Fonte configurada: **{get_data_source()}**.\n\nDetalhe: {exc}"
    )
    st.stop()

if df_raw.empty:
    st.warning("A fonte de dados nao retornou nenhum registro ainda.")
    st.stop()

df_raw["Obesity_pt"] = df_raw["Obesity"].map(OBESITY_LABELS_PT)
ausentes = missing_columns(df_raw)

# --------------------------------------------------------------------------
# Cabecalho
# --------------------------------------------------------------------------
st.title("🩺 Painel Analitico - Obesidade")
st.caption(
    "Visao de negocio para a equipe medica: principais fatores associados "
    "aos niveis de obesidade observados na base de dados."
)

source_badge = "📄 CSV (base de treinamento)" if get_data_source() != "api" else "🔌 API (dados em producao)"
st.info(f"Fonte de dados atual: **{source_badge}** · {len(df_raw)} registros carregados.")

if ausentes:
    st.caption(
        "⚠️ Esta fonte de dados nao possui as colunas "
        f"{', '.join(ausentes)}. As secoes que dependem delas ficam ocultas."
    )

# --------------------------------------------------------------------------
# Filtros (sidebar)
# --------------------------------------------------------------------------
st.sidebar.header("Filtros")

genders = sorted(df_raw["Gender"].dropna().unique().tolist()) if "Gender" in df_raw else []
sel_gender = st.sidebar.multiselect("Genero", genders, default=genders)

if "Age" in df_raw.columns and df_raw["Age"].notna().any():
    age_min, age_max = int(df_raw["Age"].min()), int(df_raw["Age"].max())
    sel_age = st.sidebar.slider("Faixa etaria", age_min, age_max, (age_min, age_max))
else:
    sel_age = None

present_levels = [c for c in OBESITY_ORDER if c in df_raw["Obesity"].unique().tolist()]
sel_levels = st.sidebar.multiselect(
    "Nivel de obesidade",
    options=present_levels,
    default=present_levels,
    format_func=lambda c: OBESITY_LABELS_PT.get(c, c),
)

df = df_raw.copy()
if sel_gender:
    df = df[df["Gender"].isin(sel_gender)]
if sel_age:
    df = df[(df["Age"] >= sel_age[0]) & (df["Age"] <= sel_age[1])]
if sel_levels:
    df = df[df["Obesity"].isin(sel_levels)]

if df.empty:
    st.warning("Nenhum registro corresponde aos filtros selecionados.")
    st.stop()

# --------------------------------------------------------------------------
# KPIs
# --------------------------------------------------------------------------
kpi_cols = st.columns(4)
kpi_cols[0].metric("Registros analisados", len(df))

if "Age" in df.columns:
    kpi_cols[1].metric("Idade media", f"{df['Age'].mean():.1f} anos")

if "family_history" in df.columns:
    pct_hist = (df["family_history"].astype(str).str.lower() == "yes").mean() * 100
    kpi_cols[2].metric("Com historico familiar", f"{pct_hist:.0f}%")

nivel_mais_comum = df["Obesity_pt"].mode().iloc[0] if not df["Obesity_pt"].mode().empty else "-"
kpi_cols[3].metric("Nivel mais frequente", nivel_mais_comum)

st.divider()

# --------------------------------------------------------------------------
# Tabs
# --------------------------------------------------------------------------
tab_overview, tab_corpo, tab_habitos, tab_correlacao, tab_dados = st.tabs(
    ["Visao geral", "Perfil e corpo", "Habitos e estilo de vida", "Correlacoes", "Dados"]
)

# ---- Visao geral ----------------------------------------------------------
with tab_overview:
    c1, c2 = st.columns([1.3, 1])

    with c1:
        dist = (
            df["Obesity_pt"]
            .value_counts()
            .reindex(ORDER_LABELS)
            .dropna()
            .reset_index()
        )
        dist.columns = ["Nivel", "Registros"]
        fig = px.bar(
            dist,
            x="Nivel",
            y="Registros",
            color="Nivel",
            category_orders={"Nivel": ORDER_LABELS},
            color_discrete_sequence=px.colors.sequential.Sunset,
            title="Distribuicao dos niveis de obesidade",
        )
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Pacientes")
        st.plotly_chart(fig, width="stretch")

    with c2:
        if "Gender" in df.columns:
            fig = px.pie(
                df,
                names="Gender",
                title="Distribuicao por genero",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            st.plotly_chart(fig, width="stretch")

    if {"Gender", "Obesity_pt"}.issubset(df.columns):
        cross = (
            df.groupby(["Gender", "Obesity_pt"], observed=True)
            .size()
            .reset_index(name="Registros")
        )
        total_por_genero = cross.groupby("Gender")["Registros"].transform("sum")
        cross["Percentual"] = cross["Registros"] / total_por_genero * 100
        fig = px.bar(
            cross,
            x="Gender",
            y="Percentual",
            color="Obesity_pt",
            category_orders={"Obesity_pt": ORDER_LABELS},
            color_discrete_sequence=px.colors.sequential.Sunset,
            title="Nivel de obesidade por genero (% dentro de cada genero)",
            labels={"Gender": "Genero", "Percentual": "% de pacientes"},
        )
        st.plotly_chart(fig, width="stretch")

    st.markdown(
        "**Leitura para a equipe medica:** o grafico acima ajuda a identificar "
        "se algum genero esta desproporcionalmente concentrado em niveis mais "
        "altos de obesidade, o que pode orientar campanhas de triagem "
        "direcionadas."
    )

# ---- Perfil e corpo ---------------------------------------------------
with tab_corpo:
    if "BMI" not in df.columns:
        st.info(
            "IMC, altura e peso nao estao disponiveis na fonte de dados atual "
            "(a API de producao nao coleta esses campos). Esta secao usa a "
            "base CSV de treinamento."
        )
    else:
        c1, c2 = st.columns(2)
        with c1:
            fig = px.box(
                df,
                x="Obesity_pt",
                y="BMI",
                color="Obesity_pt",
                category_orders={"Obesity_pt": ORDER_LABELS},
                color_discrete_sequence=px.colors.sequential.Sunset,
                title="IMC por nivel de obesidade",
                labels={"Obesity_pt": "", "BMI": "IMC (kg/m²)"},
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width="stretch")

        with c2:
            fig = px.scatter(
                df,
                x="Height",
                y="Weight",
                color="Obesity_pt",
                category_orders={"Obesity_pt": ORDER_LABELS},
                color_discrete_sequence=px.colors.sequential.Sunset,
                title="Altura x Peso, colorido por nivel de obesidade",
                labels={"Height": "Altura (m)", "Weight": "Peso (kg)"},
                opacity=0.7,
            )
            st.plotly_chart(fig, width="stretch")

    if "Age" in df.columns:
        fig = px.box(
            df,
            x="Obesity_pt",
            y="Age",
            color="Obesity_pt",
            category_orders={"Obesity_pt": ORDER_LABELS},
            color_discrete_sequence=px.colors.sequential.Sunset,
            title="Idade por nivel de obesidade",
            labels={"Obesity_pt": "", "Age": "Idade"},
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, width="stretch")

# ---- Habitos e estilo de vida ------------------------------------------
with tab_habitos:
    st.caption(
        "Percentual de pacientes em cada nivel de obesidade, por habito. "
        "Use para identificar quais comportamentos mais se associam a niveis "
        "mais graves."
    )

    habit_options = {
        "FAVC": ("Consome alimentos caloricos com frequencia", ["no", "yes"]),
        "family_history": ("Historico familiar de excesso de peso", ["no", "yes"]),
        "CAEC": ("Come entre as refeicoes", ["no", "Sometimes", "Frequently", "Always"]),
        "CALC": ("Consumo de alcool", ["no", "Sometimes", "Frequently", "Always"]),
        "MTRANS": ("Meio de transporte", None),
        "SMOKE": ("Fumante", ["no", "yes"]),
        "SCC": ("Monitora calorias ingeridas", ["no", "yes"]),
    }
    habit_options = {k: v for k, v in habit_options.items() if k in df.columns}

    if habit_options:
        chosen = st.selectbox(
            "Habito",
            options=list(habit_options.keys()),
            format_func=lambda k: habit_options[k][0],
        )
        cross = (
            df.groupby([chosen, "Obesity_pt"], observed=True)
            .size()
            .reset_index(name="Registros")
        )
        total_por_categoria = cross.groupby(chosen)["Registros"].transform("sum")
        cross["Percentual"] = cross["Registros"] / total_por_categoria * 100
        order = habit_options[chosen][1]
        fig = px.bar(
            cross,
            x=chosen,
            y="Percentual",
            color="Obesity_pt",
            category_orders={"Obesity_pt": ORDER_LABELS, chosen: order} if order else {"Obesity_pt": ORDER_LABELS},
            color_discrete_sequence=px.colors.sequential.Sunset,
            title=f"Nivel de obesidade por: {habit_options[chosen][0]}",
            labels={chosen: "", "Percentual": "% de pacientes"},
        )
        st.plotly_chart(fig, width="stretch")

    num_habits = {
        "FCVC": "Frequencia no consumo de vegetais",
        "NCP": "Numero de refeicoes principais/dia",
        "CH2O": "Consumo de agua diario",
        "FAF": "Frequencia de atividade fisica",
        "TUE": "Tempo em dispositivos eletronicos",
    }
    num_habits = {k: v for k, v in num_habits.items() if k in df.columns}
    if num_habits:
        c1, c2 = st.columns(2)
        for i, (col, label) in enumerate(num_habits.items()):
            target = c1 if i % 2 == 0 else c2
            with target:
                fig = px.box(
                    df,
                    x="Obesity_pt",
                    y=col,
                    color="Obesity_pt",
                    category_orders={"Obesity_pt": ORDER_LABELS},
                    color_discrete_sequence=px.colors.sequential.Sunset,
                    title=label,
                    labels={"Obesity_pt": "", col: label},
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, width="stretch")

# ---- Correlacoes ---------------------------------------------------------
with tab_correlacao:
    numeric_cols = [
        c for c in ["Age", "Height", "Weight", "BMI", "FCVC", "NCP", "CH2O", "FAF", "TUE"]
        if c in df.columns
    ]
    if len(numeric_cols) >= 2:
        corr = df[numeric_cols].corr(numeric_only=True)
        fig = px.imshow(
            corr,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            title="Correlacao entre variaveis numericas",
        )
        st.plotly_chart(fig, width="stretch")
        st.markdown(
            "**Leitura para a equipe medica:** valores proximos de +1 ou -1 "
            "indicam variaveis que se movem juntas (ex.: peso e IMC). Isso "
            "ajuda a identificar quais fatores de estilo de vida merecem mais "
            "atencao clinica."
        )
    else:
        st.info("Nao ha colunas numericas suficientes para calcular correlacoes.")

    if get_data_source() == "api" and "created_at" in df_raw.columns:
        st.subheader("Predicoes ao longo do tempo")
        ts = (
            df_raw.dropna(subset=["created_at"])
            .set_index("created_at")
            .resample("D")["Obesity"]
            .count()
            .reset_index(name="Predicoes")
        )
        fig = px.line(ts, x="created_at", y="Predicoes", title="Volume diario de predicoes registradas na API")
        st.plotly_chart(fig, width="stretch")

# ---- Dados -----------------------------------------------------------
with tab_dados:
    st.dataframe(df, width="stretch", height=500)
    st.download_button(
        "Baixar dados filtrados (CSV)",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="obesidade_filtrado.csv",
        mime="text/csv",
    )

st.divider()
st.caption(
    "Tech Challenge Fase 4 - Pos Tech FIAP · Painel construido com Streamlit. "
    "Uso educacional/demonstrativo, nao substitui avaliacao medica ou "
    "nutricional profissional."
)
