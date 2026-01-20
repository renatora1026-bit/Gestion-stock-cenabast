import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Radar Saavedra Pro", layout="wide")
st.title("🚀 Radar de Abastecimiento - Hospital Puerto Saavedra")

# --- 1. CARGA DE ARCHIVOS ---
st.header("1. Carga de Planillas")
col1, col2, col3 = st.columns(3)

with col1:
    f_ssasur = st.file_uploader("📥 SSASUR (CSV)", type=["csv"], key="u_ssasur")
with col2:
    f_icp = st.file_uploader("📦 CENABAST (CSV)", type=["csv"], key="u_icp")
with col3:
    f_arsenal = st.file_uploader("📋 ARSENAL (Excel)", type=["xlsx"], key="u_arsenal")

# --- 2. PROCESAMIENTO ---
data_ssasur = None
data_icp = None

# Procesar SSASUR
if f_ssasur:
    try:
        df = pd.read_csv(f_ssasur, sep=";", encoding='latin1')
        df['Saldo Meses'] = pd.to_numeric(df['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
        data_ssasur = df.dropna(subset=['Saldo Meses'])
        st.success("✅ SSASUR cargado")
    except Exception as e:
        st.error(f"Error en SSASUR: {e}")

# Procesar CENABAST (CSV que guardaste)
if f_icp:
    try:
        f_icp.seek(0)
        # Probamos con punto y coma (típico de Excel en Chile)
        try:
            data_icp = pd.read_csv(f_icp, sep=";", encoding='utf-8')
        except:
            f_icp.seek(0)
            data_icp = pd.read_csv(f_icp, sep=",", encoding='utf-8')
        
        # Limpiar nombres de columnas para el cruce
        data_icp.columns = [str(c).upper() for c in data_icp.columns]
        st.success("✅ ICP Cenabast sincronizado")
    except Exception as e:
        st.error("🚨 Sube el archivo que guardaste como '.csv' en tu Mac.")

# --- 3. DASHBOARD DE GESTIÓN ---
if data_ssasur is not None:
    st.divider()
    resumen = data_ssasur.copy()
    resumen['Producto'] = resumen['Producto'].str.upper()

    # Cruce de datos si hay ICP
    if data_icp is not None:
        # Buscamos columnas de Producto y Estado/Fecha
        c_prod = [c for c in data_icp.columns if 'NOMBRE GEN' in c or 'PRODUCTO' in c][0]
        c_estado = [c for c in data_icp.columns if 'ESTADO' in c or 'SEMAFORO' in c][0]
        
        mapa_estado = pd.Series(data_icp[c_estado].values, index=data_icp[c_prod].astype(str).str.upper()).to_dict()
        resumen['Estado Cenabast'] = resumen['Producto'].map(mapa_estado).fillna("Sin info")
    else:
        resumen['Estado Cenabast'] = "Carga el CSV de Cenabast"

    st.subheader("📋 Gestión de Stock Crítico")
    st.dataframe(resumen[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Cenabast']].sort_values('Saldo Meses').style.applymap(
        lambda x: 'background-color: #ff4b4b; color: white' if isinstance(x, float) and x < 0.5 else '', subset=['Saldo Meses']))
