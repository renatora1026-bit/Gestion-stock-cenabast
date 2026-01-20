import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Radar Saavedra Pro", layout="wide")
st.title("🚀 Sistema de Inteligencia de Inventario")
st.write("Hospital de Puerto Saavedra - Gestión Renato Rozas")

# --- 1. CARGA DE ARCHIVOS ---
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

# --- 2. PROCESAMIENTO ---

# SSASUR
if f_ssasur:
    try:
        df = pd.read_csv(f_ssasur, sep=";", encoding='latin1')
        df['Saldo Meses'] = pd.to_numeric(df['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
        data_ssasur = df.dropna(subset=['Saldo Meses'])
        st.success("✅ SSASUR cargado con éxito")
    except Exception as e:
        st.error(f"Error en SSASUR: {e}")

# ICP CENABAST (Lectura Ultra-Robusta)
if f_icp:
    try:
        # Intento A: Leer como HTML (el truco para archivos de portales públicos)
        f_icp.seek(0)
        tablas = pd.read_html(f_icp)
        data_icp = tablas[0]
    except:
        try:
            # Intento B: Excel estándar
            f_icp.seek(0)
            data_icp = pd.read_excel(f_icp)
        except:
            try:
                # Intento C: CSV
                f_icp.seek(0)
                data_icp = pd.read_csv(f_icp, sep=";", encoding='latin1')
            except:
                st.error("❌ Formato no reconocido. Abre el ICP en tu Mac, dale a 'Guardar como' -> 'Libro de Excel (.xlsx)' y súbelo de nuevo.")

    if data_icp is not None:
        st.success("✅ ICP Cenabast sincronizado")

# --- 3. CRUCE Y VISUALIZACIÓN ---
if data_ssasur is not None:
    st.divider()
    resumen = data_ssasur.copy()
    resumen['Producto'] = resumen['Producto'].str.upper()

    # Cruce con ICP para Fechas
    if data_icp is not None:
        # Buscamos columnas de Producto y Fecha sin importar mayúsculas
        data_icp.columns = [str(c).upper() for c in data_icp.columns]
        col_prod_icp = [c for c in data_icp.columns if 'PRODUCTO' in c or 'DESCRIP' in c][0]
        col_fecha = [c for c in data_icp.columns if 'FECHA' in c or 'PROGRAMADA' in c][0]
        
        dict_fechas = pd.Series(data_icp[col_fecha].values, index=data_icp[col_prod_icp].astype(str).str.upper()).to_dict()
        resumen['Llegada Cenabast'] = resumen['Producto'].map(dict_fechas).fillna("Sin programar")
    else:
        resumen['Llegada Cenabast'] = "Carga ICP"

    # Mostrar Tabla de Gestión
    st.subheader("📋 Prioridades y Próximos Despachos")
    st.dataframe(resumen[['Producto', 'Saldo Actual', 'Saldo Meses', 'Llegada Cenabast']].sort_values('Saldo Meses').style.applymap(
        lambda x: 'background-color: #ff4b4b; color: white' if isinstance(x, float) and x < 0.5 else '', subset=['Saldo Meses']))
