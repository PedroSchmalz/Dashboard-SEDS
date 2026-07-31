"""
Painel SuperAção SP — protótipo em Streamlit.

Identidade visual conforme MANUAL DE IDENTIDADE VISUAL do Governo do Estado de
São Paulo (GESP v1.6, abr 2023). Referências de página no código.

Rodar:      streamlit run app.py
Requisitos: streamlit, pandas

Para acrescentar um relatório: escreva uma função que recebe o dicionário de
tabelas e desenha na tela, e registre uma entrada em RELATORIOS.
"""

from __future__ import annotations

import altair as alt
import base64
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


# =====================================================================
# CONFIGURAÇÃO
# =====================================================================

BASE_DIR = Path(__file__).resolve().parent
DIR_TABELAS = BASE_DIR / "dados"       # funil.csv, tempos.csv, recusas.csv, qualidade.csv
DIR_MARCAS = BASE_DIR / "assets"       # pasta com os arquivos de logotipo
DIR_COMPONENTE_MAPA = BASE_DIR / "components" / "mapa"

mapa_interativo = components.declare_component(
    "mapa_interativo",
    path=str(DIR_COMPONENTE_MAPA),
)

COMPETENCIA = "julho de 2026"
VERSAO = "protótipo v0.1"

ORGAO = "Secretaria de Desenvolvimento Social"
PROGRAMA = "SuperAção SP"
FONTE = "Fonte: SIGMA/SEDS-SP. Elaboração própria."
NOTA_SUPRESSAO = (
    "Células com menos de 5 famílias são omitidas. Municípios com menos de "
    "30 elegíveis ficam fora da comparação de taxas."
)

N_MIN_COMPARATIVO = 30

# --- Marcas ----------------------------------------------------------
# Ordem da assinatura conforme manual p. 19 e 21: os logos parceiros ficam à
# ESQUERDA e o logotipo do Governo SEMPRE à direita. A secretaria assina
# imediatamente à esquerda do logotipo do Governo.
# Nenhum logo parceiro pode ultrapassar 1,5X da largura do símbolo SP (p. 19).
LOGO_GOVERNO = DIR_MARCAS / "Brasão_do_estado_de_São_Paulo.svg"
LOGO_PARCEIROS: list[Path] = []

# =====================================================================
# IDENTIDADE VISUAL — valores do manual, p. 10
# =====================================================================

# Paleta principal
VERMELHO = "#FF161F"   # PANTONE 485 C
PRETO = "#000000"      # PANTONE BLACK
BRANCO = "#FFFFFF"
CINZA_50 = "#808080"
CINZA_25 = "#BFBFBF"

# Paleta secundária
AMARELO = "#FBB900"    # PANTONE 123 C
AZUL = "#034EA2"       # PANTONE 2955 C
VERDE = "#0B9247"      # PANTONE 347 C

# Papéis no painel.
# O vermelho é a cor da marca e fica reservado à identidade (barra, marcadores,
# traço de seção). Ele NÃO é usado como cor de alerta: num painel assinado pelo
# Governo, vermelho já significa "governo", e usá-lo também para "ruim" faz o
# leitor ler alarme onde só há cabeçalho. Atenção usa o amarelo da paleta
# secundária, que é o código de advertência sem competir com a marca.
COR_SERIE = AZUL
COR_POSITIVO = VERDE
COR_ATENCAO = AMARELO
COR_MARCA = VERMELHO

# Tipografia: o manual determina Verdana como fonte de sistema para comunicação
# institucional (assinatura de e-mail p. 24, papel timbrado p. 29, cartão p. 28).
FONTE_TIPO = "Verdana, Geneva, 'DejaVu Sans', sans-serif"

# Grid: 12 colunas com espaçamento de 30px em telas ≥1200px; 4 colunas
# em telas <576px (p. 26).
GUTTER = 30


