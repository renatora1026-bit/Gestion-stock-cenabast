import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Radar Saavedra Pro", layout="wide")
st.title("🚀 Sistema de Inteligencia de Inventario")
st.write("Hospital de Puerto Saavedra - Gestión Renato Rozas")

# --- 1. DEFINICIÓN DE BOTONES DE CARGA (Aquí estaba el error) ---
st.header("1. Carga de Planillas")
col1, col2, col3 = st.columns(3)

with col1:
    f_ssasur = st.file_uploader("📥 SSASUR (CSV)", type=["csv"], key="u_ssasur")
with col2:
    f_icp = st.file_uploader("📦 CENABAST (ICP)", type=["csv", "xls", "xlsx"], key="u_icp")
with col3:
    f_arsenal = st.file_uploader("📋 ARSENAL (Excel)", type=["xlsx", "xlsm"], key="u_arsenal")

# --- 2. INICIALIZACIÓN DE VARIABLES ---
data_ssasur = None
data_icp = None
data_arsenal = []

# --- 3. PROCESAMIENTO ---

# Lectura de SSASUR
if f_ssasur:
    try:
        df = pd.read_csv(f_ssasur, sep=";", encoding='latin1')
        df['Saldo Meses'] = pd.to_numeric(df['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
        data_ssasur = df.dropna(subset=['Saldo Meses'])
        st.success("✅ SSASUR cargado")
    except Exception as e:
        st.error(f"Error SSASUR: {e}")

# Lectura de ICP (El "anti-resistencia")
if f_icp:
    try:
        f_icp.seek(0)
        # Probamos primero como HTML por si es el archivo "disfrazado" de Cenabast
        data_icp = pd.read_html(f_icp)[0]
        st.success("✅ ICP sincronizado (Formato Web)")
    except:
        try:
            f_icp.seek(0)
            data_icp = pd.read_excel(f_icp)
            st.success("✅ ICP sincronizado (Excel)")
        except:
            st.error("🚨 El archivo ICP sigue sin dejarse leer. Intenta guardarlo como .xlsx en tu Mac.")

# Lectura de Arsenal
if f_arsenal:
    try:
        df_art = pd.read_excel(f_arsenal)
        # Buscamos la columna de nombre del producto
        col_nom = [c for c in df_art.columns if 'Descrip' in c or 'Artículo' in c][0]
        data_arsenal = df_art[col_nom].astype(str).str.upper().unique()
        st.success("✅ Arsenal sincronizado")
    except Exception as e:
        st.error(f"Error Arsenal: {e}")

# --- 4. RADAR Y FILTROS ---
if data_ssasur is not None:
    st.divider()
    resumen = data_ssasur.copy()
    resumen['Producto'] = resumen['Producto'].str.upper()

    # Filtro de Arsenal
    resumen['Es Arsenal'] = resumen['Producto'].apply(lambda x: "✅" if any(p in x for p in data_arsenal) else "❌")
    
    # Cruce con Fechas de ICP
    if data_icp is not None:
        # Normalizamos nombres de columnas del ICP
        data_icp.columns = [str(c).upper() for c in data_icp.columns]
        col_f = [c for c in data_icp.columns if 'FECHA' in c or 'ENTREGA' in c][0]
        col_p = [c for c in data_icp.columns if 'PRODUCTO' in c or 'DESCRIP' in c][0]
        
        mapa_fechas = pd.Series(data_icp[col_f].values, index=data_icp[col_p].astype(str).str.upper()).to_dict()
        resumen['Llegada'] = resumen['Producto'].map(mapa_fechas).fillna("Sin fecha")
    else:
        resumen['Llegada'] = "Carga ICP"

    # Sidebar
    solo_arsenal = st.sidebar.checkbox("Ver solo Arsenal HBC", value=True)
    if solo_arsenal:
        resumen = resumen[resumen['Es Arsenal'] == "✅"]

    # Dashboard
    col_pie, col_tabla = st.columns([1, 2])
    with col_pie:
        resumen['Status'] = resumen['Saldo Meses'].apply(lambda x: 'CRÍTICO' if x < 0.5 else ('RIESGO' if x < 1.0 else 'OK'))
        fig = px.pie(resumen, names='Status', color='Status', 
                     color_discrete_map={'CRÍTICO':'#ff4b4b', 'RIESGO':'#ffa500', 'OK':'#28a745'})
        st.plotly_chart(fig)

    with col_tabla:
        st.dataframe(resumen[['Producto', 'Saldo Actual', 'Saldo Meses', 'Llegada']].sort_values('Saldo Meses').style.applymap(
            lambda x: 'background-color: #ff4b4b; color: white' if isinstance(x, float) and x < 0.5 else '', subset=['Saldo Meses']))
