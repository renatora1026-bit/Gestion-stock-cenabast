import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Radar Saavedra Pro", layout="wide")
st.title("🚀 Radar de Abastecimiento - Hospital Puerto Saavedra")

# --- 1. CARGA DE ARCHIVOS ---
st.header("1. Carga de Planillas")
col1, col2, col3 = st.columns(3)

with col1:
    f_ssasur = st.file_uploader("📥 SSASUR (CSV)", type=["csv"], key="u_ssasur")
with col2:
    f_icp = st.file_uploader("📦 CENABAST (ICP)", type=["csv", "xls", "xlsx"], key="u_icp")
with col3:
    f_arsenal = st.file_uploader("📋 ARSENAL (Excel)", type=["xlsx", "xlsm"], key="u_arsenal")

data_ssasur = None
data_icp = None
data_arsenal = []

# --- 2. PROCESAMIENTO SSASUR ---
if f_ssasur:
    try:
        df = pd.read_csv(f_ssasur, sep=";", encoding='latin1')
        df['Saldo Meses'] = pd.to_numeric(df['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
        data_ssasur = df.dropna(subset=['Saldo Meses'])
        st.success("✅ SSASUR cargado")
    except Exception as e:
        st.error(f"Error SSASUR: {e}")

# --- 3. PROCESAMIENTO ICP (El "Rompe-Muros") ---
if f_icp:
    try:
        f_icp.seek(0)
        # Intentamos leerlo decodificando el texto (UTF-8 o Latin-1)
        # Esto soluciona el problema de los archivos de portales viejos
        contenido = f_icp.read()
        try:
            decoded = contenido.decode('utf-8')
        except:
            decoded = contenido.decode('latin-1')
        
        # Forzamos la lectura de tablas desde el texto decodificado
        tablas = pd.read_html(io.StringIO(decoded))
        data_icp = tablas[0]
        st.success("✅ ICP sincronizado (Fuerza Bruta exitosa)")
    except:
        try:
            f_icp.seek(0)
            data_icp = pd.read_excel(f_icp)
            st.success("✅ ICP sincronizado (Modo Excel)")
        except:
            st.warning("⚠️ CENABAST bloqueado. Renato, última opción: Ábrelo en tu Mac y 'Guarda como CSV (delimitado por comas)'")

# --- 4. PROCESAMIENTO ARSENAL ---
if f_arsenal:
    try:
        df_art = pd.read_excel(f_arsenal)
        col_nom = [c for c in df_art.columns if 'Descrip' in c or 'Art' in c][0]
        data_arsenal = df_art[col_nom].astype(str).str.upper().unique()
        st.success("✅ Arsenal sincronizado")
    except:
        st.error("Error en Arsenal.")

# --- 5. VISUALIZACIÓN ---
if data_ssasur is not None:
    st.divider()
    resumen = data_ssasur.copy()
    resumen['Producto'] = resumen['Producto'].str.upper()

    # Filtro Arsenal
    resumen['Es Arsenal'] = resumen['Producto'].apply(lambda x: "✅" if any(p in str(x) for p in data_arsenal) else "❌")
    
    # Cruce con ICP
    if data_icp is not None:
        data_icp.columns = [str(c).upper() for c in data_icp.columns]
        c_prod = [c for c in data_icp.columns if 'PRODUCTO' in c or 'DESCRIP' in c][0]
        c_fecha = [c for c in data_icp.columns if 'FECHA' in c or 'ENTREGA' in c or 'PROGRAMADA' in c][0]
        mapa = pd.Series(data_icp[c_fecha].values, index=data_icp[c_prod].astype(str).str.upper()).to_dict()
        resumen['Próxima Entrega'] = resumen['Producto'].map(mapa).fillna("Ver portal")
    else:
        resumen['Próxima Entrega'] = "Carga ICP"

    if st.sidebar.checkbox("Ver solo Arsenal HBC", value=True):
        resumen = resumen[resumen['Es Arsenal'] == "✅"]

    st.subheader("📋 Gestión de Stock Crítico")
    st.dataframe(resumen[['Producto', 'Saldo Actual', 'Saldo Meses', 'Próxima Entrega']].sort_values('Saldo Meses').style.applymap(
        lambda x: 'background-color: #ff4b4b; color: white' if isinstance(x, float) and x < 0.5 else '', subset=['Saldo Meses']))