def css() -> str:
    return f"""
<style>
:root {{
  --vermelho:{VERMELHO}; --preto:{PRETO}; --branco:{BRANCO};
  --cinza50:{CINZA_50}; --cinza25:{CINZA_25};
  --amarelo:{AMARELO}; --azul:{AZUL}; --verde:{VERDE};
  --serie:{COR_SERIE}; --gutter:{GUTTER}px;
}}

html, body, [class*="css"], .stMarkdown, .stApp {{
  font-family:{FONTE_TIPO};
}}
.stApp {{ background:var(--branco); }}

/* Cromo do Streamlit fora do caminho */
#MainMenu, footer {{ visibility:hidden; }}
header[data-testid="stHeader"] {{ visibility:visible; background:var(--branco); height:3.25rem; }}
.block-container {{ padding:3.25rem var(--gutter) 3rem; max-width:1400px; }}

/* ---------- Barra superior (assinatura institucional) ---------- */
.faixa {{
  background:var(--preto); margin:0 calc(-1 * var(--gutter)) 0;
  padding:14px var(--gutter); display:flex; align-items:center;
  justify-content:space-between; gap:24px; flex-wrap:wrap;
}}
.faixa-titulo {{
  color:var(--branco); font-size:19px; font-weight:bold;
  letter-spacing:.01em; margin:0; line-height:1.2;
}}
.faixa-sub {{ color:var(--cinza25); font-size:12px; margin:4px 0 0; }}

/* Régua de logotipos: parceiros à esquerda, Governo à direita (p. 19) */
.regua {{ display:flex; align-items:flex-end; gap:20px; }}
.regua-slot {{
  height:34px; min-width:78px; display:flex; align-items:center;
  justify-content:center; border:1px dashed rgba(255,255,255,.35);
  color:rgba(255,255,255,.55); font-size:10px; letter-spacing:.06em;
  padding:0 8px;
}}
.regua-slot img {{ height:30px; width:auto; }}
.regua-slot.com-logo {{ min-width:0; padding:0; border:0; }}   /* mínimo digital H=5px (p. 12) */
.assinatura-orgao {{
  color:var(--branco); font-size:12px; line-height:1.25;
  text-align:right; padding-bottom:2px;
}}
.assinatura-orgao b {{ display:block; font-size:13px; }}
.filete {{
  height:4px; background:var(--vermelho);
  margin:0 calc(-1 * var(--gutter)) 22px;
}}

/* ---------- Títulos de seção (traço curto do manual) ---------- */
.secao {{ margin:26px 0 14px; }}
.secao h2 {{
  font-size:14px; font-weight:bold; text-transform:uppercase;
  letter-spacing:.06em; margin:0; color:var(--preto);
}}
.secao .traco {{
  display:block; width:26px; height:4px;
  background:var(--vermelho); margin-top:8px;
}}

/* ---------- Selo de referência ---------- */
.selo {{
  background:var(--amarelo); padding:10px 16px; text-align:right;
  display:inline-block;
}}
.selo p {{ margin:0; color:var(--preto); }}
.selo .rot {{ font-size:10px; text-transform:uppercase; letter-spacing:.08em; }}
.selo .val {{ font-size:15px; font-weight:bold; margin-top:2px; }}
.selo .ger {{ font-size:10.5px; margin-top:2px; }}

/* ---------- Cartão de indicador ---------- */
.cartao {{
  border:1px solid var(--cinza25); padding:14px 16px; height:100%;
  background:var(--branco);
}}
.cartao .rot {{
  font-size:10.5px; text-transform:uppercase; letter-spacing:.07em;
  color:var(--cinza50); margin:0; min-height:26px;
}}
.cartao .val {{
  font-size:28px; font-weight:bold; margin:4px 0 0; color:var(--preto);
  font-variant-numeric:tabular-nums; letter-spacing:-.01em;
}}
.cartao .apoio {{ font-size:11.5px; color:var(--cinza50); margin:4px 0 0; }}

/* ---------- Barras ---------- */
.barra {{ display:flex; align-items:center; gap:14px; margin-bottom:9px; }}
.barra .rot {{ font-size:12px; width:160px; flex-shrink:0; color:var(--preto); }}
.barra .trilho {{ flex:1; height:22px; background:#F2F2F2; }}
.barra .fill {{ height:100%; background:var(--serie); }}
.barra .val {{
  font-size:12px; width:70px; text-align:right; flex-shrink:0;
  font-variant-numeric:tabular-nums;
}}

/* ---------- Tabela ---------- */
table.gesp {{
  width:100%; border-collapse:collapse; font-size:13px;
  font-variant-numeric:tabular-nums;
}}
table.gesp th {{
  text-align:left; font-size:10.5px; text-transform:uppercase;
  letter-spacing:.06em; color:var(--cinza50); font-weight:bold;
  padding:0 0 8px; border-bottom:2px solid var(--preto);
}}
table.gesp td {{ padding:9px 0; border-bottom:1px solid var(--cinza25); }}
table.gesp tr:last-child td {{ border-bottom:none; }}
.abaixo {{ color:#8A6600; font-weight:bold; }}
.abaixo::before {{
  content:""; display:inline-block; width:8px; height:8px;
  background:var(--amarelo); margin-right:6px; vertical-align:1px;
}}
.tenue {{ color:var(--cinza50); }}

/* ---------- Leitura e estado vazio ---------- */
.leitura {{ border-left:4px solid var(--preto); padding:10px 0 10px 14px; }}
.leitura p {{ margin:0; font-size:13.5px; }}
.vazio {{
  border:1px dashed var(--cinza25); padding:36px 24px; text-align:center;
}}
.vazio .msg {{ font-size:15px; font-weight:bold; margin:0; }}
.vazio .acao {{
  font-size:12.5px; color:var(--cinza50); margin:10px auto 0;
  max-width:54ch; line-height:1.6;
}}
.nota {{ font-size:11.5px; color:var(--cinza50); line-height:1.6; margin:12px 0 0; }}

/* ---------- Painel executivo do mapa ---------- */
.painel-executivo {{ border:1px solid #D9D9D9; border-top:5px solid var(--vermelho); padding:20px; background:#FFFFFF; min-height:590px; }}
.pe-eyebrow {{ font-size:10px; letter-spacing:.12em; font-weight:700; color:#666; text-transform:uppercase; }}
.painel-executivo h3 {{ font-size:21px; line-height:1.15; margin:5px 0 10px; color:#000; }}
.pe-badge {{ display:inline-block; background:#F2F2F2; color:#222; border-left:4px solid var(--amarelo); padding:5px 9px; font-size:11px; font-weight:700; }}
.pe-destaque {{ margin:18px 0 14px; padding-bottom:14px; border-bottom:1px solid #DDD; }}
.pe-destaque .rot {{ font-size:10px; color:#666; text-transform:uppercase; letter-spacing:.08em; }}
.pe-destaque .val {{ font-size:34px; font-weight:700; line-height:1.05; margin-top:3px; color:#000; }}
.pe-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:9px; margin:12px 0 16px; }}
.pe-kpi {{ background:#F5F5F5; padding:10px 11px; border-left:3px solid #034EA2; }}
.pe-kpi .rot {{ font-size:9.5px; color:#666; text-transform:uppercase; letter-spacing:.05em; min-height:24px; }}
.pe-kpi .val {{ font-size:19px; font-weight:700; color:#000; margin-top:2px; }}
.pe-barra {{ margin:9px 0; }}
.pe-barra .cab {{ display:flex; justify-content:space-between; font-size:11px; font-weight:700; color:#222; }}
.pe-barra .trilho {{ height:7px; background:#E5E5E5; margin-top:5px; }}
.pe-barra .fill {{ display:block; height:100%; background:#034EA2; }}
.pe-leitura {{ margin-top:16px; border-left:4px solid var(--preto); padding:9px 0 9px 11px; font-size:11.5px; color:#333; line-height:1.45; }}
.mapa-legenda {{ display:flex; gap:18px; align-items:center; font-size:10.5px; color:#555; margin:5px 0 0; }}
.mapa-legenda span::before {{ content:""; display:inline-block; width:11px; height:11px; margin-right:5px; vertical-align:-1px; }}
.mapa-legenda .contexto::before {{ background:#F3F3F3; border:1px solid #AAA; }}
.mapa-legenda .monitorado::before {{ background:#034EA2; }}
.mapa-legenda .selecionado::before {{ background:#FF161F; }}
/* ---------- Barra lateral ---------- */
section[data-testid="stSidebar"] {{ background:var(--preto); width:240px !important; }}
section[data-testid="stSidebar"] * {{ color:var(--branco); }}
section[data-testid="stSidebar"] [data-testid="stImage"] {{
  display:flex; justify-content:center; width:100%; margin:0 auto;
}}
section[data-testid="stSidebar"] [data-testid="stImage"] img {{ margin:0 auto; }}
section[data-testid="stSidebar"] .marca-slot {{
  height:74px; display:flex;
  align-items:center; justify-content:center; color:rgba(255,255,255,.55);
  font-size:10px; letter-spacing:.06em; margin-bottom:14px;
}}
section[data-testid="stSidebar"] .lat-orgao {{
  font-size:11.5px; color:var(--cinza25); line-height:1.35;
}}
section[data-testid="stSidebar"] .lat-programa {{
  font-size:17px; font-weight:bold; margin:2px 0 0; color:var(--branco);
}}
section[data-testid="stSidebar"] .lat-rotulo {{
  font-size:10px; text-transform:uppercase; letter-spacing:.09em;
  color:var(--cinza50); margin:22px 0 4px;
}}
/* Rádio como navegação, com marcador vermelho no item ativo */
section[data-testid="stSidebar"] div[role="radiogroup"] label {{
  padding:9px 10px; border-left:4px solid transparent; margin-bottom:2px;
  white-space:normal; line-height:1.3;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
  background:rgba(255,255,255,.07);
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
  border-left-color:var(--vermelho); background:rgba(255,255,255,.12);
}}
section[data-testid="stSidebar"] div[role="radiogroup"] input {{ display:none; }}
/* ---------- Subabas: contraste explícito no tema claro ---------- */
[data-testid="stTabs"] [role="tablist"],
div[data-baseweb="tab-list"] {{ background:var(--branco) !important; }}
[data-testid="stTabs"] [role="tab"],
[data-testid="stTabs"] [role="tab"] *,
div[data-baseweb="tab-list"] [role="tab"],
div[data-baseweb="tab-list"] [role="tab"] * {{
  color:#000000 !important; -webkit-text-fill-color:#000000 !important;
  opacity:1 !important; visibility:visible !important;
}}
[data-testid="stTabs"] [role="tab"],
div[data-baseweb="tab-list"] [role="tab"] {{
  background:#FFFFFF !important; font-weight:700 !important;
  border-bottom:4px solid #BFBFBF !important; padding:10px 15px !important;
}}
[data-testid="stTabs"] [role="tab"][aria-selected="true"],
div[data-baseweb="tab-list"] [role="tab"][aria-selected="true"] {{
  color:#000000 !important; background:#F2F2F2 !important;
  border-bottom-color:var(--vermelho) !important;
}}
[data-testid="stTabs"] [role="tabpanel"] {{
  color:#000000 !important; background:#FFFFFF !important;
}}
section[data-testid="stSidebar"] .lat-versao {{
  font-size:10.5px; color:var(--cinza50); margin-top:24px;
}}

@media (max-width:576px) {{      /* grid de 4 colunas, p. 26 */
  .block-container {{ padding-left:16px; padding-right:16px; }}
  .barra .rot {{ width:104px; }}
}}
</style>
"""


# =====================================================================
# FORMATAÇÃO
# =====================================================================

def num(v, casas=0) -> str:
    if v is None or pd.isna(v):
        return "—"
    s = f"{float(v):,.{casas}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def pct(v, casas=1) -> str:
    return "—" if v is None or pd.isna(v) else f"{num(v, casas)}%"


def taxa(a, b, casas=1) -> str:
    if not b or pd.isna(b) or pd.isna(a):
        return "—"
    return pct(100 * a / b, casas)


def marca_img(caminho: Path, alt: str, rotulo: str) -> str:
    """Logotipo embutido em base64, ou espaço reservado se o arquivo não existir."""
    if caminho.exists():
        mime = "image/svg+xml" if caminho.suffix == ".svg" else "image/png"
        b64 = base64.b64encode(caminho.read_bytes()).decode()
        return f'<div class="regua-slot com-logo"><img src="data:{mime};base64,{b64}" alt="{alt}"></div>'
    return f'<div class="regua-slot">{rotulo}</div>'


# =====================================================================
# COMPONENTES
# =====================================================================

def secao(titulo: str) -> None:
    st.markdown(
        f'<div class="secao"><h2>{titulo}</h2><span class="traco"></span></div>',
        unsafe_allow_html=True,
    )


def cartao(rotulo: str, valor: str, apoio: str = "") -> str:
    ap = f'<p class="apoio">{apoio}</p>' if apoio else ""
    return f'<div class="cartao"><p class="rot">{rotulo}</p><p class="val">{valor}</p>{ap}</div>'


def linha_cartoes(itens: list[tuple[str, str, str]], por_linha: int = 3) -> None:
    """Grid de 12 colunas: 3 cartões = 4 colunas cada (p. 26)."""
    for i in range(0, len(itens), por_linha):
        bloco = itens[i:i + por_linha]
        cols = st.columns(por_linha, gap="medium")
        for col, (rot, val, apoio) in zip(cols, bloco):
            col.markdown(cartao(rot, val, apoio), unsafe_allow_html=True)
        st.write("")


def barras(linhas: list[tuple[str, float]], total: float, opacidades=None) -> None:
    op = opacidades or [1.0] * len(linhas)
    html = []
    for (rot, val), o in zip(linhas, op):
        larg = 0 if not total else max(0.6, 100 * val / total)
        html.append(
            f'<div class="barra"><span class="rot">{rot}</span>'
            f'<span class="trilho"><span class="fill" style="width:{larg:.1f}%;opacity:{o}"></span></span>'
            f'<span class="val">{num(val)}</span></div>'
        )
    st.markdown("".join(html), unsafe_allow_html=True)


def tabela(df: pd.DataFrame, colunas: list[tuple[str, str, str]], larguras: list[str]) -> None:
    ths = "".join(
        f'<th style="width:{w};text-align:{a}">{c}</th>'
        for (_, c, a), w in zip(colunas, larguras)
    )
    trs = "".join(
        "<tr>" + "".join(f'<td style="text-align:{a}">{r[k]}</td>' for k, _, a in colunas) + "</tr>"
        for _, r in df.iterrows()
    )
    st.markdown(
        f'<table class="gesp"><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>',
        unsafe_allow_html=True,
    )

