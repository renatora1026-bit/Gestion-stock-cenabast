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
        df = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
        df['Saldo Meses'] = pd.to_numeric(df['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
        data_ssasur = df.dropna(subset=['Saldo Meses'])
        st.success("✅ SSASUR cargado")
    except Exception as e:
        st.error(f"Error SSASUR: {e}")

# --- 3. PROCESAMIENTO CENABAST ---
if f_icp:
    try:
        # Leemos el archivo saltando posibles encabezados vacíos
        df_temp = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip')
        if "INFORME" in str(df_temp.columns[0]).upper() or df_temp.shape[1] < 5:
            f_icp.seek(0)
            df_temp = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', skiprows=4, on_bad_lines='skip')
        
        data_icp = df_temp
        data_icp.columns = [str(c).upper().strip() for c in data_icp.columns]
        st.success("✅ ICP Cenabast sincronizado")
    except Exception as e:
        st.error("Error al procesar Cenabast.")

# --- 4. CRUCE INTELIGENTE Y DASHBOARD ---
if data_ssasur is not None:
    st.divider()
    resumen = data_ssasur.copy()
    resumen['Producto'] = resumen['Producto'].str.upper().str.strip()

    if data_icp is not None:
        # Buscamos columnas clave
        col_prod_icp = [c for c in data_icp.columns if any(k in c for k in ['NOMBRE', 'GENERICO', 'PRODUCTO'])][0]
        col_estado_icp = [c for c in data_icp.columns if any(k in c for k in ['ESTADO', 'SEMAFORO', 'STATUS'])][0]
        
        # Limpieza de datos de Cenabast para el cruce
        data_icp[col_prod_icp] = data_icp[col_prod_icp].astype(str).str.upper().str.strip()
        
        # Función de búsqueda inteligente
        def buscar_estado(prod_ssasur):
            # Intento 1: Coincidencia exacta
            match = data_icp[data_icp[col_prod_icp] == prod_ssasur]
            if not match.empty:
                return match[col_estado_icp].iloc[0]
            
            # Intento 2: ¿El nombre de Cenabast está contenido en el de SSASUR?
            # Tomamos las primeras dos palabras para buscar (ej: "FLUOXETINA 20")
            base = " ".join(prod_ssasur.split()[:2])
            match_parcial = data_icp[data_icp[col_prod_icp].str.contains(base, na=False)]
            if not match_parcial.empty:
                return match_parcial[col_estado_icp].iloc[0]
            
            return "Pendiente"

        resumen['Estado Cenabast'] = resumen['Producto'].apply(buscar_estado)
    else:
        resumen['Estado Cenabast'] = "Carga ICP para ver estado"

    st.subheader("📋 Prioridades de Abastecimiento")
    cols = ['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Cenabast']
    st.dataframe(resumen[cols].sort_values('Saldo Meses').style.applymap(
        lambda x: 'background-color: #ff4b4b; color: white' if isinstance(x, float) and x < 0.5 else '', subset=['Saldo Meses']))
