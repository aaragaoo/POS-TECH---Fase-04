# Painel Analitico - Obesidade

Dashboard em Streamlit com a visao analitica do Tech Challenge Fase 4 (Data
Analytics): principais fatores associados aos niveis de obesidade, para
apoiar a equipe medica. Painel ao vivo: **https://painel-obesidade-postech.streamlit.app**

## Estrutura

```
dashboard.py              # app Streamlit (UI, filtros, graficos)
data_loader.py            # acesso a dados: hoje CSV, depois API
Obesity.csv               # base de treinamento usada como fonte inicial
requirements.txt
.streamlit/
├── config.toml           # tema claro (padrao)
└── secrets.toml.example  # copie para secrets.toml
```

## Rodando localmente

```bash
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

- **Hoje** (`DATA_SOURCE=csv`, padrao): le `Obesity.csv`, a base de
  treinamento do modelo.
- **Quando o backend estiver pronto** (`DATA_SOURCE=api`): consome
  `GET /api/v1/obesity-records` do backend. O dashboard detecta
  automaticamente quais colunas a fonte atual fornece e oculta as secoes
  que dependem de dados ausentes.

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
- **Perfil e corpo**: IMC por nivel, dispersao altura x peso, idade por
  nivel.
- **Habitos e estilo de vida**: nivel de obesidade por habito (alimentacao
  calorica, historico familiar, comer entre refeicoes, alcool, transporte,
  fumo, monitoramento de calorias) e distribuicoes de vegetais, refeicoes,
  agua, atividade fisica e tempo de tela.

Filtros de genero, faixa etaria e nivel de obesidade ficam na barra lateral.
Tema claro/escuro fica no topo da barra lateral.

## Deploy no Streamlit Cloud

Repositorio ja pronto para ser a raiz do app: em
[streamlit.io/cloud](https://streamlit.io/cloud), aponte para este repo e o
arquivo principal `dashboard.py`, e configure os secrets se for usar a API.

## Aviso

Uso educacional/demonstrativo — nao substitui avaliacao medica ou
nutricional profissional.
