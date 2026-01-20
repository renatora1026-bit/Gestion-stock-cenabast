import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Radar Saavedra Pro", layout="wide")
st.title("🚀 Sistema de Inteligencia de Inventario")
st.write("Hospital de Puerto Saavedra - Área de Abastecimiento")

# --- SECCIÓN DE CARGA ORGANIZADA ---
st.header("1. Carga de Planillas")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📥 SSASUR")
    f_ssasur = st.file_uploader("Reporte Consumo (CSV)", type=["csv"], key="ssasur")

with col2:
    st.subheader("📦 CENABAST")
    f_icp = st.file_uploader("ICP Intermediación/PM", type=["csv", "xls", "xlsx"], key="icp")

with col3:
    st.subheader("📋 ARSENAL")
    f_arsenal = st.file_uploader("Arsenal HBC (Excel)", type=["xlsx", "xlsm"], key="arsenal")

# --- VARIABLES DE DATOS ---
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

# --- PROCESAMIENTO ICP (Aquí corregimos el error de la imagen) ---
if f_icp:
    try:
        # Intento 1: Como Excel normal
        data_icp = pd.read_excel(f_icp)
    except:
        try:
            # Intento 2: Como el formato HTML/Texto que suele exportar Cenabast
            f_icp.seek(0) # Volver al inicio del archivo
            data_icp = pd.read_html(f_icp)[0]
        except:
            try:
                # Intento 3: Como CSV con punto y coma
                f_icp.seek(0)
                data_icp = pd.read_csv(f_icp, sep=";", encoding='latin1')
            except Exception as e:
                st.error(f"No pudimos descifrar el formato de Cenabast. Intenta guardarlo como 'Excel Libro' (.xlsx) en tu PC antes de subirlo.")
    
    if data_icp is not None:
        st.success("✅ ICP Cenabast cargado")

# --- PROCESAMIENTO ARSENAL ---
if f_arsenal:
    try:
        df_art = pd.read_excel(f_arsenal, engine='openpyxl')
        data_arsenal = df_art['Descrip. Artículo'].unique() if 'Descrip. Artículo' in df_art.columns else []
        st.success("✅ Arsenal cargado")
    except Exception as e:
        st.error(f"Error en Arsenal: {e}")

# --- RADAR Y GRÁFICOS ---
if data_ssasur is not None:
    st.divider()
    resumen = data_ssasur.copy()
    
    # Marcamos Arsenal
    resumen['Es Arsenal'] = resumen['Producto'].apply(lambda x: "✅ Sí" if any(str(p).strip().lower() in str(x).strip().lower() for p in data_arsenal) else "❌ No")
    
    # Buscamos fechas en ICP
    if data_icp is not None:
        # Intentamos encontrar la columna de fecha (Cenabast suele llamarla 'Fecha Entrega Programada')
        col_fecha = [c for c in data_icp.columns if 'Fecha' in c]
        if col_fecha:
            # Creamos un mapa de Producto -> Fecha
            dict_fechas = pd.Series(data_icp[col_fecha[0]].values, index=data_icp['Producto']).to_dict()
            resumen['Próxima Entrega'] = resumen['Producto'].map(dict_fechas).fillna("Sin fecha")
        else:
            resumen['Próxima Entrega'] = "No hay columna de fecha"
    else:
        resumen['Próxima Entrega'] = "Carga ICP para ver"

    # Filtros y Semáforo
    st.sidebar.header("Opciones")
    solo_arsenal = st.sidebar.checkbox("Ver solo Arsenal", value=True)
    if solo_arsenal:
        resumen = resumen[resumen['Es Arsenal'] == "✅ Sí"]

    col_chart, col_table = st.columns([1, 2])
    with col_chart:
        resumen['Estatus'] = resumen['Saldo Meses'].apply(lambda x: 'Crítico' if x < 0.5 else ('Riesgo' if x < 1.0 else 'Seguro'))
        fig = px.pie(resumen, names='Estatus', color='Estatus', color_discrete_map={'Crítico':'#ff4b4b', 'Riesgo':'#ffa500', 'Seguro':'#28a745'})
        st.plotly_chart(fig)

    with col_table:
        st.dataframe(resumen[['Producto', 'Saldo Actual', 'Saldo Meses', 'Próxima Entrega']].style.applymap(
            lambda x: 'background-color: #ff4b4b; color: white' if isinstance(x, float) and x < 0.5 else '', subset=['Saldo Meses']))
