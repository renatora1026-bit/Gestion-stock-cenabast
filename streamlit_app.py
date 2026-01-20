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

# --- 3. PROCESAMIENTO CENABAST (Buscador Universal) ---
if f_icp:
    try:
        # Cargamos el archivo completo sin importar los encabezados
        f_icp.seek(0)
        df_full = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', header=None, on_bad_lines='skip')
        
        # Buscamos la fila donde aparece la palabra "NOMBRE GEN" o "PRODUCTO"
        row_idx = None
        for i, row in df_full.iterrows():
            if any('NOMBRE GEN' in str(cell).upper() or 'PRODUCTO' in str(cell).upper() for cell in row):
                row_idx = i
                break
        
        if row_idx is not None:
            # Re-cargamos la tabla desde esa fila específica
            f_icp.seek(0)
            data_icp = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', skiprows=row_idx, on_bad_lines='skip')
            data_icp.columns = [str(c).upper().strip() for c in data_icp.columns]
            st.success("✅ ICP Cenabast sincronizado")
        else:
            st.error("🚨 No se detectó la columna 'NOMBRE GEN'. Asegúrate de guardar el ICP como CSV.")
    except Exception as e:
        st.error(f"Error de lectura: {e}")

# --- 4. CRUCE Y DASHBOARD ---
if data_ssasur is not None:
    st.divider()
    resumen = data_ssasur.copy()
    resumen['Producto'] = resumen['Producto'].str.upper().str.strip()
    resumen['Estado Cenabast'] = "Sin información"

    if data_icp is not None:
        try:
            # Identificación dinámica de columnas de cruce
            col_prod_icp = [c for c in data_icp.columns if any(k in c for k in ['NOMBRE', 'GENERICO', 'PRODUCTO'])][0]
            col_est_icp = [c for c in data_icp.columns if any(k in c for k in ['ESTADO', 'SEMAFORO', 'STATUS'])][0]
            
            # Limpieza para el cruce
            data_icp[col_prod_icp] = data_icp[col_prod_icp].astype(str).str.upper().str.strip()
            
            # Función de búsqueda por palabras clave
            def buscar_estado(prod_ssasur):
                base = " ".join(str(prod_ssasur).split()[:2])
                match = data_icp[data_icp[col_prod_icp].str.contains(base, na=False, regex=False)]
                return match[col_est_icp].iloc[0] if not match.empty else "Pendiente"

            resumen['Estado Cenabast'] = resumen['Producto'].apply(buscar_estado)
        except:
            st.warning("⚠️ Columnas identificadas pero formato de datos inusual.")

    st.subheader("📋 Gestión de Stock Crítico")
    cols_f = ['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Cenabast']
    st.dataframe(resumen[cols_f].sort_values('Saldo Meses').style.applymap(
        lambda x: 'background-color: #ff4b4b; color: white' if isinstance(x, float) and x < 0.5 else '', subset=['Saldo Meses']))
