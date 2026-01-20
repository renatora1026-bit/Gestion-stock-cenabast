import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Radar Saavedra Pro", layout="wide")
st.title("🚀 Sistema de Inteligencia de Inventario")
st.write("Hospital de Puerto Saavedra - Gestión Renato Rozas")

# --- 1. SECCIÓN DE CARGA ---
st.header("1. Carga de Planillas")
col1, col2, col3 = st.columns(3)

with col1:
    f_ssasur = st.file_uploader("📥 SSASUR (CSV)", type=["csv"], key="ssasur")
with col2:
    f_icp = st.file_uploader("📦 CENABAST (ICP)", type=["csv", "xls", "xlsx"], key="icp")
with col3:
    f_arsenal = st.file_uploader("📋 ARSENAL (Excel)", type=["xlsx", "xlsm"], key="arsenal")

data_ssasur = None
data_icp = None
data_arsenal = []

# --- 2. PROCESAMIENTO INTELIGENTE ---

# SSASUR: Lectura Robusta
if f_ssasur:
    try:
        df = pd.read_csv(f_ssasur, sep=";", encoding='latin1')
        df['Saldo Meses'] = pd.to_numeric(df['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
        data_ssasur = df.dropna(subset=['Saldo Meses'])
        st.success("✅ SSASUR cargado con éxito")
    except Exception as e:
        st.error(f"Error en SSASUR: {e}")

# ICP CENABAST: El "Desencriptador"
if f_icp:
    try:
        # Intento 1: Como Excel Estándar
        data_icp = pd.read_excel(f_icp)
    except:
        try:
            # Intento 2: Como HTML (Formato real de muchos archivos .xls de Cenabast)
            f_icp.seek(0)
            data_icp = pd.read_html(io.BytesIO(f_icp.read()))[0]
        except:
            try:
                # Intento 3: Como CSV con punto y coma
                f_icp.seek(0)
                data_icp = pd.read_csv(f_icp, sep=";", encoding='latin1')
            except Exception as e:
                st.error("⚠️ No pudimos leer el archivo. Prueba abriéndolo en Excel y guardándolo como 'Libro de Excel (.xlsx)'")

    if data_icp is not None:
        st.success("✅ ICP Cenabast sincronizado")

# ARSENAL: Extracción de Listado
if f_arsenal:
    try:
        df_art = pd.read_excel(f_arsenal)
        col_prod = [c for c in df_art.columns if 'Descrip' in c or 'ARTICULO' in c.upper()][0]
        data_arsenal = df_art[col_prod].astype(str).str.upper().unique()
        st.success("✅ Arsenal sincronizado")
    except Exception as e:
        st.error("Revisa que el Arsenal tenga una columna llamada 'Descrip. Artículo'")

# --- 3. RADAR DE DISPONIBILIDAD ---
if data_ssasur is not None:
    st.divider()
    resumen = data_ssasur.copy()
    resumen['Producto'] = resumen['Producto'].str.upper()

    # Identificación de Arsenal
    resumen['Es Arsenal'] = resumen['Producto'].apply(lambda x: "✅" if any(p in x for p in data_arsenal) else "❌")
    
    # Cruce con ICP (Fechas y Estado)
    if data_icp is not None:
        # Buscamos columnas clave en el ICP
        col_fecha = [c for c in data_icp.columns if 'Fecha' in c or 'PROGRAMADA' in c.upper()]
        if col_fecha:
            dict_fechas = pd.Series(data_icp[col_fecha[0]].values, index=data_icp['Producto'].astype(str).str.upper()).to_dict()
            resumen['Próxima Entrega'] = resumen['Producto'].map(dict_fechas).fillna("Sin fecha")
        else:
            resumen['Próxima Entrega'] = "No detectada"
    else:
        resumen['Próxima Entrega'] = "Carga ICP"

    # Filtros y Visualización
    st.sidebar.header("Control de Inventario")
    solo_arsenal = st.sidebar.checkbox("Ver solo mi Arsenal", value=True)
    if solo_arsenal:
        resumen = resumen[resumen['Es Arsenal'] == "✅"]

    col_chart, col_table = st.columns([1, 2])
    with col_chart:
        resumen['Nivel'] = resumen['Saldo Meses'].apply(lambda x: 'CRÍTICO' if x < 0.5 else ('RIESGO' if x < 1.0 else 'SEGURO'))
        fig = px.pie(resumen, names='Nivel', color='Nivel', 
                     color_discrete_map={'CRÍTICO':'#ff4b4b', 'RIESGO':'#ffa500', 'SEGURO':'#28a745'},
                     title="Composición de Stock")
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.subheader("📋 Listado de Gestión")
        # Semáforo dinámico
        st.dataframe(resumen[['Producto', 'Saldo Actual', 'Saldo Meses', 'Próxima Entrega']].sort_values('Saldo Meses').style.applymap(
            lambda x: 'background-color: #ff4b4b; color: white' if isinstance(x, float) and x < 0.5 else '', subset=['Saldo Meses']))