def grafico_barras_horizontais(df: pd.DataFrame, categoria: str, valor: str, titulo: str,
                                formato: str = ".1f", sufixo: str = "", cor: str = AZUL) -> None:
    """Ranking horizontal com valor direto, inspirado nos slides executivos."""
    base = df[[categoria, valor]].dropna().copy().sort_values(valor, ascending=False)
    base["rotulo_valor"] = base[valor].map(lambda v: f"{num(v, 1) if formato == '.1f' else num(v)}{sufixo}")
    maximo = float(base[valor].max()) if len(base) else 1
    barras_chart = alt.Chart(base).mark_bar(color=cor, cornerRadiusEnd=3, height=18).encode(
        y=alt.Y(f"{categoria}:N", sort="-x", title=None,
                axis=alt.Axis(labelLimit=260, labelFontSize=11, labelColor="#222")),
        x=alt.X(f"{valor}:Q", title=None, axis=None, scale=alt.Scale(domain=[0, maximo * 1.22])),
        tooltip=[alt.Tooltip(f"{categoria}:N", title="Categoria"),
                 alt.Tooltip(f"{valor}:Q", title="Valor", format=formato)],
    )
    rotulos = alt.Chart(base).mark_text(align="left", dx=6, fontSize=11, fontWeight="bold", color="#222").encode(
        y=alt.Y(f"{categoria}:N", sort="-x"), x=alt.X(f"{valor}:Q"), text="rotulo_valor:N"
    )
    chart = (barras_chart + rotulos).properties(title=alt.Title(titulo, fontSize=14, fontWeight="bold", anchor="start"),
                                                height=max(190, 31 * len(base)))
    st.altair_chart(chart.configure_view(strokeWidth=0).configure_axis(grid=False, domain=False, ticks=False), width="stretch")


def grafico_barras_agrupadas(df: pd.DataFrame, categoria: str, series: dict[str, str], titulo: str,
                              dominio: list[str] | None = None) -> None:
    """Compara duas ou mais taxas com a mesma escala e rótulos diretos."""
    base = df[[categoria, *series.keys()]].melt(id_vars=categoria, var_name="serie", value_name="valor")
    base["serie"] = base["serie"].map(series)
    cores = [AZUL, AMARELO, VERDE, VERMELHO][:len(series)]
    chart = alt.Chart(base).mark_bar(cornerRadiusEnd=2).encode(
        y=alt.Y(f"{categoria}:N", title=None, sort=alt.EncodingSortField(field="valor", op="max", order="descending"),
                axis=alt.Axis(labelLimit=245, labelFontSize=10.5)),
        x=alt.X("valor:Q", title="Percentual (%)", scale=alt.Scale(domain=dominio or [0, 100]),
                axis=alt.Axis(grid=True, gridColor="#E5E5E5")),
        yOffset=alt.YOffset("serie:N"),
        color=alt.Color("serie:N", title=None, scale=alt.Scale(domain=list(series.values()), range=cores),
                        legend=alt.Legend(orient="top")),
        tooltip=[alt.Tooltip(f"{categoria}:N"), alt.Tooltip("serie:N"), alt.Tooltip("valor:Q", format=".1f")],
    ).properties(title=alt.Title(titulo, fontSize=14, fontWeight="bold", anchor="start"),
                 height=max(220, 36 * df[categoria].nunique()))
    st.altair_chart(chart.configure_view(strokeWidth=0).configure_axis(domain=False, ticks=False), width="stretch")


def grafico_composicao(df: pd.DataFrame, categoria: str, series: dict[str, str], titulo: str) -> None:
    """Barras 100% empilhadas para composição dos estágios."""
    base = df[[categoria, *series.keys()]].melt(id_vars=categoria, var_name="serie", value_name="valor")
    base["serie"] = base["serie"].map(series)
    ordem = list(series.values())
    cores = [AZUL, VERDE, AMARELO, "#E07A2D", CINZA_50][:len(ordem)]
    chart = alt.Chart(base).mark_bar().encode(
        y=alt.Y(f"{categoria}:N", title=None, sort=alt.EncodingSortField(field="valor", op="sum", order="descending"),
                axis=alt.Axis(labelLimit=250, labelFontSize=10.5)),
        x=alt.X("valor:Q", stack="normalize", title="Composição (%)", axis=alt.Axis(format="%")),
        color=alt.Color("serie:N", title=None, sort=ordem, scale=alt.Scale(domain=ordem, range=cores),
                        legend=alt.Legend(orient="top", columns=3)),
        tooltip=[alt.Tooltip(f"{categoria}:N"), alt.Tooltip("serie:N"), alt.Tooltip("valor:Q", format=",.0f")],
    ).properties(title=alt.Title(titulo, fontSize=14, fontWeight="bold", anchor="start"),
                 height=max(220, 32 * df[categoria].nunique()))
    st.altair_chart(chart.configure_view(strokeWidth=0).configure_axis(domain=False, ticks=False), width="stretch")


