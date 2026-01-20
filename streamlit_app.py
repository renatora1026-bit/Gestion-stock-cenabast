import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Radar Saavedra Pro", layout="wide")
st.title("🚀 Sistema de Inteligencia de Inventario")
st.write("Hospital de Puerto Saavedra - Gestión Renato Rozas")

# --- CARGA DE PLANILLAS ---
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

# --- PROCESAMIENTO SSASUR ---
if f_ssasur:
    try:
        df = pd.read_csv(f_ssasur, sep=";", encoding='latin1')
        df['Saldo Meses'] = pd.to_numeric(df['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
        data_ssasur = df.dropna(subset=['Saldo Meses'])
        st.success("✅ SSASUR cargado")
    except Exception as e:
        st.error(f"Error en SSASUR: {e}")

# --- PROCESAMIENTO ICP (Aquí está la magia anti-errores) ---
if f_icp:
    try:
        # Intento 1: Excel estándar
        data_icp = pd.read_excel(f_icp)
    except:
        try:
            # Intento 2: Como HTML (Formato común de exportaciones Cenabast)
            f_icp.seek(0)
            data_icp = pd.read_html(f_icp)[0]
        except:
            try:
                # Intento 3: CSV con punto y coma
                f_icp.seek(0)
                data_icp = pd.read_csv(f_icp, sep=";", encoding='latin1')
            except:
                st.error("⚠️ El formato de este ICP es inusual. Prueba guardándolo como '.xlsx' en tu PC antes de subirlo.")

    if data_icp is not None:
        st.success("✅ ICP Cenabast cargado")

# --- PROCESAMIENTO ARSENAL ---
if f_arsenal:
    try:
        df_art = pd.read_excel(f_arsenal, engine='openpyxl')
        # Buscamos la columna de descripción (ajustar si el nombre cambia)
        col_desc = [c for c in df_art.columns if 'Descrip' in c or 'Producto' in c]
        if col_desc:
            data_arsenal = df_art[col_desc[0]].unique()
            st.success("✅ Arsenal cargado")
    except Exception as e:
        st.error(f"Error en Arsenal: {e}")

# --- VISUALIZACIÓN ---
if data_ssasur is not None:
    st.divider()
    resumen = data_ssasur.copy()
    
    # Marcamos qué es de Arsenal
    resumen['Es Arsenal'] = resumen['Producto'].apply(lambda x: "✅" if any(str(p).strip().lower() in str(x).strip().lower() for p in data_arsenal) else "❌")
    
    # Cruzamos con fechas de ICP
    if data_icp is not None:
        col_fecha = [c for c in data_icp.columns if 'Fecha' in c]
        if col_fecha:
            # Diccionario de Producto -> Fecha para cruce rápido
            dict_fechas = pd.Series(data_icp[col_fecha[0]].values, index=data_icp['Producto']).to_dict()
            resumen['Próxima Entrega'] = resumen['Producto'].map(dict_fechas).fillna("Sin fecha")
        else:
            resumen['Próxima Entrega'] = "No hay columna de fecha"
    else:
        resumen['Próxima Entrega'] = "Carga ICP para ver"

    # Filtros laterales
    st.sidebar.header("Opciones")
    solo_arsenal = st.sidebar.checkbox("Ver solo mi Arsenal", value=True)
    if solo_arsenal:
        resumen = resumen[resumen['Es Arsenal'] == "✅"]

    # Semáforo y Gráfico
    col_chart, col_table = st.columns([1, 2])
    with col_chart:
        resumen['Estatus'] = resumen['Saldo Meses'].apply(lambda x: 'Crítico' if x < 0.5 else ('Riesgo' if x < 1.0 else 'Seguro'))
        fig = px.pie(resumen, names='Estatus', color='Estatus', color_discrete_map={'Crítico':'#ff4b4b', 'Riesgo':'#ffa500', 'Seguro':'#28a745'})
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.subheader("📋 Plan de Acción Logístico")
        st.dataframe(resumen[['Producto', 'Saldo Actual', 'Saldo Meses', 'Es Arsenal', 'Próxima Entrega']].sort_values('Saldo Meses').style.applymap(
            lambda x: 'background-color: #ff4b4b; color: white' if isinstance(x, float) and x < 0.5 else '', subset=['Saldo Meses']))
