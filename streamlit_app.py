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

# --- 3. PROCESAMIENTO CENABAST (Buscador Flexible) ---
if f_icp:
    try:
        f_icp.seek(0)
        df_full = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', header=None, on_bad_lines='skip')
        
        # Localizamos la fila de encabezados
        row_idx = None
        for i, row in df_full.iterrows():
            if any('NOMBRE GEN' in str(cell).upper() or 'PRODUCTO' in str(cell).upper() for cell in row):
                row_idx = i
                break
        
        if row_idx is not None:
            f_icp.seek(0)
            data_icp = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', skiprows=row_idx, on_bad_lines='skip')
            data_icp.columns = [str(c).upper().strip() for c in data_icp.columns]
            st.success("✅ ICP Cenabast sincronizado")
        else:
            st.error("🚨 No se detectó la tabla. Revisa que el archivo sea el CSV correcto.")
    except Exception as e:
        st.error(f"Error de lectura: {e}")

# --- 4. CRUCE INTELIGENTE Y DASHBOARD ---
if data_ssasur is not None:
    st.divider()
    resumen = data_ssasur.copy()
    resumen['Producto'] = resumen['Producto'].str.upper().str.strip()

    if data_icp is not None:
        try:
            # Columnas clave del ICP
            col_prod_icp = [c for c in data_icp.columns if any(k in c for k in ['NOMBRE', 'GENERICO', 'PRODUCTO'])][0]
            col_est_icp = [c for c in data_icp.columns if any(k in c for k in ['ESTADO', 'SEMAFORO', 'STATUS'])][0]
            
            # Limpieza exhaustiva de datos de Cenabast
            data_icp[col_prod_icp] = data_icp[col_prod_icp].astype(str).str.upper().str.strip()
            
            # Función de búsqueda "Fuzzy" (Coincidencia por la primera palabra clave)
            def buscar_estado_flexible(prod_ssasur):
                # Sacamos solo la primera palabra (ej: "FLUOXETINA") para máxima compatibilidad
                palabra_clave = str(prod_ssasur).split()[0]
                mask = data_icp[col_prod_icp].str.contains(palabra_clave, na=False, regex=False)
                match = data_icp[mask]
                
                if not match.empty:
                    # Si hay varias, priorizamos la que tenga el nombre más largo (más específica)
                    return match.sort_values(by=col_prod_icp, key=lambda x: x.str.len(), ascending=False)[col_est_icp].iloc[0]
                return "No en ICP"

            resumen['Estado Cenabast'] = resumen['Producto'].apply(buscar_estado_flexible)
        except:
            resumen['Estado Cenabast'] = "Error en Cruce"

    st.subheader("📋 Gestión de Stock Crítico - Hospital Puerto Saavedra")
    cols_v = ['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Cenabast']
    
    # Formateo visual: Rojo para stock crítico (< 0.5 meses)
    st.dataframe(
        resumen[cols_v].sort_values('Saldo Meses').style.applymap(
            lambda x: 'background-color: #ff4b4b; color: white' if isinstance(x, float) and x < 0.5 else '', 
            subset=['Saldo Meses']
        )
    )
