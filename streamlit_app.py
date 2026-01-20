import streamlit as st
import pandas as pd

st.set_page_config(page_title="Radar Saavedra Pro", layout="wide")
st.title("🚀 Radar de Abastecimiento - Hospital Puerto Saavedra")

# --- 1. CARGA DE ARCHIVOS ---
col1, col2, col3 = st.columns(3)
with col1: f_ssasur = st.file_uploader("📥 SSASUR (CSV)", type=["csv"])
with col2: f_icp = st.file_uploader("📦 CENABAST (CSV)", type=["csv"])
with col3: f_arsenal = st.file_uploader("📋 ARSENAL (Excel)", type=["xlsx"])

data_ssasur = None
data_icp = None

# --- 2. PROCESAMIENTO SSASUR ---
if f_ssasur:
    try:
        df = pd.read_csv(f_ssasur, sep=";", encoding='latin1')
        df['Saldo Meses'] = pd.to_numeric(df['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
        data_ssasur = df.dropna(subset=['Saldo Meses'])
        st.success("✅ SSASUR cargado")
    except Exception as e:
        st.error(f"Error SSASUR: {e}")

# --- 3. PROCESAMIENTO CENABAST (Versión Ultra-Flexible) ---
if f_icp:
    try:
        f_icp.seek(0)
        # Cargamos el CSV saltándonos las filas de título iniciales del portal
        df_temp = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8')
        
        # Si la primera columna parece ser un título y no datos, re-escaneamos
        if "INFORME" in str(df_temp.columns[0]).upper():
            f_icp.seek(0)
            df_temp = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', skiprows=4)
        
        data_icp = df_temp
        data_icp.columns = [str(c).upper().strip() for c in data_icp.columns]
        st.success("✅ ICP Cenabast sincronizado")
    except Exception as e:
        st.error(f"Error al procesar el CSV de Cenabast: {e}")

# --- 4. DASHBOARD Y CRUCE ---
if data_ssasur is not None:
    st.divider()
    resumen = data_ssasur.copy()
    resumen['Producto'] = resumen['Producto'].str.upper()

    if data_icp is not None:
        # Buscamos columnas de forma segura
        col_prod = [c for c in data_icp.columns if any(k in c for k in ['NOMBRE', 'GENERICO', 'PRODUCTO'])]
        col_est = [c for c in data_icp.columns if any(k in c for k in ['ESTADO', 'SEMAFORO', 'STATUS'])]
        
        if col_prod and col_est:
            mapa = pd.Series(data_icp[col_est[0]].values, index=data_icp[col_prod[0]].astype(str).str.upper()).to_dict()
            resumen['Estado Cenabast'] = resumen['Producto'].map(mapa).fillna("Sin registro")
        else:
            resumen['Estado Cenabast'] = "Columnas no detectadas"
    
    st.subheader("📋 Gestión de Stock Crítico")
    st.dataframe(resumen[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Cenabast']].sort_values('Saldo Meses').style.applymap(
        lambda x: 'background-color: #ff4b4b; color: white' if isinstance(x, float) and x < 0.5 else '', subset=['Saldo Meses']))
