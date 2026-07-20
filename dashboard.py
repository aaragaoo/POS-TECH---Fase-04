"""
Dashboard analitico - Estudo sobre Obesidade
Tech Challenge Fase 4 - Pos Tech FIAP (Data Analytics)

Painel de insights para apoiar a equipe medica na compreensao dos fatores
associados aos diferentes niveis de obesidade. Nao faz predicao individual
(isso e feito pelo app preditivo separado) -- aqui o foco e a leitura
agregada da base de dados, em formato executivo (metricas e medias, sem
graficos estatisticos como boxplot).

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

ORDER_LABELS = [OBESITY_LABELS_PT[c] for c in OBESITY_ORDER]
COLOR_SEQUENCE = px.colors.sequential.Sunset
GENDER_LABELS_PT = {"Female": "Feminino", "Male": "Masculino"}
BAR_GAP = 0.15


def apply_theme(fig):
    """Forca cores explicitas de fundo/fonte do grafico conforme o tema
    selecionado (nao depende so do 'template' do plotly, que pode nao ser
    respeitado pelo componente de renderizacao)."""
    if is_dark:
        fig.update_layout(
            paper_bgcolor="#0e1117",
            plot_bgcolor="#0e1117",
            font_color="#fafafa",
            legend=dict(font=dict(color="#fafafa")),
            title_font_color="#fafafa",
            hoverlabel=dict(bgcolor="#161a23", font_color="#fafafa"),
        )
        fig.update_xaxes(gridcolor="#30363d", linecolor="#30363d", zerolinecolor="#30363d")
        fig.update_yaxes(gridcolor="#30363d", linecolor="#30363d", zerolinecolor="#30363d")
    else:
        fig.update_layout(
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            font_color="#262730",
            title_font_color="#262730",
        )
    return fig


def style_bar(fig):
    """Colunas mais grossas (menos espaco entre barras)."""
    fig.update_layout(bargap=BAR_GAP, bargroupgap=0.05)
    return apply_theme(fig)


# Niveis considerados "obesidade" propriamente dita (exclui abaixo do peso,
# peso normal e sobrepeso), usados nos insights de concentracao por grupo.
SEVERE_LABELS = ORDER_LABELS[4:]


def trend_insight(agg, label):
    """Frase curta comparando o primeiro e o ultimo nivel presentes no
    grafico, para dar contexto rapido sem exigir leitura detalhada."""
    if len(agg) < 2:
        return None
    first, last = agg.iloc[0], agg.iloc[-1]
    delta = last[label] - first[label]
    if abs(delta) < 0.05:
        return f"{label} se mantem estavel entre os niveis (~{first[label]:.1f})."
    direcao = "sobe" if delta > 0 else "cai"
    return (
        f"{label} {direcao} de {first[label]:.1f} ({first['Nivel']}) "
        f"para {last[label]:.1f} ({last['Nivel']})."
    )


def severe_share_insight(cross, group_col):
    """% de cada categoria (genero, habito, etc.) classificada em algum
    nivel de obesidade (I a III), para destacar disparidades entre grupos."""
    severe = cross[cross["Obesity_pt"].isin(SEVERE_LABELS)]
    if severe.empty:
        return None
    share = severe.groupby(group_col)["Percentual"].sum().sort_values(ascending=False)
    if share.empty:
        return None
    if len(share) == 1:
        cat = share.index[0]
        return f"{share.iloc[0]:.0f}% dos pacientes de '{cat}' estao em algum nivel de obesidade (I a III)."
    partes = " · ".join(f"{cat}: {pct:.0f}%" for cat, pct in share.items())
    return f"Em algum nivel de obesidade (I a III) — {partes}."


def bar_by_level(data, y_col, label, template, color_sequence):
    """Grafico de barras com a media de y_col por nivel de obesidade.

    Usado no lugar de boxplot: mais direto de ler para um publico de
    negocio/medico (uma barra e um numero por nivel, com rotulo visivel).
    Retorna (figura, insight) para exibir um descritivo logo abaixo.
    """
    agg = (
        data.groupby("Obesity_pt", observed=True)[y_col]
        .mean()
        .reindex(ORDER_LABELS)
        .dropna()
        .reset_index()
    )
    agg.columns = ["Nivel", label]
    fig = px.bar(
        agg,
        x="Nivel",
        y=label,
        color="Nivel",
        category_orders={"Nivel": ORDER_LABELS},
        color_discrete_sequence=color_sequence,
        title=f"{label} - media por nivel de obesidade",
        text_auto=".1f",
        template=template,
    )
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title=label)
    return style_bar(fig), trend_insight(agg, label)


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
if "Gender" in df_raw.columns:
    df_raw["Gender_pt"] = df_raw["Gender"].map(GENDER_LABELS_PT).fillna(df_raw["Gender"])
ausentes = missing_columns(df_raw)

# --------------------------------------------------------------------------
# Aparencia (tema claro/escuro)
# --------------------------------------------------------------------------
if "tema" not in st.session_state:
    st.session_state.tema = "Claro"

st.sidebar.header("Aparencia")
st.session_state.tema = st.sidebar.radio(
    "Tema",
    options=["Claro", "Escuro"],
    index=["Claro", "Escuro"].index(st.session_state.tema),
    horizontal=True,
)
is_dark = st.session_state.tema == "Escuro"
plot_template = "plotly_dark" if is_dark else "plotly_white"

if is_dark:
    st.markdown(
        """
        <style>
        .stApp { background-color: #0e1117; color: #fafafa; }
        section[data-testid="stSidebar"] { background-color: #161a23; }
        [data-testid="stHeader"] { background-color: #0e1117; }
        [data-testid="stAppViewBlockContainer"] { background-color: #0e1117; }

        /* Contraste dos textos no tema escuro */
        .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 { color: #fafafa !important; }
        [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] p { color: #fafafa; }
        [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: #c9d1d9 !important; }
        [data-testid="stWidgetLabel"] p { color: #fafafa !important; }
        [data-testid="stMetricValue"] { color: #fafafa; }
        [data-testid="stMetricLabel"] { color: #c9d1d9; }
        [data-testid="stTabs"] button p { color: #c9d1d9; }
        [data-testid="stTabs"] button[aria-selected="true"] p { color: #fafafa !important; }
        section[data-testid="stSidebar"] label p { color: #fafafa !important; }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #fafafa !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <style>
        .stApp { background-color: #ffffff; color: #262730; }
        section[data-testid="stSidebar"] { background-color: #f5f5f5; }
        </style>
        """,
        unsafe_allow_html=True,
    )

st.sidebar.divider()

# --------------------------------------------------------------------------
# Cabecalho
# --------------------------------------------------------------------------
st.title("🩺 Painel Analitico - Obesidade")
st.caption(
    "Visao de negocio para a equipe medica: principais fatores associados "
    "aos niveis de obesidade observados na base de dados."
)

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
sel_gender = st.sidebar.multiselect(
    "Genero",
    genders,
    default=genders,
    format_func=lambda g: GENDER_LABELS_PT.get(g, g),
)

sel_age = None
if "Age" in df_raw.columns and df_raw["Age"].notna().any():
    age_min, age_max = int(df_raw["Age"].min()), int(df_raw["Age"].max())
    st.sidebar.subheader("Idade")
    st.sidebar.caption("Digite a faixa etaria desejada")
    col_idade_min, col_idade_max = st.sidebar.columns(2)
    idade_de = col_idade_min.number_input(
        "De", min_value=age_min, max_value=age_max, value=age_min, step=1
    )
    idade_ate = col_idade_max.number_input(
        "Ate", min_value=age_min, max_value=age_max, value=age_max, step=1
    )
    if idade_de > idade_ate:
        st.sidebar.warning("'De' maior que 'Ate' -- valores invertidos automaticamente.")
        idade_de, idade_ate = idade_ate, idade_de
    sel_age = (idade_de, idade_ate)

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
kpi_cols = st.columns(3)

if "Age" in df.columns:
    kpi_cols[0].metric("Idade media", f"{df['Age'].mean():.1f} anos")

if "family_history" in df.columns:
    pct_hist = (df["family_history"].astype(str).str.lower() == "yes").mean() * 100
    kpi_cols[1].metric("Com historico familiar", f"{pct_hist:.0f}%")

nivel_mais_comum = df["Obesity_pt"].mode().iloc[0] if not df["Obesity_pt"].mode().empty else "-"
kpi_cols[2].metric("Nivel mais frequente", nivel_mais_comum)

st.divider()

# --------------------------------------------------------------------------
# Tabs
# --------------------------------------------------------------------------
tab_overview, tab_corpo, tab_habitos = st.tabs(
    ["Visao geral", "Perfil e corpo", "Habitos e estilo de vida"]
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
            color_discrete_sequence=COLOR_SEQUENCE,
            title="Distribuicao dos niveis de obesidade",
            text_auto=True,
            template=plot_template,
        )
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Pacientes")
        st.plotly_chart(style_bar(fig), width="stretch", theme=None)
        top_row = dist.loc[dist["Registros"].idxmax()]
        pct_top = top_row["Registros"] / dist["Registros"].sum() * 100
        st.caption(f"Nivel mais frequente: **{top_row['Nivel']}** ({pct_top:.0f}% da base filtrada).")

    with c2:
        if "Gender_pt" in df.columns:
            fig = px.pie(
                df,
                names="Gender_pt",
                title="Distribuicao por genero",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Set2,
                template=plot_template,
            )
            fig.update_layout(legend_title_text="Genero")
            st.plotly_chart(apply_theme(fig), width="stretch", theme=None)
            gender_counts = df["Gender_pt"].value_counts()
            top_gender = gender_counts.idxmax()
            pct_gender = gender_counts.max() / gender_counts.sum() * 100
            st.caption(f"**{top_gender}** representa {pct_gender:.0f}% da base filtrada.")

    if {"Gender_pt", "Obesity_pt"}.issubset(df.columns):
        cross = (
            df.groupby(["Gender_pt", "Obesity_pt"], observed=True)
            .size()
            .reset_index(name="Registros")
        )
        total_por_genero = cross.groupby("Gender_pt")["Registros"].transform("sum")
        cross["Percentual"] = cross["Registros"] / total_por_genero * 100
        fig = px.bar(
            cross,
            x="Gender_pt",
            y="Percentual",
            color="Obesity_pt",
            category_orders={"Obesity_pt": ORDER_LABELS},
            color_discrete_sequence=COLOR_SEQUENCE,
            title="Nivel de obesidade por genero (% dentro de cada genero)",
            labels={"Gender_pt": "Genero", "Percentual": "% de pacientes"},
            template=plot_template,
        )
        st.plotly_chart(style_bar(fig), width="stretch", theme=None)
        insight_cross = severe_share_insight(cross, "Gender_pt")
        if insight_cross:
            st.caption(insight_cross)

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
            fig, insight_imc = bar_by_level(df, "BMI", "IMC (kg/m²)", plot_template, COLOR_SEQUENCE)
            st.plotly_chart(fig, width="stretch", theme=None)
            if insight_imc:
                st.caption(insight_imc)

        with c2:
            fig = px.scatter(
                df,
                x="Height",
                y="Weight",
                color="Obesity_pt",
                category_orders={"Obesity_pt": ORDER_LABELS},
                color_discrete_sequence=COLOR_SEQUENCE,
                title="Altura x Peso, colorido por nivel de obesidade",
                labels={"Height": "Altura (m)", "Weight": "Peso (kg)"},
                opacity=0.7,
                template=plot_template,
            )
            st.plotly_chart(apply_theme(fig), width="stretch", theme=None)
            peso_por_nivel = (
                df.groupby("Obesity_pt", observed=True)["Weight"]
                .mean()
                .reindex(ORDER_LABELS)
                .dropna()
            )
            if len(peso_por_nivel) >= 2:
                st.caption(
                    f"Peso medio sobe de {peso_por_nivel.iloc[0]:.0f} kg ({peso_por_nivel.index[0]}) "
                    f"para {peso_por_nivel.iloc[-1]:.0f} kg ({peso_por_nivel.index[-1]}), para "
                    "alturas semelhantes entre os niveis."
                )

    if "Age" in df.columns:
        fig, insight_idade = bar_by_level(df, "Age", "Idade", plot_template, COLOR_SEQUENCE)
        st.plotly_chart(fig, width="stretch", theme=None)
        if insight_idade:
            st.caption(insight_idade)

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
            color_discrete_sequence=COLOR_SEQUENCE,
            title=f"Nivel de obesidade por: {habit_options[chosen][0]}",
            labels={chosen: "", "Percentual": "% de pacientes"},
            template=plot_template,
        )
        st.plotly_chart(style_bar(fig), width="stretch", theme=None)
        insight_habito = severe_share_insight(cross, chosen)
        if insight_habito:
            st.caption(insight_habito)

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
                fig, insight_habit_num = bar_by_level(df, col, label, plot_template, COLOR_SEQUENCE)
                st.plotly_chart(fig, width="stretch", theme=None)
                if insight_habit_num:
                    st.caption(insight_habit_num)

st.divider()
st.caption(
    "Tech Challenge Fase 4 - Pos Tech FIAP · Painel construido com Streamlit. "
    "Uso educacional/demonstrativo, nao substitui avaliacao medica ou "
    "nutricional profissional."
)