def grafico_evolucao(df: pd.DataFrame, periodo: str, series: dict[str, str], titulo: str) -> None:
    """Série temporal com linhas e pontos, no estilo das projeções dos slides."""
    base = df[[periodo, *series.keys()]].melt(id_vars=periodo, var_name="serie", value_name="valor")
    base["serie"] = base["serie"].map(series)
    ordem = list(series.values())
    chart = alt.Chart(base).mark_line(point=alt.OverlayMarkDef(size=55), strokeWidth=3).encode(
        x=alt.X(f"{periodo}:O", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("valor:Q", title="Percentual (%)", scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(grid=True, gridColor="#E5E5E5")),
        color=alt.Color("serie:N", title=None, scale=alt.Scale(domain=ordem, range=[AZUL, AMARELO, VERDE]),
                        legend=alt.Legend(orient="top")),
        tooltip=[alt.Tooltip(f"{periodo}:O"), alt.Tooltip("serie:N"), alt.Tooltip("valor:Q", format=".1f")],
    ).properties(title=alt.Title(titulo, fontSize=14, fontWeight="bold", anchor="start"), height=310)
    st.altair_chart(chart.configure_view(strokeWidth=0).configure_axis(domain=False, ticks=False), width="stretch")

def nota(texto: str) -> None:
    st.markdown(f'<p class="nota">{texto}</p>', unsafe_allow_html=True)


def leitura(texto: str) -> None:
    st.markdown(f'<div class="leitura"><p>{texto}</p></div>', unsafe_allow_html=True)


def vazio(msg: str, acao: str = "") -> None:
    extra = f'<p class="acao">{acao}</p>' if acao else ""
    st.markdown(f'<div class="vazio"><p class="msg">{msg}</p>{extra}</div>', unsafe_allow_html=True)


# =====================================================================
# RELATÓRIOS
# =====================================================================

def rel_visao_geral(d: dict) -> None:
    f = d["funil"]
    f = f[f["data_ref"] == f["data_ref"].max()]
    t = d["tempos"]

    tot = {c: int(f[c].sum()) for c in f.columns if c.startswith("n_")}
    med = t.loc[t["etapa"] == "aceite_pactuacao", "p50"]
    med = med.median() if len(med) else None

    linha_cartoes([
        ("1 · Cobertura da busca ativa", taxa(tot["n_tentativa"], tot["n_elegivel"]),
         f'{num(tot["n_tentativa"])} de {num(tot["n_elegivel"])} elegíveis'),
        ("2 · Taxa de localização", taxa(tot["n_contato"], tot["n_tentativa"]),
         f'{num(tot["n_contato"])} contatos efetivos'),
        ("3 · Aceite do termo", taxa(tot["n_aceite"], tot["n_contato"]),
         f'{num(tot["n_aceite"])} famílias aceitaram'),
        ("4 · Conclusão do diagnóstico", taxa(tot["n_diag_fim"], tot["n_aceite"]),
         f'{num(tot["n_diag_fim"])} diagnósticos finalizados'),
        ("5 · Pactuação do PDF", taxa(tot["n_pdf_pactuado"], tot["n_diag_fim"]),
         f'{num(tot["n_pdf_pactuado"])} planos pactuados'),
        ("6 · Tempo até a pactuação", f"{num(med)} dias" if med else "—",
         "mediana do aceite ao plano"),
    ])

    secao("Onde as famílias saem do funil")
    barras(
        [("Elegíveis", tot["n_elegivel"]),
         ("Com tentativa", tot["n_tentativa"]),
         ("Contato efetivo", tot["n_contato"]),
         ("Termo aceito", tot["n_aceite"]),
         ("Diagnóstico final", tot["n_diag_fim"]),
         ("PDF pactuado", tot["n_pdf_pactuado"])],
        tot["n_elegivel"],
        opacidades=[1.0, 1.0, .82, .82, .62, .45],
    )
    nota(FONTE)


def rel_municipios(d: dict) -> None:
    f = d["funil"]
    f = f[f["data_ref"] == f["data_ref"].max()].copy().sort_values("n_elegivel", ascending=False)

    med_aceite = 100 * (f["n_aceite"] / f["n_contato"]).median()
    med_pact = 100 * (f["n_pdf_pactuado"] / f["n_diag_fim"]).median()

    def marcar(v, mediana):
        if pd.isna(v):
            return "—"
        return f'<span class="abaixo">{pct(v)}</span>' if v < mediana else pct(v)

    linhas = []
    for _, r in f.head(12).iterrows():
        pequeno = r["n_elegivel"] < N_MIN_COMPARATIVO
        a = 100 * r["n_aceite"] / r["n_contato"] if r["n_contato"] else float("nan")
        p = 100 * r["n_pdf_pactuado"] / r["n_diag_fim"] if r["n_diag_fim"] else float("nan")
        linhas.append({
            "municipio": f'<span class="tenue">{r["municipio"]}</span>' if pequeno else r["municipio"],
            "elegiveis": num(r["n_elegivel"]),
            "aceite": "—" if pequeno else marcar(a, med_aceite),
            "pactuacao": "—" if pequeno else marcar(p, med_pact),
        })

    linha_cartoes([
        ("Municípios com atividade", num((f["n_elegivel"] > 0).sum()), "de 645 no estado"),
        ("Concentração", taxa(f.nlargest(10, "n_elegivel")["n_elegivel"].sum(), f["n_elegivel"].sum()),
         "dos elegíveis nos 10 maiores"),
        ("Fora do comparativo", num((f["n_elegivel"] < N_MIN_COMPARATIVO).sum()),
         f"com menos de {N_MIN_COMPARATIVO} elegíveis"),
    ])

    secao("Maiores municípios por volume de elegíveis")
    tabela(
        pd.DataFrame(linhas),
        [("municipio", "Município", "left"), ("elegiveis", "Elegíveis", "right"),
         ("aceite", "Aceite", "right"), ("pactuacao", "Pactuação", "right")],
        ["40%", "20%", "20%", "20%"],
    )
    nota(
        f"Marcado em amarelo: abaixo da mediana estadual (aceite {pct(med_aceite)} · "
        f"pactuação {pct(med_pact)}). Ordenação por volume, não por desempenho. {FONTE}"
    )


def rel_recusas(d: dict) -> None:
    agg = (d["recusas"].groupby("categoria", as_index=False)["n"].sum()
           .sort_values("n", ascending=False))
    secao("Motivos declarados de recusa")
    barras(list(zip(agg["categoria"], agg["n"])), agg["n"].sum())
    nota(
        "Apenas categorias do menu suspenso do SIGMA. O campo de texto livre não entra "
        f"nesta contagem. {FONTE}"
    )


def rel_tempos(d: dict) -> None:
    t = d["tempos"]
    if t.empty:
        return vazio("Sem dados de tempo nesta competência.")
    nomes = {
        "tentativa_aceite": "Primeira visita → aceite",
        "aceite_diag_fim": "Aceite → diagnóstico final",
        "aceite_pactuacao": "Aceite → pactuação",
        "diag_fim_pactuacao": "Diagnóstico → pactuação",
    }
    agg = (t.groupby("etapa", as_index=False)
             .agg(p25=("p25", "median"), p50=("p50", "median"), p75=("p75", "median"), n=("n", "sum")))
    agg["etapa_nome"] = agg["etapa"].map(nomes).fillna(agg["etapa"])
    intervalo = alt.Chart(agg).mark_rule(color=AZUL, strokeWidth=7).encode(
        y=alt.Y("etapa_nome:N", title=None, sort=alt.EncodingSortField(field="p50", order="ascending"),
                axis=alt.Axis(labelLimit=260, labelFontSize=11)),
        x=alt.X("p25:Q", title="Dias", axis=alt.Axis(grid=True, gridColor="#E5E5E5")),
        x2="p75:Q",
        tooltip=[alt.Tooltip("etapa_nome:N", title="Etapa"), alt.Tooltip("p25:Q", title="p25", format=".0f"),
                 alt.Tooltip("p50:Q", title="Mediana", format=".0f"), alt.Tooltip("p75:Q", title="p75", format=".0f"),
                 alt.Tooltip("n:Q", title="Famílias", format=",.0f")],
    )
    mediana = alt.Chart(agg).mark_point(filled=True, size=105, color=VERMELHO, stroke="white", strokeWidth=1.5).encode(
        y=alt.Y("etapa_nome:N", sort=alt.EncodingSortField(field="p50", order="ascending")), x="p50:Q"
    )
    rotulo = alt.Chart(agg).mark_text(dx=9, align="left", fontWeight="bold", fontSize=11).encode(
        y=alt.Y("etapa_nome:N", sort=alt.EncodingSortField(field="p50", order="ascending")),
        x="p50:Q", text=alt.Text("p50:Q", format=".0f")
    )
    chart = (intervalo + mediana + rotulo).properties(
        title=alt.Title("Tempo entre etapas: intervalo interquartil e mediana", fontSize=14, fontWeight="bold", anchor="start"),
        height=max(230, 52 * len(agg)),
    )
    st.altair_chart(chart.configure_view(strokeWidth=0).configure_axis(domain=False, ticks=False), width="stretch")
    nota("A barra mostra do p25 ao p75; o ponto vermelho representa a mediana. " + FONTE)

def rel_qualidade(d: dict) -> None:
    q = d["qualidade"]
    tot = int(q["n_familias"].sum())
    linha_cartoes([
        ("Cadastro CadÚnico vencido", taxa(q["n_cadunico_desatual"].sum(), tot),
         f'{num(q["n_cadunico_desatual"].sum())} famílias há mais de 24 meses'),
        ("Sem data de atualização", taxa(q["n_cadunico_sem_data"].sum(), tot),
         f'{num(q["n_cadunico_sem_data"].sum())} famílias'),
        ("Divergência de responsável", taxa(q["n_divergencia_rf"].sum(), tot),
         "RF do SIGMA difere do CadÚnico"),
    ])
    secao("Por que isto importa")
    leitura(
        "Cadastro vencido compromete a elegibilidade e o cálculo de benefício. "
        "Divergência de responsável familiar indica que a família foi abordada por "
        "pessoa diferente da registrada no CadÚnico, o que afeta a validade do termo de aceite."
    )
    nota(FONTE)
def rel_completo_panorama(d: dict) -> None:
    x = d["relatorio_completo"]
    linha_cartoes([
        ("Famílias no relatório", num(x["n_familias"].sum()), f'{num(x["n_pessoas"].sum())} pessoas'),
        ("Municípios", num(x["municipio"].nunique()), "recorte territorial ativo"),
        ("Políticas públicas", num(x["n_politicas"].max()), f'{num(x["n_modulos"].max())} módulos'),
        ("Atividades", num(x["n_atividades"].sum()), f'{num(x["n_acoes"].sum())} ações registradas'),
    ], por_linha=4)
    secao("Onde se concentra a execução")
    grafico_barras_horizontais(x, "municipio", "n_atividades", "Atividades registradas por município", ".0f")
    leitura("A concentração territorial orienta onde volume, capacidade operacional e qualidade do acompanhamento devem ser lidos em conjunto.")


def rel_completo_pactuacao(d: dict) -> None:
    x = d["relatorio_completo"].copy()
    familias, pactuadas = int(x["n_familias"].sum()), int(x["n_pdfs_pactuados"].sum())
    mediana = (x["mediana_dias_pactuacao_atividade"] * x["n_pdfs_pactuados"]).sum() / max(pactuadas, 1)
    linha_cartoes([
        ("PDFs pactuados", num(pactuadas), taxa(pactuadas, familias) + " das famílias"),
        ("Ainda sem pactuação", num(familias - pactuadas), "estoque a acompanhar"),
        ("Pactuação → primeira atividade", f"{num(mediana)} dias", "mediana ponderada fictícia"),
    ])
    x["taxa_pactuacao"] = 100 * x["n_pdfs_pactuados"] / x["n_familias"]
    secao("Conversão territorial da pactuação")
    grafico_barras_horizontais(x, "municipio", "taxa_pactuacao", "Famílias com PDF pactuado", ".1f", "%")


def rel_completo_status(d: dict) -> None:
    x = d["relatorio_completo"]
    total = int(x["n_atividades"].sum())
    concluida = int(x["n_concluidas"].sum())
    andamento = int(x["n_andamento"].sum())
    atrasada = int(x["n_atrasadas"].sum())
    nao_iniciada = int(x["n_nao_iniciadas"].sum())
    linha_cartoes([
        ("Conclusão", taxa(concluida, total), f"{num(concluida)} atividades"),
        ("Em andamento", taxa(andamento, total), f"{num(andamento)} atividades"),
        ("Atrasadas", taxa(atrasada, total), f"{num(atrasada)} atividades"),
        ("Não iniciadas", taxa(nao_iniciada, total), f"{num(nao_iniciada)} atividades"),
    ], por_linha=4)
    secao("Status mais recente das atividades")
    barras([("Concluídas", concluida), ("Em andamento", andamento),
            ("Atrasadas", atrasada), ("Não iniciadas", nao_iniciada)], total)
    nota("Cada atividade entra uma vez, pelo status mais recente e sua respectiva data de atualização.")


def rel_completo_politicas(d: dict) -> None:
    x = d["dimensoes_completo"].copy()
    x["Conclusão"] = 100 * x["n_concluidas"] / x["n_atividades"]
    x["Atraso"] = 100 * x["n_atrasadas"] / x["n_atividades"]
    secao("Demanda × progresso")
    grafico_barras_agrupadas(x, "politica", {"Conclusão": "Conclusão", "Atraso": "Atraso"},
                             "Taxas por política pública")
    leitura("Políticas com grande demanda e atraso elevado devem ser priorizadas; taxa isolada não substitui a leitura do volume.")


def rel_completo_responsaveis(d: dict) -> None:
    x = d["relatorio_completo"]
    pessoa = int(x["n_resp_pessoa"].sum())
    estado = int(x["n_resp_estado"].sum())
    municipio = int(x["n_resp_municipio"].sum())
    total = pessoa + estado + municipio
    linha_cartoes([
        ("Responsabilidade da pessoa", taxa(pessoa, total), f"{num(pessoa)} atividades"),
        ("Responsabilidade estadual", taxa(estado, total), f"{num(estado)} atividades"),
        ("Responsabilidade municipal", taxa(municipio, total), f"{num(municipio)} atividades"),
        ("Responsável ausente", num(x["n_responsavel_ausente"].sum()), "registros para correção"),
    ], por_linha=4)
    secao("Distribuição do responsável pela ação")
    barras([("Pessoa/família", pessoa), ("Estado", estado), ("Município", municipio)], total)


def rel_completo_qualidade(d: dict) -> None:
    x = d["relatorio_completo"].copy()
    atividades = int(x["n_atividades"].sum())
    descricao = int(x["n_desc_preenchida"].sum())
    linha_cartoes([
        ("Descrição preenchida", taxa(descricao, atividades), f"{num(descricao)} atividades"),
        ("Sem data de status", num(x["n_status_sem_atualizacao"].sum()), "corrigir antes da análise temporal"),
        ("Sem responsável", num(x["n_responsavel_ausente"].sum()), "pendência operacional"),
        ("Sem agente registrador", num(x["n_agente_ausente"].sum()), "pendência de rastreabilidade"),
    ], por_linha=4)
    x["Sem data de status"] = 100 * x["n_status_sem_atualizacao"] / x["n_atividades"]
    x["Sem responsável"] = 100 * x["n_responsavel_ausente"] / x["n_atividades"]
    x["Sem agente"] = 100 * x["n_agente_ausente"] / x["n_atividades"]
    secao("Pendências que afetam a leitura")
    grafico_barras_agrupadas(x, "municipio", {"Sem data de status": "Sem data", "Sem responsável": "Sem responsável", "Sem agente": "Sem agente"},
                             "Percentual de registros com pendência", dominio=[0, max(8, float(x[["Sem data de status", "Sem responsável", "Sem agente"]].max().max()) * 1.2)])


def rel_completo_temporal(d: dict) -> None:
    x = d["relatorio_completo"].copy()
    x["Atualização do status"] = x["mediana_dias_status"]
    x["Início após pactuação"] = x["mediana_dias_pactuacao_atividade"]
    secao("Velocidade operacional")
    grafico_barras_agrupadas(x, "municipio", {"Atualização do status": "Registro → status", "Início após pactuação": "Pactuação → 1ª atividade"},
                             "Mediana de dias entre marcos", dominio=[0, max(35, float(x[["Atualização do status", "Início após pactuação"]].max().max()) * 1.2)])
    nota("Medianas fictícias calculadas apenas para pares de datas válidos.")


def rel_desinteresse(d: dict) -> None:
    x = d["desinteresse"].copy()
    prospectadas, sem_interesse = int(x["n_prospectadas"].sum()), int(x["n_sem_interesse"].sum())
    qualificadas = int(x["n_obs_qualificada"].sum())
    linha_cartoes([
        ("Famílias sem interesse", num(sem_interesse), taxa(sem_interesse, prospectadas) + " das prospectadas"),
        ("Observações qualificadas", taxa(qualificadas, sem_interesse), f"{num(qualificadas)} registros utilizáveis"),
        ("A requalificar", num((x["n_obs_generica"] + x["n_obs_insuficiente"]).sum()), "genéricos ou insuficientes"),
    ])
    x["Taxa sem interesse"] = 100 * x["n_sem_interesse"] / x["n_prospectadas"]
    x["Observação qualificada"] = 100 * x["n_obs_qualificada"] / x["n_sem_interesse"]
    secao("Volume, incidência e qualidade")
    grafico_barras_agrupadas(x, "municipio", {"Taxa sem interesse": "Sem interesse", "Observação qualificada": "Registro qualificado"},
                             "Desinteresse e qualidade do registro")


def rel_atividades_panorama(d: dict) -> None:
    x = d["atividades"]
    total = int(x["n_atividades"].sum())
    aplicaveis = total - int(x["n_sem_aplicaveis"].sum())
    concluidas = int(x["n_concluidas"].sum())
    andamento = int(x["n_em_andamento"].sum())
    espera = int((x["n_atrasadas"] + x["n_nao_iniciadas"]).sum())
    linha_cartoes([
        ("Atividades registradas", num(total), f"{num(aplicaveis)} aplicáveis"),
        ("Concluídas", taxa(concluidas, aplicaveis), f"{num(concluidas)} atividades"),
        ("Concluídas ou em andamento", taxa(concluidas + andamento, aplicaveis), "progresso observado"),
        ("Atrasadas ou não iniciadas", taxa(espera, aplicaveis), f"{num(espera)} atividades"),
    ], por_linha=4)
    secao("Composição do status")
    barras([("Concluídas", concluidas), ("Em andamento", andamento),
            ("Atrasadas", int(x["n_atrasadas"].sum())),
            ("Não iniciadas", int(x["n_nao_iniciadas"].sum()))], aplicaveis)


def rel_atividades_municipios(d: dict) -> None:
    x = d["atividades"].copy()
    secao("Composição da execução por município")
    grafico_composicao(x, "municipio", {"n_concluidas": "Concluídas", "n_em_andamento": "Em andamento",
                                         "n_atrasadas": "Atrasadas", "n_nao_iniciadas": "Não iniciadas"},
                       "Status das atividades aplicáveis")
    x["em_atencao"] = 100 * (x["n_atrasadas"] + x["n_nao_iniciadas"]) / (x["n_atividades"] - x["n_sem_aplicaveis"])
    grafico_barras_horizontais(x, "municipio", "em_atencao", "Atividades atrasadas ou não iniciadas", ".1f", "%", AMARELO)


def rel_politicas(d: dict) -> None:
    x = d["politicas"].copy()
    total = int(x["n_inclusoes"].sum())
    linha_cartoes([
        ("Inclusões nos PDFs", num(total), "política × família × ação"),
        ("Referência concluída", taxa(x["n_ref_concluida"].sum(), total), "marco intermediário"),
        ("Acesso efetivado", taxa(x["n_acesso_efetivado"].sum(), total), "última atividade concluída"),
        ("Com atividade atrasada", taxa(x["n_com_atraso"].sum(), total), "ponto de atenção"),
    ], por_linha=4)
    x["Referência concluída"] = 100 * x["n_ref_concluida"] / x["n_inclusoes"]
    x["Acesso efetivado"] = 100 * x["n_acesso_efetivado"] / x["n_inclusoes"]
    x["Com atraso"] = 100 * x["n_com_atraso"] / x["n_inclusoes"]
    secao("Progresso nas políticas mais demandadas")
    grafico_barras_agrupadas(x, "politica", {"Referência concluída": "Referência", "Acesso efetivado": "Acesso", "Com atraso": "Atraso"},
                             "Taxas por política pública")


def rel_coortes(d: dict) -> None:
    x = d["coortes"].copy()
    x["Acesso bruto"] = 100 * x["n_acessos"] / x["n_inclusoes"]
    x["Com atraso"] = 100 * x["n_atrasadas"] / x["n_inclusoes"]
    secao("Evolução por coorte de entrada")
    grafico_evolucao(x, "coorte", {"Acesso bruto": "Acesso bruto", "Com atraso": "Com atraso"},
                      "Maturidade e evolução das coortes")
    grafico_barras_horizontais(x, "coorte", "mediana_dias_acesso", "Mediana de dias até o acesso", ".0f", " dias", CINZA_50)
    nota("Coortes recentes tiveram menos tempo de exposição; a taxa bruta não deve ser interpretada como comparação causal.")


def rel_beneficios(d: dict) -> None:
    x = d["beneficios"].copy()
    linha_cartoes([
        ("Famílias beneficiárias", num(x["n_familias"].sum()), "pode haver sobreposição"),
        ("Pagamentos realizados", num(x["n_pagamentos"].sum()), "parcelas e pagamentos únicos"),
        ("Valor fictício executado", f'R$ {num(x["valor_total"].sum(), 2)}', "base demonstrativa"),
    ])
    secao("Cobertura dos benefícios")
    grafico_barras_horizontais(x, "beneficio", "cobertura_pct", "Famílias cobertas entre as aderidas", ".1f", "%")
    grafico_barras_horizontais(x, "beneficio", "lag_mediano_dias", "Defasagem até o primeiro pagamento", ".0f", " dias", CINZA_50)


def rel_pagamentos_municipios(d: dict) -> None:
    x = d["pagamentos_municipios"].copy()
    for origem, destino in [("n_compromisso", "Compromisso"), ("n_protecao_social", "Proteção social"),
                            ("n_ajuda_custo", "Ajuda de custo"), ("n_conclusao", "Conclusão")]:
        x[destino] = 100 * x[origem] / x["n_aderidas"]
    secao("Cobertura territorial dos benefícios")
    grafico_barras_agrupadas(x, "municipio", {"Compromisso": "Compromisso", "Proteção social": "Proteção social",
                                               "Ajuda de custo": "Ajuda de custo", "Conclusão": "Conclusão"},
                             "Percentual das famílias aderidas")


def rel_fluxo_beneficios(d: dict) -> None:
    x = d["beneficios"].sort_values("lag_mediano_dias")
    secao("Defasagem mediana até o primeiro pagamento")
    barras(list(zip(x["beneficio"], x["lag_mediano_dias"])), x["lag_mediano_dias"].max())
    nota("O tempo entre adesão ou elegibilidade e o primeiro pagamento ajuda a separar fila operacional de falha de cobertura.")

def rel_ebia(d: dict) -> None:
    vazio(
        "Relatório em construção.",
        "As classificações de insegurança alimentar apresentam variação entre meses "
        "compatível com artefato de cadastro. O relatório entra no painel quando a "
        "rotina de alertas estabilizar a série.",
    )


TIPOS_RELATORIO = [
    "Relatório SIGMA completo",
    "Relatório PDF Atividades",
    "Relatório PDF Estratégia",
    "Diagnóstico",
]

RELATORIOS_CONFIG = {
    "Relatório SIGMA completo": [
        ("Panorama", rel_completo_panorama),
        ("Pactuação", rel_completo_pactuacao),
        ("Status das atividades", rel_completo_status),
        ("Políticas e módulos", rel_completo_politicas),
        ("Responsáveis", rel_completo_responsaveis),
        ("Agentes e qualidade", rel_completo_qualidade),
        ("Tempos", rel_completo_temporal),
    ],
    "Relatório PDF Atividades": [
        ("Status das atividades", rel_atividades_panorama),
        ("Execução municipal", rel_atividades_municipios),
        ("Tempos do processo", rel_tempos),
        ("Qualidade da base", rel_qualidade),
    ],
    "Relatório PDF Estratégia": [
        ("Funil de acesso", rel_politicas),
        ("Políticas públicas", rel_politicas),
        ("Coortes e maturidade", rel_coortes),
        ("Território dos atrasos", rel_atividades_municipios),
    ],
    "Diagnóstico": [
        ("Panorama dos benefícios", rel_beneficios),
        ("Cobertura municipal", rel_pagamentos_municipios),
        ("Fluxo dos pagamentos", rel_fluxo_beneficios),
        ("Qualidade do diagnóstico", rel_qualidade),
    ],
}

OPCOES_NAVEGACAO = [*TIPOS_RELATORIO, "Nota Metodológica"]

NOTAS_METODOLOGICAS = {
    "Relatório SIGMA completo": {
        "Objetivo e unidade de análise": "Acompanha famílias, pessoas, PDFs e atividades registrados no SIGMA. A leitura municipal agrega os registros pelo município informado na base.",
        "Indicadores principais": "Conclusão corresponde às atividades concluídas sobre o total de atividades. Pactuação corresponde aos PDFs pactuados sobre o total de famílias. Tempos são apresentados por medianas para reduzir o efeito de valores extremos.",
        "Tratamento e cautelas": "Contagens dependem do preenchimento dos campos de município, status, responsável, agente e datas. Registros sem abertura municipal permanecem apenas nas análises consolidadas.",
    },
    "Relatório PDF Atividades": {
        "Objetivo e unidade de análise": "Monitora a execução das atividades previstas nos Planos de Desenvolvimento Familiar, com agregação por município e situação da atividade.",
        "Indicadores principais": "A base aplicável exclui atividades classificadas como não aplicáveis. Em atenção reúne atividades atrasadas e não iniciadas; conclusão usa atividades concluídas sobre a base aplicável.",
        "Tratamento e cautelas": "Datas e status inconsistentes podem afetar a classificação temporal. Resultados com denominador nulo são exibidos sem taxa e devem ser interpretados junto ao volume absoluto.",
    },
    "Relatório PDF Estratégia": {
        "Objetivo e unidade de análise": "Analisa o percurso entre elegibilidade, contato, aceite, diagnóstico, pactuação e acesso às políticas públicas previstas na estratégia.",
        "Indicadores principais": "Taxa de aceite usa aceites sobre contatos. Pactuação pós-diagnóstico usa PDFs pactuados sobre diagnósticos finalizados. Coortes organizam os resultados pelo período de entrada.",
        "Tratamento e cautelas": "As etapas possuem denominadores distintos e não devem ser comparadas como percentuais de uma mesma base. Competências recentes podem apresentar maturação incompleta.",
    },
    "Diagnóstico": {
        "Objetivo e unidade de análise": "Consolida benefícios, pagamentos e aspectos de qualidade do diagnóstico das famílias acompanhadas.",
        "Indicadores principais": "Coberturas municipais relacionam famílias contempladas em cada benefício às famílias aderidas. Defasagens são calculadas entre o marco de elegibilidade ou adesão e o primeiro pagamento.",
        "Tratamento e cautelas": "Uma família pode aparecer em mais de um benefício. Valores, competências e indicadores demonstrativos devem ser substituídos ou validados antes de divulgação externa.",
    },
}


def nota_metodologica() -> None:
    """Exibe uma subaba metodológica para cada tipo de relatório."""
    abas = st.tabs(TIPOS_RELATORIO)
    for aba, relatorio in zip(abas, TIPOS_RELATORIO):
        with aba:
            secao(relatorio)
            for titulo, texto in NOTAS_METODOLOGICAS[relatorio].items():
                st.markdown(f"#### {titulo}")
                st.write(texto)
            st.info(NOTA_SUPRESSAO)


def sincronizar_navegacao() -> None:
    """Mantém a seleção lateral coerente com os parâmetros usados pelo mapa."""
    escolha = st.session_state["navegacao_lateral"]
    if escolha in TIPOS_RELATORIO:
        st.query_params["relatorio"] = str(TIPOS_RELATORIO.index(escolha))
    else:
        st.query_params.pop("relatorio", None)
        st.query_params.pop("municipio", None)


def sincronizar_municipio(chave_relatorio: int, filtro_key: str) -> None:
    """Atualiza a URL quando o recorte territorial muda pelo seletor."""
    municipio = st.session_state[filtro_key]
    st.query_params["relatorio"] = str(chave_relatorio)
    if municipio == "Visão consolidada":
        st.query_params.pop("municipio", None)
    else:
        st.query_params["municipio"] = municipio

MARCADOR = {"atual": "●", "defasado": "◐", "pendente": "○"}

COORDENADAS_MUNICIPIOS = {
    "São Paulo": (-23.5505, -46.6333),
    "Guarulhos": (-23.4543, -46.5337),
    "Campinas": (-22.9056, -47.0608),
    "São Bernardo do Campo": (-23.6914, -46.5646),
    "Santo André": (-23.6639, -46.5383),
    "Osasco": (-23.5329, -46.7917),
    "Sorocaba": (-23.5015, -47.4526),
    "Ribeirão Preto": (-21.1704, -47.8103),
    "Santos": (-23.9608, -46.3336),
    "São José dos Campos": (-23.1896, -45.8841),
    "Registro": (-24.4979, -47.8449),
    "Borá": (-22.2691, -50.5409),
}


@st.cache_data(show_spinner=False)
def carregar_malhas() -> tuple[dict, dict, dict]:
    """Carrega contexto municipal, contorno estadual e recorte monitorado do IBGE."""
    contexto = json.loads((DIR_TABELAS / "municipios_sp_contexto.geojson").read_text(encoding="utf-8"))
    estado = json.loads((DIR_TABELAS / "estado_sp.geojson").read_text(encoding="utf-8"))
    monitorados = json.loads((DIR_TABELAS / "municipios_mock.geojson").read_text(encoding="utf-8"))
    return contexto, estado, monitorados


def _pontos_geometria(coordenadas):
    if coordenadas and isinstance(coordenadas[0], (int, float)):
        yield coordenadas
        return
    for parte in coordenadas:
        yield from _pontos_geometria(parte)


def _barra_executiva(rotulo: str, valor: float) -> str:
    largura = max(0, min(100, valor))
    return (
        f'<div class="pe-barra"><div class="cab"><span>{rotulo}</span>'
        f'<span>{pct(valor)}</span></div><div class="trilho">'
        f'<span class="fill" style="width:{largura:.1f}%"></span></div></div>'
    )


def mapa_municipal(d: dict, chave: str, municipio: str) -> str | None:
    """Mapa executivo de SP com contexto, zoom municipal e síntese decisória."""
    contexto_geo, estado_geo, monitorados_original = carregar_malhas()
    monitorados_geo = json.loads(json.dumps(monitorados_original))
    permitidos = {f["properties"]["municipio"] for f in monitorados_geo["features"]}

    if chave == "0":
        f = d["relatorio_completo"].copy()
        f["valor_mapa"] = f["n_atividades"]
        rotulo_mapa = "Atividades acompanhadas"
        total_base = f["n_atividades"]
        taxa_1 = 100 * f["n_concluidas"] / f["n_atividades"]
        taxa_2 = 100 * f["n_pdfs_pactuados"] / f["n_familias"]
    elif chave == "1":
        f = d["atividades"].copy()
        f["valor_mapa"] = f["n_atrasadas"] + f["n_nao_iniciadas"]
        rotulo_mapa = "Atividades que exigem atenção"
        total_base = f["n_atividades"] - f["n_sem_aplicaveis"]
        taxa_1 = 100 * f["n_concluidas"] / total_base
        taxa_2 = 100 * (f["n_atrasadas"] + f["n_nao_iniciadas"]) / total_base
    elif chave == "2":
        f = d["funil"]
        f = f[f["data_ref"] == f["data_ref"].max()].copy()
        f["valor_mapa"] = f["n_pdf_pactuado"]
        rotulo_mapa = "PDFs pactuados"
        total_base = f["n_elegivel"]
        taxa_1 = 100 * f["n_aceite"] / f["n_contato"]
        taxa_2 = 100 * f["n_pdf_pactuado"] / f["n_diag_fim"]
    else:
        f = d["pagamentos_municipios"].copy()
        cols_beneficios = ["n_compromisso", "n_protecao_social", "n_ajuda_custo", "n_conclusao"]
        f["valor_mapa"] = f[cols_beneficios].sum(axis=1)
        rotulo_mapa = "Coberturas de benefícios"
        total_base = f["n_aderidas"]
        taxa_1 = 100 * f["n_compromisso"] / f["n_aderidas"]
        taxa_2 = 100 * f["n_protecao_social"] / f["n_aderidas"]

    f = f[f["municipio"].isin(permitidos)].copy()
    f["taxa_1"] = taxa_1.loc[f.index]
    f["taxa_2"] = taxa_2.loc[f.index]
    f["total_base"] = total_base.loc[f.index]
    municipios_com_dados = set(f["municipio"].dropna())
    monitorados_geo["features"] = [
        feature for feature in monitorados_geo["features"]
        if feature["properties"]["municipio"] in municipios_com_dados
    ]
    selecionado = None if municipio == "Visão consolidada" else municipio

    valores = f.set_index("municipio")["valor_mapa"].to_dict()
    maximo = max(valores.values()) if valores else 1

    feicao_selecionada = None
    for feature in monitorados_geo["features"]:
        nome = feature["properties"]["municipio"]
        valor = float(valores.get(nome, 0))
        destaque = nome == selecionado
        proporcao = valor / maximo if maximo else 0
        r = int(181 + (3 - 181) * proporcao)
        g = int(211 + (78 - 211) * proporcao)
        b = int(230 + (162 - 230) * proporcao)
        feature["properties"].update({
            "valor_fmt": num(valor), "indicador": rotulo_mapa,
            "fill_hex": "#FF161F" if destaque else f"#{r:02X}{g:02X}{b:02X}",
            "line_width": 5 if destaque else 1.5,
        })
        if destaque:
            feicao_selecionada = feature

    if feicao_selecionada:
        pontos = list(_pontos_geometria(feicao_selecionada["geometry"]["coordinates"]))
        xs, ys = [p[0] for p in pontos], [p[1] for p in pontos]
        centro_lon, centro_lat = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        zoom = 9.4 if selecionado != "Campinas" else 8.9
    else:
        centro_lon, centro_lat, zoom = -48.65, -22.35, 6.05

    # Leaflet é carregado diretamente no componente HTML: nenhuma dependência Python extra.
    mapa_html = """<!doctype html>
<html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>html,body,#map{height:100%;margin:0;background:#fff}#map{background:#f7f7f7;border:1px solid #d8d8d8;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,.08)}
.leaflet-interactive:focus{outline:none}.leaflet-tooltip{font-family:Arial,sans-serif;font-size:12px}.map-title{background:rgba(255,255,255,.95);padding:10px 13px;border-left:4px solid #FF161F;box-shadow:0 1px 6px rgba(0,0,0,.18);font:700 12px Arial;color:#111}.map-title small{display:block;color:#666;font-weight:400;margin-top:3px}.map-scale{background:rgba(255,255,255,.95);padding:8px 10px;box-shadow:0 1px 6px rgba(0,0,0,.16);font:10px Arial;color:#444}.gradient{width:125px;height:8px;background:linear-gradient(90deg,#B5D3E6,#034EA2);margin:5px 0}.mun-label{background:rgba(255,255,255,.9);border:0;box-shadow:0 1px 3px rgba(0,0,0,.25);color:#111;font:700 10px Arial;padding:2px 5px;white-space:nowrap}</style></head>
<body><div id="map"></div><script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const contexto=__CONTEXTO__; const estado=__ESTADO__; const monitorados=__MONITORADOS__;
const selecionado=__SELECIONADO__; const chaveRelatorio=__CHAVE_RELATORIO__;
const map=L.map('map',{zoomControl:true,minZoom:5,maxZoom:13,zoomSnap:.25}).setView([__LAT__,__LON__],__ZOOM__);
const Title=L.Control.extend({onAdd:()=>{const d=L.DomUtil.create('div','map-title');d.innerHTML='PAINEL TERRITORIAL<small>Municípios monitorados · Governo de SP</small>';return d}});new Title({position:'topleft'}).addTo(map);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',{
 attribution:'&copy; OpenStreetMap &copy; CARTO',subdomains:'abcd',maxZoom:20
}).addTo(map);
L.geoJSON(contexto,{interactive:false,style:()=>({fill:false,fillOpacity:0,color:'#aeb4b8',weight:.55,opacity:.72})}).addTo(map);
L.geoJSON(estado,{interactive:false,style:()=>({fill:false,fillOpacity:0,color:'#202020',weight:2.4,opacity:1})}).addTo(map);
const foco=L.geoJSON(monitorados,{
 style:(f)=>{const ativo=f.properties.municipio===selecionado;return {fill:true,fillColor:f.properties.fill_hex,fillOpacity:ativo?.88:.78,color:ativo?'#000':'#fff',weight:ativo?5:1.5,opacity:1}},
 onEachFeature:(f,l)=>{l.bindTooltip('<b>'+f.properties.municipio+'</b><br>'+f.properties.indicador+': '+f.properties.valor_fmt+'<br><small>Clique para filtrar a análise</small>',{sticky:true});l.on('mouseover',()=>l.setStyle({weight:2,color:'#fff',fillOpacity:.88}));l.on('mouseout',()=>foco.resetStyle(l));l.on('click',()=>window.parent.postMessage({type:'municipio-selecionado',municipio:f.properties.municipio},'*'));}
}).addTo(map);
const Scale=L.Control.extend({onAdd:()=>{const d=L.DomUtil.create('div','map-scale');d.innerHTML='Menor volume<div class="gradient"></div>Maior volume';return d}});new Scale({position:'bottomright'}).addTo(map);
const labels=L.layerGroup().addTo(map);function atualizarRotulos(){labels.clearLayers();if(map.getZoom()<7)return;foco.eachLayer(l=>{const c=l.getBounds().getCenter();L.marker(c,{interactive:false,icon:L.divIcon({className:'mun-label',html:l.feature.properties.municipio,iconSize:null})}).addTo(labels)})}map.on('zoomend',atualizarRotulos);
if(selecionado){foco.eachLayer(l=>{if(l.feature.properties.municipio===selecionado){map.fitBounds(l.getBounds(),{padding:[34,34],maxZoom:10})}})}
else if(foco.getLayers().length){map.fitBounds(foco.getBounds(),{padding:[34,34],maxZoom:9})}else{map.fitBounds(L.geoJSON(estado).getBounds(),{padding:[14,14]})}atualizarRotulos();
</script></body></html>"""
    mapa_html = (mapa_html
        .replace("__CONTEXTO__", json.dumps(contexto_geo, ensure_ascii=False))
        .replace("__ESTADO__", json.dumps(estado_geo, ensure_ascii=False))
        .replace("__MONITORADOS__", json.dumps(monitorados_geo, ensure_ascii=False))
        .replace("__SELECIONADO__", json.dumps(selecionado, ensure_ascii=False))
        .replace("__CHAVE_RELATORIO__", json.dumps(chave))
        .replace("__LAT__", str(centro_lat)).replace("__LON__", str(centro_lon))
        .replace("__ZOOM__", str(zoom)))

    linha = f[f["municipio"] == selecionado] if selecionado else f
    valor_principal = linha["valor_mapa"].sum()
    base = linha["total_base"].sum()
    t1 = float((linha["taxa_1"] * linha["total_base"]).sum() / max(base, 1))
    t2 = float((linha["taxa_2"] * linha["total_base"]).sum() / max(base, 1))
    if selecionado:
        ranking = int(f["valor_mapa"].rank(method="min", ascending=False)[f["municipio"] == selecionado].iloc[0])
        situacao = "Atenção executiva" if (chave == "1" and t2 >= 30) or (chave != "1" and t1 < 40) else "Evolução acompanhada"
        leitura_exec = f"{ranking}º maior volume entre os {len(f)} municípios monitorados. Priorizar leitura conjunta de volume, taxa e capacidade operacional local."
    else:
        ranking = None
        situacao = "Visão consolidada do recorte"
        leitura_exec = f"Síntese dos {len(f)} municípios citados nas análises. Os demais municípios aparecem apenas como contexto territorial."

    if chave == "0":
        kpis = [("Famílias", num(linha["n_familias"].sum())), ("Pessoas", num(linha["n_pessoas"].sum())),
                ("Conclusão", pct(t1)), ("Pactuação", pct(t2))]
        bar1, bar2 = "Atividades concluídas", "PDFs pactuados"
    elif chave == "1":
        kpis = [("Aplicáveis", num(base)), ("Concluídas", num(linha["n_concluidas"].sum())),
                ("Conclusão", pct(t1)), ("Em atenção", pct(t2))]
        bar1, bar2 = "Conclusão", "Atrasadas/não iniciadas"
    elif chave == "2":
        kpis = [("Elegíveis", num(linha["n_elegivel"].sum())), ("Aceites", num(linha["n_aceite"].sum())),
                ("Taxa de aceite", pct(t1)), ("Pactuação pós-diagnóstico", pct(t2))]
        bar1, bar2 = "Aceite após contato", "Pactuação após diagnóstico"
    else:
        kpis = [("Aderidas", num(linha["n_aderidas"].sum())), ("Compromisso", num(linha["n_compromisso"].sum())),
                ("Cobertura compromisso", pct(t1)), ("Proteção social", pct(t2))]
        bar1, bar2 = "Incentivo ao compromisso", "Proteção social"

    kpis_html = "".join(f'<div class="pe-kpi"><div class="rot">{r}</div><div class="val">{v}</div></div>' for r, v in kpis)
    titulo = selecionado or "Estado de São Paulo"
    painel = (
        f'<div class="painel-executivo"><div class="pe-eyebrow">Síntese executiva</div><h3>{titulo}</h3>'
        f'<span class="pe-badge">{situacao}</span><div class="pe-destaque"><div class="rot">{rotulo_mapa}</div>'
        f'<div class="val">{num(valor_principal)}</div></div><div class="pe-grid">{kpis_html}</div>'
        f'{_barra_executiva(bar1, t1)}{_barra_executiva(bar2, t2)}'
        f'<div class="pe-leitura"><b>Leitura para decisão.</b> {leitura_exec}</div></div>'
    )

    mapa_col, resumo_col = st.columns([2.05, 1], gap="large")
    with mapa_col:
        municipio_clicado = mapa_interativo(
            html=mapa_html,
            height=590,
            default=None,
            key=f"mapa_municipal_{chave}",
        )

        st.markdown('<div class="mapa-legenda"><span class="contexto">Contexto estadual</span>'
                    '<span class="monitorado">Município monitorado</span>'
                    '<span class="selecionado">Município em foco</span></div>', unsafe_allow_html=True)
    with resumo_col:
        st.markdown(painel, unsafe_allow_html=True)

    return municipio_clicado

# =====================================================================
# DADOS
# =====================================================================

@st.cache_data(show_spinner=False)
def carregar(dir_tabelas: str) -> dict[str, pd.DataFrame]:
    p = Path(dir_tabelas)
    nomes = ["funil", "tempos", "recusas", "qualidade", "desinteresse", "atividades",
             "politicas", "coortes", "beneficios", "pagamentos_municipios",
             "relatorio_completo", "dimensoes_completo"]
    return {n: pd.read_csv(p / f"{n}.csv") for n in nomes}

def filtrar_dados_municipio(dados: dict[str, pd.DataFrame], municipio: str | None) -> dict[str, pd.DataFrame]:
    """Aplica o mesmo recorte às tabelas que possuem abertura municipal."""
    if not municipio:
        return dados
    filtrados: dict[str, pd.DataFrame] = {}
    for nome, df in dados.items():
        if "municipio" in df.columns:
            recorte = df[df["municipio"] == municipio].copy()
            filtrados[nome] = recorte if not recorte.empty else df
        else:
            filtrados[nome] = df
    return filtrados

# =====================================================================
# APLICAÇÃO
# =====================================================================

def main() -> None:
    st.set_page_config(
        page_title=f"{PROGRAMA} — painel de acompanhamento",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(css(), unsafe_allow_html=True)

    relatorio_param = st.query_params.get("relatorio")
    if relatorio_param is not None and str(relatorio_param).isdigit():
        indice_relatorio = int(relatorio_param)
        if 0 <= indice_relatorio < len(TIPOS_RELATORIO):
            st.session_state["navegacao_lateral"] = TIPOS_RELATORIO[indice_relatorio]

    # ---------- Barra lateral: tipos de relatório ----------
    with st.sidebar:
        st.image(str(LOGO_GOVERNO), width=100)
        st.markdown(
            f'<p class="lat-orgao">{ORGAO}</p>'
            f'<p class="lat-programa">{PROGRAMA}</p>'
            '<p class="lat-rotulo">Tipos de relatório</p>',
            unsafe_allow_html=True,
        )
        tipo_relatorio = st.radio(
            "Tipos de relatório",
            options=OPCOES_NAVEGACAO,
            key="navegacao_lateral",
            on_change=sincronizar_navegacao,
            label_visibility="collapsed",
        )
        st.markdown(
            '<p class="lat-rotulo">Situação do dado</p>'
            '<p class="lat-orgao">● competência atual<br>'
            '◐ competência anterior<br>○ ainda não disponível</p>'
            f'<p class="lat-versao">{VERSAO}</p>',
            unsafe_allow_html=True,
        )

    # ---------- Assinatura institucional ----------
    parceiros = "".join(marca_img(p, "logotipo parceiro", "PARCEIRO") for p in LOGO_PARCEIROS)
    governo = marca_img(LOGO_GOVERNO, "São Paulo — Governo do Estado", "LOGOTIPO SP")
    st.markdown(
        f'<div class="faixa">'
        f'  <div><p class="faixa-titulo">{tipo_relatorio}</p>'
        f'     <p class="faixa-sub">{PROGRAMA} · acompanhamento da busca ativa</p></div>'
        f'  <div class="regua">{parceiros}'
        f'     <div class="assinatura-orgao">Secretaria de<b>Desenvolvimento Social</b></div>'
        f'     {governo}</div>'
        f'</div><div class="filete"></div>',
        unsafe_allow_html=True,
    )

    # ---------- Selo de referência ----------
    _, dir_ = st.columns([3, 1], gap="medium")
    with dir_:
        st.markdown(
            f'<div class="selo"><p class="rot">Dados de referência</p>'
            f'<p class="val">{COMPETENCIA}</p>'
            f'<p class="ger">painel gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}</p></div>',
            unsafe_allow_html=True,
        )

    if tipo_relatorio == "Nota Metodológica":
        nota_metodologica()
        nota("Documento de uso interno. A metodologia deve ser revista quando houver alteração nas fontes, regras de negócio ou periodicidade.")
        return

    try:
        dados = carregar(str(DIR_TABELAS))
    except Exception as e:
        vazio(
            "Tabelas da camada agregada não encontradas.",
            f"Esperado em {DIR_TABELAS.resolve()} — {type(e).__name__}: {e}",
        )
        return

    # O recorte territorial é único e vale para todas as subabas com abertura municipal.
    chave_relatorio = TIPOS_RELATORIO.index(tipo_relatorio)
    _, _, malha_monitorada = carregar_malhas()
    municipios = sorted(f["properties"]["municipio"] for f in malha_monitorada["features"])
    filtro_key = f"filtro_global_{chave_relatorio}"
    municipio_param = st.query_params.get("municipio")
    if municipio_param in municipios:
        st.session_state[filtro_key] = municipio_param
    filtro_municipio = st.selectbox(
        "Recorte territorial",
        ["Visão consolidada", *municipios],
        key=filtro_key,
        on_change=sincronizar_municipio,
        args=(chave_relatorio, filtro_key),
        help="O filtro é aplicado ao mapa, cartões e tabelas que possuem dados municipais. Também é possível selecionar clicando no mapa.",
    )
    municipio_selecionado = None if filtro_municipio == "Visão consolidada" else filtro_municipio
    dados_filtrados = filtrar_dados_municipio(dados, municipio_selecionado)
    if municipio_selecionado:
        st.caption(f"Recorte ativo: {municipio_selecionado}. Seções sem abertura municipal permanecem consolidadas.")

    secoes_relatorio = RELATORIOS_CONFIG[tipo_relatorio]
    nomes_abas = ["Mapa municipal", *[titulo for titulo, _ in secoes_relatorio]]
    abas = st.tabs(nomes_abas)

    with abas[0]:
        municipio_clicado = mapa_municipal(dados, str(chave_relatorio), filtro_municipio)
        if municipio_clicado in municipios and municipio_clicado != filtro_municipio:
            st.query_params["relatorio"] = str(chave_relatorio)
            st.query_params["municipio"] = municipio_clicado
            st.rerun()

    for aba, (_, fn_secao) in zip(abas[1:], secoes_relatorio):
        with aba:
            try:
                fn_secao(dados_filtrados)
            except Exception as e:
                vazio("Não foi possível montar esta seção.", f"{type(e).__name__}: {e}")

    nota(NOTA_SUPRESSAO + " Documento de uso interno. Não contém dados pessoais.")

if __name__ == "__main__":
    main()
