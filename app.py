"""
SELU - Optimizacion de Minimos de Stock
App web para supervisoras de locales
"""
import streamlit as st
import pandas as pd
import numpy as np
import math
import warnings
from datetime import datetime
from io import BytesIO
from scipy.stats import norm

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="SELU - Stock",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════════════════
# ESTILOS
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* Paleta SELU: rosa, nude, negro, blanco */
    :root {
        --selu-rosa: #e9a5b2;
        --selu-rosa-claro: #fff4f4;
        --selu-rosa-medio: #ffedea;
        --selu-salmon: #ff9e8b;
        --selu-nude: #d7c5b7;
        --selu-negro: #3f3f40;
        --selu-gris: #796161;
    }

    .block-container {padding-top: 1rem;}

    /* Metricas con borde rosa */
    .stMetric {
        background: var(--selu-rosa-claro);
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid var(--selu-rosa);
    }
    div[data-testid="stMetricValue"] {font-size: 1.8rem; color: var(--selu-negro);}
    div[data-testid="stMetricLabel"] {color: var(--selu-gris);}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .stTabs [data-baseweb="tab"] {padding: 8px 16px; font-weight: 600;}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: var(--selu-negro);
        border-bottom-color: var(--selu-rosa);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: var(--selu-rosa-claro);
    }
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--selu-negro);
    }

    /* Botones */
    .stButton > button {
        background-color: var(--selu-negro);
        color: white;
        border: none;
        border-radius: 6px;
    }
    .stButton > button:hover {
        background-color: var(--selu-gris);
        color: white;
    }

    /* Download button */
    .stDownloadButton > button {
        background-color: var(--selu-rosa);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
    }
    .stDownloadButton > button:hover {
        background-color: var(--selu-salmon);
        color: white;
    }

    /* Headers */
    h1, h2, h3 {color: var(--selu-negro);}

    /* Links */
    a {color: var(--selu-rosa);}

    /* Expanders */
    .streamlit-expanderHeader {
        color: var(--selu-negro);
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

PASSWORD = "SELU2026"

# ═══════════════════════════════════════════════════════════════
# 1. LOGIN
# ═══════════════════════════════════════════════════════════════
def render_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 40px 0 20px 0;">
            <h1 style="color: #3f3f40; font-weight: 300; letter-spacing: 4px; margin-bottom: 5px;">SELU</h1>
            <p style="color: #e9a5b2; font-size: 14px; letter-spacing: 2px;">OPTIMIZACION DE STOCK</p>
        </div>
        """, unsafe_allow_html=True)
        pwd = st.text_input("Contrasena", type="password", key="pwd_input", placeholder="Ingrese su contrasena")
        if st.button("Ingresar", use_container_width=True):
            if pwd == PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Contrasena incorrecta")

# ═══════════════════════════════════════════════════════════════
# 2. SIDEBAR
# ═══════════════════════════════════════════════════════════════
def render_sidebar():
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <h2 style="font-weight: 300; letter-spacing: 3px; color: #3f3f40; margin-bottom: 0;">SELU</h2>
        <p style="color: #e9a5b2; font-size: 11px; letter-spacing: 2px; margin-top: 0;">GESTION DE STOCK</p>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.markdown("---")

    st.sidebar.markdown("### 📁 Archivos")
    file_min = st.sidebar.file_uploader("Minimos (.xls)", type=["xls", "xlsx"], key="f_min")
    file_vta = st.sidebar.file_uploader("Ventas (.xls)", type=["xls", "xlsx"], key="f_vta")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Parametros")

    with st.sidebar.expander("Reposicion", expanded=False):
        lead_time = st.number_input("Lead time (dias)", min_value=1, max_value=60, value=10, key="p_lt")
        service_level = st.slider("Service level (%)", min_value=80, max_value=99, value=95, key="p_sl")
        buffer_min = st.number_input("Buffer minimo (dias)", min_value=0, max_value=10, value=2, key="p_buf")

    with st.sidebar.expander("Umbrales de cobertura", expanded=False):
        umbral_sobre = st.number_input("Sobrestock (dias >)", min_value=10, max_value=90, value=20, key="p_us")
        umbral_riesgo = st.number_input("Riesgo (dias <)", min_value=5, max_value=30, value=12, key="p_ur")

    with st.sidebar.expander("Analisis de demanda", expanded=False):
        meses_vpd = st.number_input("Meses para VPD", min_value=3, max_value=24, value=12, key="p_mv")
        meses_reciente = st.number_input("Meses 'venta reciente'", min_value=1, max_value=12, value=3, key="p_mr")

    with st.sidebar.expander("Reglas de negocio", expanded=False):
        min_sin_demanda = st.number_input("Minimo sin demanda (muestra)", min_value=0, max_value=5, value=1, key="p_msd")
        abc_a = st.number_input("ABC clase A (% fact acum)", min_value=50, max_value=95, value=80, key="p_abc_a")
        abc_b = st.number_input("ABC clase B (% fact acum)", min_value=85, max_value=99, value=95, key="p_abc_b")

    return {
        "file_min": file_min, "file_vta": file_vta,
        "lead_time": lead_time, "service_level": service_level / 100,
        "buffer_min": buffer_min, "umbral_sobre": umbral_sobre,
        "umbral_riesgo": umbral_riesgo, "meses_vpd": meses_vpd,
        "meses_reciente": meses_reciente, "min_sin_demanda": min_sin_demanda,
        "abc_a": abc_a, "abc_b": abc_b,
    }

# ═══════════════════════════════════════════════════════════════
# 3. CARGA DE DATOS
# ═══════════════════════════════════════════════════════════════
@st.cache_data
def load_minimos(file_bytes):
    xls = pd.ExcelFile(BytesIO(file_bytes), engine="xlrd")
    # Tomar la primera hoja que tenga datos de minimos
    df = None
    for sheet in xls.sheet_names:
        tmp = pd.read_excel(xls, sheet_name=sheet, dtype=str)
        if len(tmp.columns) >= 10:
            if df is None:
                df = tmp
            else:
                df = pd.concat([df, tmp], ignore_index=True)

    if df is None or len(df) == 0:
        return pd.DataFrame()

    # Asignar nombres por posicion
    # El XLS puede tener 12 o 13 columnas (col 6 extra = "VIGENTE")
    cols = list(df.columns)
    col_map = {}
    if len(cols) >= 13:
        col_map = {cols[0]: "base_datos", cols[1]: "articulo", cols[2]: "color",
                   cols[3]: "color_desc", cols[4]: "talle", cols[5]: "vigencia",
                   cols[6]: "vigente_flag", cols[7]: "cantidad", cols[8]: "minimo_rep",
                   cols[9]: "maximo_rep", cols[10]: "diferencia", cols[11]: "base_modif",
                   cols[12]: "numero"}
    elif len(cols) >= 12:
        col_map = {cols[0]: "base_datos", cols[1]: "articulo", cols[2]: "color",
                   cols[3]: "color_desc", cols[4]: "talle", cols[5]: "vigencia",
                   cols[6]: "cantidad", cols[7]: "minimo_rep", cols[8]: "maximo_rep",
                   cols[9]: "diferencia", cols[10]: "base_modif", cols[11]: "numero"}
    df = df.rename(columns=col_map)

    for c in ["articulo", "color_desc", "talle", "base_datos"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()

    df["color_desc"] = df["color_desc"].fillna("")
    df["talle"] = df["talle"].fillna("")

    # Filtrar subtotales
    df = df[(df["color_desc"] != "") & (df["talle"] != "") &
            (df["color_desc"] != "nan") & (df["talle"] != "nan")]

    # SKU
    df["sku"] = df["articulo"] + "|" + df["color_desc"] + "|" + df["talle"]

    # Numericos
    for c in ["cantidad", "minimo_rep"]:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", ""), errors="coerce").fillna(0)

    df["local"] = df["base_datos"]

    # Vigentes
    df = df[(df["minimo_rep"] > 0) | (df["cantidad"] > 0)].copy()

    return df

@st.cache_data
def load_ventas(file_bytes):
    xls = pd.ExcelFile(BytesIO(file_bytes), engine="xlrd")
    frames = []

    for sheet in xls.sheet_names:
        tmp = pd.read_excel(xls, sheet_name=sheet, dtype=str)
        if len(tmp.columns) < 4:
            continue
        # Verificar que parece datos de ventas (tiene "Mes" en alguna celda de fecha)
        cols = list(tmp.columns)
        tmp = tmp.rename(columns={
            cols[0]: "articulo", cols[1]: "color_desc", cols[2]: "talle",
            cols[3]: "fecha", cols[4]: "cantidad_str",
            cols[5]: "total_str" if len(cols) > 5 else "extra"
        })
        frames.append(tmp)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    df["fecha"] = df["fecha"].astype(str).str.strip()
    # Extraer anio y mes
    df["anio"] = df["fecha"].str.extract(r"(\d{4})")
    df["mes"] = df["fecha"].str.extract(r"[Mm]es\s+(\d{2})")
    df = df.dropna(subset=["anio", "mes"])
    df["anio"] = df["anio"].astype(int)
    df["mes"] = df["mes"].astype(int)
    df["periodo"] = pd.to_datetime(df["anio"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2) + "-01")

    for c in ["articulo", "color_desc", "talle"]:
        df[c] = df[c].astype(str).str.strip()

    df["sku"] = df["articulo"] + "|" + df["color_desc"] + "|" + df["talle"]
    df["cantidad"] = pd.to_numeric(df["cantidad_str"].astype(str).str.replace(",", ""), errors="coerce").fillna(0)
    df["total"] = pd.to_numeric(df.get("total_str", pd.Series(dtype=str)).astype(str).str.replace(",", ""), errors="coerce").fillna(0)

    return df

# ═══════════════════════════════════════════════════════════════
# 4. ANALISIS PRINCIPAL
# ═══════════════════════════════════════════════════════════════
def run_analysis(df_min, df_vta, p):
    z_score = norm.ppf(p["service_level"])
    results = {}

    # --- Locales disponibles ---
    locales = sorted(df_min["local"].unique())
    results["locales"] = locales

    # --- VPD ultimos N meses ---
    fecha_max = df_vta["periodo"].max()
    fecha_corte = fecha_max - pd.DateOffset(months=p["meses_vpd"] - 1)
    df_rec = df_vta[df_vta["periodo"] >= fecha_corte].copy()
    total_meses = df_rec["periodo"].nunique()

    agg_vpd = df_rec.groupby("sku").agg(uds_periodo=("cantidad", "sum")).reset_index()
    agg_vpd["vpd"] = agg_vpd["uds_periodo"] / (total_meses * 30)

    # Desvio
    df_rec["dias_mes"] = df_rec["periodo"].dt.days_in_month
    df_rec["vpd_mes"] = df_rec["cantidad"] / df_rec["dias_mes"]
    agg_std = df_rec.groupby("sku").agg(
        vpd_media=("vpd_mes", "mean"), vpd_std=("vpd_mes", "std"),
        n_meses=("vpd_mes", "count")
    ).reset_index()
    agg_std["vpd_std"] = agg_std["vpd_std"].fillna(agg_std["vpd_media"] * 0.5)

    def adj_std(row):
        n_con = row["n_meses"]
        n_sin = total_meses - n_con
        if n_sin <= 0:
            return row["vpd_std"]
        mc = row["vpd_media"]
        vc = row["vpd_std"] ** 2 if n_con > 1 else (mc * 0.5) ** 2
        nt = n_con + n_sin
        return math.sqrt((n_con * vc + n_con * n_sin * mc ** 2 / nt) / nt)

    agg_std["vpd_std_adj"] = agg_std.apply(adj_std, axis=1)

    # Historico completo
    agg_hist = df_vta.groupby("sku").agg(
        uds_total=("cantidad", "sum"),
        facturacion=("total", "sum"),
        meses_venta=("cantidad", "count")
    ).reset_index()

    # Ventas recientes
    fecha_reciente = fecha_max - pd.DateOffset(months=p["meses_reciente"] - 1)
    df_ult = df_vta[df_vta["periodo"] >= fecha_reciente]
    skus_recientes = set(df_ult[df_ult["cantidad"] > 0]["sku"].unique())

    # --- MERGE ---
    df = df_min[["local", "sku", "articulo", "color_desc", "talle", "minimo_rep", "cantidad"]].copy()
    df = df.rename(columns={"minimo_rep": "minimo_actual", "cantidad": "stock_actual"})

    df = df.merge(agg_vpd[["sku", "vpd"]], on="sku", how="left")
    df = df.merge(agg_std[["sku", "vpd_std_adj"]], on="sku", how="left")
    df = df.merge(agg_hist[["sku", "uds_total", "facturacion", "meses_venta"]], on="sku", how="left")

    df["vpd"] = df["vpd"].fillna(0)
    df["vpd_std_adj"] = df["vpd_std_adj"].fillna(0)
    df["uds_total"] = df["uds_total"].fillna(0).astype(int)
    df["facturacion"] = df["facturacion"].fillna(0)
    df["meses_venta"] = df["meses_venta"].fillna(0).astype(int)
    df["vendio_reciente"] = df["sku"].isin(skus_recientes).map({True: "SI", False: "NO"})

    # --- Minimo optimo ---
    df["ss"] = df.apply(
        lambda r: max(r["vpd"] * r["vpd_std_adj"] * z_score, r["vpd"] * p["buffer_min"]) if r["vpd"] > 0 else 0,
        axis=1
    )
    df["minimo_optimo"] = (df["vpd"] * p["lead_time"] + df["ss"]).apply(
        lambda x: max(math.ceil(x), 1) if x > 0 else 0
    )
    df.loc[df["vpd"] == 0, "minimo_optimo"] = p["min_sin_demanda"]
    df["delta"] = df["minimo_optimo"] - df["minimo_actual"]

    # --- Dias para vender excedente (sin devolver, esperar a que se venda) ---
    # Usar VPD historico completo (mas representativo que ultimos N meses)
    fecha_min = df_vta["periodo"].min()
    dias_historico = max((fecha_max - fecha_min).days, 30)
    agg_vpd_hist = df_vta.groupby("sku").agg(uds_hist=("cantidad", "sum")).reset_index()
    agg_vpd_hist["vpd_hist"] = agg_vpd_hist["uds_hist"] / dias_historico
    df = df.merge(agg_vpd_hist[["sku", "vpd_hist"]], on="sku", how="left")
    df["vpd_hist"] = df["vpd_hist"].fillna(0)

    def dias_vender_excedente(row):
        excedente = row["stock_actual"] - row["minimo_optimo"]
        if excedente <= 0:
            return 0
        if row["vpd_hist"] <= 0:
            return 9999  # no se vende
        return round(excedente / row["vpd_hist"])

    df["dias_vender_excedente"] = df.apply(dias_vender_excedente, axis=1)

    # --- Estado ---
    def clasificar(row):
        if row["vpd"] == 0:
            if row["minimo_actual"] > p["min_sin_demanda"]:
                return "SIN DEMANDA (sobrestock)"
            elif row["minimo_actual"] == p["min_sin_demanda"]:
                return "SIN DEMANDA (optimo)"
            else:
                return "SIN DEMANDA (falta muestra)"
        cob = row["minimo_actual"] / row["vpd"]
        if cob > p["umbral_sobre"]:
            return "SOBRESTOCK"
        if cob < p["umbral_riesgo"]:
            return "RIESGO"
        return "OPTIMO"

    df["estado"] = df.apply(clasificar, axis=1)

    # --- ABC ---
    abc = df.groupby("articulo").agg(fact=("facturacion", "sum")).reset_index()
    abc = abc.sort_values("fact", ascending=False)
    abc["fact_acum"] = abc["fact"].cumsum()
    total_fact = abc["fact"].sum()
    abc["pct_acum"] = abc["fact_acum"] / total_fact * 100 if total_fact > 0 else 0

    def asignar_abc(pct):
        if pct <= p["abc_a"]:
            return "A"
        if pct <= p["abc_b"]:
            return "B"
        return "C"

    abc["abc"] = abc["pct_acum"].apply(asignar_abc)
    df = df.merge(abc[["articulo", "abc"]], on="articulo", how="left")
    df["abc"] = df["abc"].fillna("C")

    # --- Estacionalidad ---
    estac = df_vta.groupby(["articulo", "mes"])["cantidad"].sum().reset_index()
    estac_pivot = estac.pivot_table(index="articulo", columns="mes", values="cantidad", fill_value=0)

    def calc_estac(row):
        total = row.sum()
        if total == 0:
            return "SIN DATOS"
        top4 = sum(sorted(row.values, reverse=True)[:4])
        pct = top4 / total
        if pct >= 0.70:
            return "ESTACIONAL"
        if pct >= 0.55:
            return "SEMI-ESTACIONAL"
        return "PAREJO"

    meses_nombre = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
                    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

    def meses_pico(row):
        if row.sum() == 0:
            return ""
        top2 = row.nlargest(2).index.tolist()
        return ", ".join([meses_nombre.get(m, "?") for m in top2])

    estac_tipo = estac_pivot.apply(calc_estac, axis=1).reset_index()
    estac_tipo.columns = ["articulo", "estacionalidad"]
    estac_pico = estac_pivot.apply(meses_pico, axis=1).reset_index()
    estac_pico.columns = ["articulo", "meses_pico"]
    estac_res = estac_tipo.merge(estac_pico, on="articulo")

    df = df.merge(estac_res, on="articulo", how="left")
    df["estacionalidad"] = df["estacionalidad"].fillna("SIN DATOS")
    df["meses_pico"] = df["meses_pico"].fillna("")

    # --- Curva de talles ---
    curva = df_vta.groupby(["articulo", "color_desc", "talle"])["cantidad"].sum().reset_index()
    curva_tot = df_vta.groupby(["articulo", "color_desc"])["cantidad"].sum().reset_index()
    curva_tot.columns = ["articulo", "color_desc", "total_art_color"]
    curva = curva.merge(curva_tot, on=["articulo", "color_desc"])
    curva["pct_talle"] = (curva["cantidad"] / curva["total_art_color"] * 100).round(1)
    curva = curva.sort_values(["articulo", "color_desc", "pct_talle"], ascending=[True, True, False])

    # --- Accion ---
    def accion(row):
        msd = p["min_sin_demanda"]
        if row["vpd"] == 0 and row["minimo_actual"] > msd and row["stock_actual"] > msd:
            return f"REDUCIR a {msd} y devolver excedente"
        if row["vpd"] == 0 and row["minimo_actual"] > msd:
            return f"REDUCIR minimo a {msd}"
        if row["vpd"] == 0 and row["minimo_actual"] < msd and row["stock_actual"] < msd:
            return f"AGREGAR {msd} unidad(es) de muestra"
        if row["vpd"] == 0:
            return "OK - mantener"
        if row["estado"] == "SOBRESTOCK" and row["stock_actual"] > row["minimo_optimo"]:
            return f"REDUCIR min a {row['minimo_optimo']:.0f}, devolver {row['stock_actual'] - row['minimo_optimo']:.0f} uds"
        if row["estado"] == "SOBRESTOCK":
            return f"REDUCIR min a {row['minimo_optimo']:.0f}"
        if row["estado"] == "RIESGO":
            return f"SUBIR min a {row['minimo_optimo']:.0f}"
        return "OK - mantener"

    df["accion"] = df.apply(accion, axis=1)

    # --- Metricas resumen ---
    total = len(df)
    estados = df["estado"].value_counts().to_dict()
    sobre_total = estados.get("SOBRESTOCK", 0) + estados.get("SIN DEMANDA (sobrestock)", 0)
    optimo_total = estados.get("OPTIMO", 0) + estados.get("SIN DEMANDA (optimo)", 0)
    riesgo_total = estados.get("RIESGO", 0)
    falta_total = estados.get("SIN DEMANDA (falta muestra)", 0)
    uds_liberar = abs(df[df["delta"] < 0]["delta"].sum())
    uds_faltantes = df[df["delta"] > 0]["delta"].sum()
    vendio_rec = (df["vendio_reciente"] == "SI").sum()

    results["summary"] = {
        "total": total,
        "sobre": sobre_total,
        "optimo": optimo_total,
        "riesgo": riesgo_total,
        "falta_muestra": falta_total,
        "pct_sobre": sobre_total / total * 100 if total > 0 else 0,
        "pct_optimo": optimo_total / total * 100 if total > 0 else 0,
        "pct_riesgo": riesgo_total / total * 100 if total > 0 else 0,
        "uds_liberar": uds_liberar,
        "uds_faltantes": uds_faltantes,
        "vendio_reciente": vendio_rec,
        "min_actual_total": df["minimo_actual"].sum(),
        "min_optimo_total": df["minimo_optimo"].sum(),
        "fecha_desde": fecha_corte.strftime("%Y-%m"),
        "fecha_hasta": fecha_max.strftime("%Y-%m"),
        "total_meses": total_meses,
    }

    results["df_detail"] = df
    results["df_abc"] = abc
    results["df_curva"] = curva
    results["df_estac"] = estac_res
    results["estac_pivot"] = estac_pivot
    results["estados"] = estados

    return results

# ═══════════════════════════════════════════════════════════════
# 5. TABS DE VISUALIZACION
# ═══════════════════════════════════════════════════════════════

def render_summary(r):
    s = r["summary"]
    st.markdown("### Resumen Ejecutivo")
    st.markdown(f"Periodo de analisis: **{s['fecha_desde']}** a **{s['fecha_hasta']}** ({s['total_meses']} meses)")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("SKUs Vigentes", f"{s['total']:,}")
    c2.metric("Sobrestock", f"{s['sobre']:,}", f"{s['pct_sobre']:.1f}%")
    c3.metric("Optimo", f"{s['optimo']:,}", f"{s['pct_optimo']:.1f}%")
    c4.metric("Riesgo", f"{s['riesgo']:,}", f"{s['pct_riesgo']:.1f}%")

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Uds a Liberar", f"{s['uds_liberar']:,.0f}")
    c2.metric("Uds Faltantes", f"{s['uds_faltantes']:,.0f}")
    c3.metric("Vendio Ult. Meses", f"{s['vendio_reciente']:,}")
    c4.metric("Falta Muestra", f"{s['falta_muestra']:,}")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Distribucion por Estado")
        estado_df = pd.DataFrame(list(r["estados"].items()), columns=["Estado", "SKUs"])
        estado_df = estado_df.sort_values("SKUs", ascending=True)
        st.bar_chart(estado_df.set_index("Estado"))

    with c2:
        st.markdown("#### Minimos: Actual vs Optimo")
        comp = pd.DataFrame({
            "Tipo": ["Minimo Actual Total", "Minimo Optimo Total"],
            "Unidades": [s["min_actual_total"], s["min_optimo_total"]]
        })
        st.bar_chart(comp.set_index("Tipo"))

def render_classification(r):
    df = r["df_detail"]
    st.markdown("### Clasificacion de Stock")

    c1, c2 = st.columns(2)
    with c1:
        filtro_estado = st.multiselect("Filtrar por Estado", options=sorted(df["estado"].unique()),
                                        default=sorted(df["estado"].unique()), key="cls_est")
    with c2:
        filtro_abc = st.multiselect("Filtrar por ABC", options=["A", "B", "C"],
                                     default=["A", "B", "C"], key="cls_abc")

    buscar = st.text_input("Buscar articulo", key="cls_buscar")

    mask = df["estado"].isin(filtro_estado) & df["abc"].isin(filtro_abc)
    if buscar:
        mask = mask & df["articulo"].str.contains(buscar.upper(), na=False)

    show_cols = ["local", "articulo", "color_desc", "talle", "abc", "minimo_actual",
                 "stock_actual", "estado", "minimo_optimo", "delta", "dias_vender_excedente",
                 "vendio_reciente", "estacionalidad", "uds_total", "accion"]
    show_names = ["Local", "Articulo", "Color", "Talle", "ABC", "Min Actual",
                  "Stock", "Estado", "Min Optimo", "Delta", "Dias Vender Excedente",
                  "Venta Reciente", "Estacionalidad", "Uds Vendidas", "Accion"]

    df_show = df.loc[mask, show_cols].copy()
    df_show.columns = show_names
    st.dataframe(df_show, use_container_width=True, height=500)
    st.caption(f"Mostrando {len(df_show):,} de {len(df):,} registros")

def render_abc(r):
    df_abc = r["df_abc"]
    st.markdown("### Clasificacion ABC (Pareto)")

    c1, c2, c3 = st.columns(3)
    for cat, col in zip(["A", "B", "C"], [c1, c2, c3]):
        sub = df_abc[df_abc["abc"] == cat]
        col.metric(f"Clase {cat}", f"{len(sub)} articulos",
                   f"${sub['fact'].sum():,.0f}")

    st.markdown("---")
    st.markdown("#### Curva de Pareto")
    pareto = df_abc[["articulo", "pct_acum", "abc"]].head(100).copy()
    pareto = pareto.reset_index(drop=True)
    st.line_chart(pareto.set_index("articulo")["pct_acum"])

    st.markdown("#### Detalle ABC")
    show = df_abc[["articulo", "fact", "pct_acum", "abc"]].copy()
    show.columns = ["Articulo", "Facturacion", "% Acumulado", "ABC"]
    show["Facturacion"] = show["Facturacion"].apply(lambda x: f"${x:,.0f}")
    show["% Acumulado"] = show["% Acumulado"].round(1)
    st.dataframe(show, use_container_width=True, height=400)

def render_seasonality(r):
    df_estac = r["df_estac"]
    st.markdown("### Estacionalidad")

    c1, c2, c3 = st.columns(3)
    for tipo, col in zip(["ESTACIONAL", "SEMI-ESTACIONAL", "PAREJO"], [c1, c2, c3]):
        n = len(df_estac[df_estac["estacionalidad"] == tipo])
        col.metric(tipo, f"{n} articulos")

    st.markdown("---")

    filtro = st.selectbox("Filtrar por tipo", ["TODOS", "ESTACIONAL", "SEMI-ESTACIONAL", "PAREJO", "SIN DATOS"], key="est_f")
    if filtro != "TODOS":
        show = df_estac[df_estac["estacionalidad"] == filtro]
    else:
        show = df_estac
    show_exp = show.copy()
    show_exp.columns = ["Articulo", "Estacionalidad", "Meses Pico"]
    st.dataframe(show_exp, use_container_width=True, height=400)

    # Heatmap para articulo seleccionado
    st.markdown("---")
    st.markdown("#### Detalle mensual por articulo")
    pivot = r["estac_pivot"]
    if len(pivot) > 0:
        art_sel = st.selectbox("Seleccionar articulo", sorted(pivot.index.tolist()), key="est_art")
        if art_sel in pivot.index:
            row = pivot.loc[art_sel]
            meses_nombre = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
                            7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
            chart_df = pd.DataFrame({"Mes": [meses_nombre[m] for m in row.index], "Unidades": row.values})
            st.bar_chart(chart_df.set_index("Mes"))

def render_size_curve(r):
    curva = r["df_curva"]
    st.markdown("### Curva de Talles")

    arts = sorted(curva["articulo"].unique())
    art_sel = st.selectbox("Articulo", arts, key="sz_art")
    sub = curva[curva["articulo"] == art_sel]

    colores = sorted(sub["color_desc"].unique())
    col_sel = st.selectbox("Color", colores, key="sz_col") if len(colores) > 0 else None

    if col_sel:
        sub2 = sub[sub["color_desc"] == col_sel].sort_values("pct_talle", ascending=False)
        st.bar_chart(sub2.set_index("talle")["pct_talle"])

        show = sub2[["talle", "cantidad", "pct_talle"]].copy()
        show.columns = ["Talle", "Uds Vendidas", "% del Talle"]
        show["Uds Vendidas"] = show["Uds Vendidas"].astype(int)
        st.dataframe(show, use_container_width=True)

def render_actionable(r):
    df = r["df_detail"]
    st.markdown("### Lista Accionable")

    df_acc = df[~df["accion"].str.startswith("OK")].copy()

    tipo_accion = st.multiselect("Tipo de accion",
                                  options=sorted(df_acc["accion"].apply(lambda x: x.split(" ")[0]).unique()),
                                  default=sorted(df_acc["accion"].apply(lambda x: x.split(" ")[0]).unique()),
                                  key="acc_tipo")

    mask = df_acc["accion"].apply(lambda x: x.split(" ")[0]).isin(tipo_accion)
    df_show = df_acc.loc[mask, ["local", "articulo", "color_desc", "talle", "abc",
                                 "minimo_actual", "stock_actual", "estado",
                                 "minimo_optimo", "delta", "dias_vender_excedente",
                                 "vendio_reciente", "accion"]].copy()
    df_show.columns = ["Local", "Articulo", "Color", "Talle", "ABC",
                        "Min Actual", "Stock", "Estado", "Min Optimo", "Delta",
                        "Dias Vender Excedente", "Venta Reciente", "Accion"]
    df_show = df_show.sort_values("Delta")

    c1, c2, c3 = st.columns(3)
    c1.metric("SKUs con accion", f"{len(df_show):,}")
    c2.metric("A reducir", f"{(df_show['Delta'] < 0).sum():,}")
    c3.metric("A subir", f"{(df_show['Delta'] > 0).sum():,}")

    st.dataframe(df_show, use_container_width=True, height=500)

def render_download(r):
    df = r["df_detail"]
    st.markdown("### Descargar Excel Completo")
    st.markdown("El archivo incluye todas las hojas del analisis.")

    det_cols = ["local", "articulo", "color_desc", "talle", "sku", "abc",
                "minimo_actual", "stock_actual", "estado", "minimo_optimo", "delta",
                "dias_vender_excedente", "vendio_reciente", "estacionalidad", "meses_pico",
                "meses_venta", "uds_total", "facturacion", "accion"]
    det_names = ["Local", "Articulo", "Color", "Talle", "SKU", "ABC",
                 "Min Actual", "Stock Actual", "Estado", "Min Optimo", "Delta",
                 "Dias Vender Excedente", "Vendio Reciente", "Estacionalidad", "Meses Pico",
                 "Meses con Venta", "Uds Vendidas", "Facturacion", "Accion"]

    df_det = df[det_cols].copy()
    df_det.columns = det_names
    df_det["Facturacion"] = df_det["Facturacion"].round(0)

    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_det.to_excel(writer, sheet_name="Detalle", index=False)

        sobre = df_det[df_det["Estado"].isin(["SOBRESTOCK", "SIN DEMANDA (sobrestock)"])].sort_values("Delta")
        sobre.to_excel(writer, sheet_name="Sobrestock", index=False)

        riesgo = df_det[df_det["Estado"].isin(["RIESGO", "SIN DEMANDA (falta muestra)"])].sort_values("Delta")
        riesgo.to_excel(writer, sheet_name="Riesgo", index=False)

        acc = df_det[~df_det["Accion"].str.startswith("OK")].sort_values("Accion")
        acc.to_excel(writer, sheet_name="Accionable", index=False)

        abc_exp = r["df_abc"][["articulo", "fact", "pct_acum", "abc"]].copy()
        abc_exp.columns = ["Articulo", "Facturacion", "% Acumulado", "ABC"]
        abc_exp.to_excel(writer, sheet_name="ABC Pareto", index=False)

        curva_exp = r["df_curva"][["articulo", "color_desc", "talle", "cantidad", "pct_talle"]].copy()
        curva_exp.columns = ["Articulo", "Color", "Talle", "Uds Vendidas", "% Talle"]
        curva_exp.to_excel(writer, sheet_name="Curva Talles", index=False)

        estac_exp = r["df_estac"].copy()
        estac_exp.columns = ["Articulo", "Estacionalidad", "Meses Pico"]
        estac_exp.to_excel(writer, sheet_name="Estacionalidad", index=False)

        res_art = df.groupby("articulo").agg(
            abc=("abc", "first"), variantes=("sku", "count"),
            min_actual=("minimo_actual", "sum"), min_optimo=("minimo_optimo", "sum"),
            delta=("delta", "sum"), stock=("stock_actual", "sum"),
            uds=("uds_total", "max"), fact=("facturacion", "max"),
            estac=("estacionalidad", "first"),
        ).reset_index().sort_values("fact", ascending=False)
        res_art.columns = ["Articulo", "ABC", "Variantes", "Min Actual", "Min Optimo",
                            "Delta", "Stock", "Uds Vendidas", "Facturacion", "Estacionalidad"]
        res_art.to_excel(writer, sheet_name="Por Articulo", index=False)

    st.download_button(
        label="📥 Descargar analisis_completo.xlsx",
        data=buf.getvalue(),
        file_name=f"analisis_stock_SELU_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# ═══════════════════════════════════════════════════════════════
# 6. MAIN
# ═══════════════════════════════════════════════════════════════
def main():
    if not st.session_state.get("authenticated"):
        render_login()
        return

    params = render_sidebar()

    st.markdown("""
    <h1 style="font-weight: 300; letter-spacing: 3px; color: #3f3f40; border-bottom: 2px solid #e9a5b2; padding-bottom: 10px;">
        SELU <span style="font-size: 0.5em; color: #796161;">Optimizacion de Stock</span>
    </h1>
    """, unsafe_allow_html=True)

    if params["file_min"] is None or params["file_vta"] is None:
        st.info("📁 Suba los archivos de **Minimos** y **Ventas** en el panel lateral para comenzar.")
        return

    with st.spinner("Procesando datos..."):
        try:
            df_min = load_minimos(params["file_min"].getvalue())
            df_vta = load_ventas(params["file_vta"].getvalue())
        except Exception as e:
            st.error(f"Error leyendo archivos: {e}")
            return

        if len(df_min) == 0 or len(df_vta) == 0:
            st.error("No se pudieron cargar los datos. Verifique el formato de los archivos.")
            return

        st.sidebar.success(f"✅ Minimos: {len(df_min):,} SKUs")
        st.sidebar.success(f"✅ Ventas: {len(df_vta):,} registros")

        try:
            results = run_analysis(df_min, df_vta, params)
        except Exception as e:
            st.error(f"Error en el analisis: {e}")
            return

    tabs = st.tabs(["📊 Resumen", "📋 Clasificacion", "🏷️ ABC Pareto",
                     "📅 Estacionalidad", "📐 Curva Talles",
                     "✅ Accionable", "📥 Descargar"])

    with tabs[0]:
        render_summary(results)
    with tabs[1]:
        render_classification(results)
    with tabs[2]:
        render_abc(results)
    with tabs[3]:
        render_seasonality(results)
    with tabs[4]:
        render_size_curve(results)
    with tabs[5]:
        render_actionable(results)
    with tabs[6]:
        render_download(results)

if __name__ == "__main__":
    main()
