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
        # Usamos sep=None para que pandas detecte si es , o ;
        df = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
        df['Saldo Meses'] = pd.to_numeric(df['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
        data_ssasur = df.dropna(subset=['Saldo Meses'])
        st.success("✅ SSASUR cargado")
    except Exception as e:
        st.error(f"Error SSASUR: {e}")

# --- 3. PROCESAMIENTO CENABAST (Detección Automática) ---
if f_icp:
    try:
        f_icp.seek(0)
        # El motor 'python' con sep=None es la clave para leer CSVs de Excel Chile
        df_temp = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
        
        # Limpieza de encabezados vacíos del portal
        if df_temp.shape[1] < 3: # Si detectó pocas columnas, es que el encabezado está más abajo
            f_icp.seek(0)
            df_temp = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', skiprows=4, on_bad_lines='skip')
        
        data_icp = df_temp
        data_icp.columns = [str(c).upper().strip() for c in data_icp.columns]
        st.success("✅ ICP Cenabast sincronizado")
    except Exception as e:
        st.error(f"Error ICP: Guarda el archivo nuevamente como CSV en tu Mac.")

# --- 4. DASHBOARD FINAL ---
if data_ssasur is not None:
    st.divider()
    resumen = data_ssasur.copy()
    resumen['Producto'] = resumen['Producto'].str.upper()

    # Inicializamos la columna de estado
    resumen['Estado Cenabast'] = "Sin información"

    if data_icp is not None:
        # Buscamos columnas de Producto y Estado de forma flexible
        col_prod = [c for c in data_icp.columns if any(k in c for k in ['NOMBRE', 'GENERICO', 'PRODUCTO'])]
        col_est = [c for c in data_icp.columns if any(k in c for k in ['ESTADO', 'SEMAFORO', 'STATUS'])]
        
        if col_prod and col_est:
            mapa = pd.Series(data_icp[col_est[0]].values, index=data_icp[col_prod[0]].astype(str).str.upper()).to_dict()
            resumen['Estado Cenabast'] = resumen['Producto'].map(mapa).fillna("Pendiente")
    
    st.subheader("📋 Gestión de Stock Crítico")
    # Mostramos la tabla solo si tenemos las columnas listas
    cols_mostrar = ['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Cenabast']
    st.dataframe(resumen[cols_mostrar].sort_values('Saldo Meses').style.applymap(
        lambda x: 'background-color: #ff4b4b; color: white' if isinstance(x, float) and x < 0.5 else '', subset=['Saldo Meses']))
