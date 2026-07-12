# Painel Analitico - Obesidade

Dashboard em Streamlit com a visao analitica exigida pelo Tech Challenge
Fase 4 (Data Analytics): principais insights sobre os fatores associados
aos niveis de obesidade, para apoiar a equipe medica. Este painel e
separado do app preditivo (formulario que roda o modelo de ML).

## Estrutura

```
dashboard-obesidade/
├── dashboard.py              # app Streamlit (UI, filtros, graficos)
├── data_loader.py            # acesso a dados: hoje CSV, depois API
├── Obesity.csv               # base de treinamento usada como fonte inicial
├── requirements.txt
└── .streamlit/
    ├── config.toml           # tema
    └── secrets.toml.example  # copie para secrets.toml
```

## Rodando localmente

```bash
cd dashboard-obesidade
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
streamlit run dashboard.py
```

Abre em `http://localhost:8501`.

## Fonte de dados: CSV agora, API depois

O painel nunca le o CSV nem chama a API diretamente em `dashboard.py` — tudo
passa por `data_loader.load_obesity_data()`, que decide a fonte a partir de
`DATA_SOURCE`:

- **Hoje** (`DATA_SOURCE=csv`, padrao): le `Obesity.csv`, a base usada no
  estudo/treinamento do modelo (17 colunas, inclui altura, peso, fumante,
  monitora calorias).
- **Quando o backend estiver pronto** (`DATA_SOURCE=api`): consome
  `GET /api/v1/obesity-records` do backend (repo `backend-ml-obesity`),
  que registra as predicoes feitas pelo app. Essa fonte tem menos colunas
  (sem altura/peso/fumante/monitora calorias, ja que o formulario de
  predicao nao coleta esses campos) e ganha `created_at`, usado para o
  grafico de volume de predicoes ao longo do tempo. O dashboard detecta
  automaticamente quais colunas existem e oculta as secoes que dependem de
  dados ausentes.

Para trocar a fonte quando o backend estiver no ar:

1. Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml`
   (local) ou cole os valores em *App settings → Secrets* no Streamlit
   Cloud.
2. Ajuste:
   ```toml
   DATA_SOURCE = "api"
   API_BASE_URL = "https://SEU-BACKEND.onrender.com"
   ```
3. Reinicie/redeploy o app. Nenhuma alteracao de codigo e necessaria.

## Conteudo do painel

- **Visao geral**: distribuicao dos niveis de obesidade, distribuicao por
  genero, cruzamento genero x nivel.
- **Perfil e corpo**: IMC por nivel (quando altura/peso disponiveis),
  dispersao altura x peso, idade por nivel.
- **Habitos e estilo de vida**: nivel de obesidade por habito (alimentacao
  calorica, historico familiar, comer entre refeicoes, alcool, transporte,
  fumo, monitoramento de calorias) e distribuicoes de vegetais, refeicoes,
  agua, atividade fisica e tempo de tela por nivel.
- **Correlacoes**: heatmap entre variaveis numericas; quando a fonte e a
  API, mostra tambem o volume diario de predicoes registradas.
- **Dados**: tabela filtrada + download em CSV.

Filtros de genero, faixa etaria e nivel de obesidade ficam na barra lateral
e afetam todas as abas.

## Deploy no Streamlit Cloud

1. Suba esta pasta para um repositorio GitHub (ela ja esta pronta para ser
   a raiz do repo: `dashboard.py`, `requirements.txt`, etc.).
2. Em [streamlit.io/cloud](https://streamlit.io/cloud), aponte para o repo
   e o arquivo principal `dashboard.py`.
3. Configure os secrets (`DATA_SOURCE`, `API_BASE_URL`) em *App settings →
   Secrets*.

## Aviso

Uso educacional/demonstrativo — nao substitui avaliacao medica ou
nutricional profissional.
