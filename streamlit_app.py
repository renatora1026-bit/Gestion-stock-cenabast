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

# --- 3. PROCESAMIENTO CENABAST (Cazador de Encabezados) ---
if f_icp:
    try:
        # Probamos leer el archivo saltando diferentes filas (0, 2, 4)
        for saltar in [0, 2, 4]:
            f_icp.seek(0)
            df_temp = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', skiprows=saltar, on_bad_lines='skip')
            cols = [str(c).upper() for c in df_temp.columns]
            
            # Si encontramos las palabras clave, esta es la tabla correcta
            if any('NOMBRE' in c or 'PRODUCTO' in c or 'GENERICO' in c for c in cols):
                data_icp = df_temp
                data_icp.columns = cols
                break
        
        if data_icp is not None:
            st.success("✅ ICP Cenabast sincronizado con éxito")
        else:
            st.error("🚨 No se encontró la tabla de productos. Revisa el CSV.")
    except Exception as e:
        st.error(f"Error en lectura de ICP: {e}")

# --- 4. CRUCE Y DASHBOARD ---
if data_ssasur is not None:
    st.divider()
    resumen = data_ssasur.copy()
    resumen['Producto'] = resumen['Producto'].str.upper().str.strip()
    resumen['Estado Cenabast'] = "Sin información"

    if data_icp is not None:
        # Localización dinámica de columnas
        try:
            col_prod_icp = [c for c in data_icp.columns if any(k in c for k in ['NOMBRE', 'GENERICO', 'PRODUCTO'])][0]
            col_estado_icp = [c for c in data_icp.columns if any(k in c for k in ['ESTADO', 'SEMAFORO', 'STATUS'])][0]
            
            data_icp[col_prod_icp] = data_icp[col_prod_icp].astype(str).str.upper().str.strip()
            
            # Mapeo por coincidencia de las primeras dos palabras
            def buscar_estado(prod_s):
                base = " ".join(str(prod_s).split()[:2])
                match = data_icp[data_icp[col_prod_icp].str.contains(base, na=False, regex=False)]
                return match[col_estado_icp].iloc[0] if not match.empty else "Pendiente"

            resumen['Estado Cenabast'] = resumen['Producto'].apply(buscar_estado)
        except:
            st.warning("⚠️ Columnas de Cenabast no identificadas para el cruce.")

    st.subheader("📋 Gestión de Stock Crítico")
    # Limpiamos para mostrar solo lo relevante
    cols_finales = ['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Cenabast']
    st.dataframe(resumen[cols_finales].sort_values('Saldo Meses').style.applymap(
        lambda x: 'background-color: #ff4b4b; color: white' if isinstance(x, float) and x < 0.5 else '', subset=['Saldo Meses']))
