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
    f_ssasur = st.file_uploader("Consumo o stock (CSV)", type=["csv"], key="ssasur")

with col2:
    st.subheader("📦 CENABAST")
    f_icp = st.file_uploader("ICP Intermediación/PM", type=["csv", "xlsx"], key="icp")

with col3:
    st.subheader("📋 ARSENAL")
    f_arsenal = st.file_uploader("Arsenal HBC (Excel)", type=["xlsx", "xlsm"], key="arsenal")

# --- PROCESAMIENTO ---
data_ssasur = None
data_icp = None
data_arsenal = []

if f_ssasur:
    try:
        df = pd.read_csv(f_ssasur, sep=";", encoding='latin1')
        df['Saldo Meses'] = pd.to_numeric(df['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
        data_ssasur = df.dropna(subset=['Saldo Meses'])
    except Exception as e:
        st.error(f"Error en SSASUR: {e}")

if f_icp:
    try:
        # Los ICP de Cenabast suelen venir con codificación especial
        data_icp = pd.read_csv(f_icp, sep=";", encoding='latin1')
    except:
        data_icp = pd.read_excel(f_icp)

if f_arsenal:
    df_art = pd.read_excel(f_arsenal, engine='openpyxl')
    data_arsenal = df_art['Descrip. Artículo'].unique() if 'Descrip. Artículo' in df_art.columns else []

# --- VISUALIZACIÓN Y FILTROS ---
if data_ssasur is not None:
    st.divider()
    st.header("2. Radar de Disponibilidad")
    
    # Lógica de Cruce
    resumen = data_ssasur.copy()
    
    # Filtro Arsenal
    resumen['Es Arsenal'] = resumen['Producto'].apply(lambda x: "✅ Sí" if any(str(p).strip() in str(x).strip() for p in data_arsenal) else "❌ No")
    
    # Cruce con ICP para Fechas
    if data_icp is not None:
        # Simplificamos nombres para el cruce
        dict_fechas = pd.Series(data_icp['Fecha Entrega Programada'].values, index=data_icp['Producto']).to_dict()
        resumen['Próxima Entrega'] = resumen['Producto'].map(dict_fechas).fillna("Sin fecha")
    else:
        resumen['Próxima Entrega'] = "No cargado"

    # Filtros laterales
    solo_arsenal = st.sidebar.checkbox("Ver solo mi Arsenal", value=True)
    if solo_arsenal:
        resumen = resumen[resumen['Es Arsenal'] == "✅ Sí"]

    # Gráfico de Torta (Tu nuevo reporte de gestión)
    col_chart, col_table = st.columns([1, 2])
    
    with col_chart:
        resumen['Estatus'] = resumen['Saldo Meses'].apply(lambda x: 'Crítico' if x < 0.5 else ('Riesgo' if x < 1.0 else 'Seguro'))
        fig = px.pie(resumen, names='Estatus', title="Estado del Arsenal HBC", 
                     color='Estatus', color_discrete_map={'Crítico':'#ff4b4b', 'Riesgo':'#ffa500', 'Seguro':'#28a745'})
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        def color_logistico(row):
            if row['Saldo Meses'] < 0.5:
                return ['background-color: #ff4b4b; color: white'] * len(row)
            return [''] * len(row)
            
        st.dataframe(resumen[['Producto', 'Saldo Actual', 'Saldo Meses', 'Es Arsenal', 'Próxima Entrega']].style.apply(color_logistico, axis=1))

else:
    st.info("💡 Para comenzar, carga primero el archivo de SSASUR.")
