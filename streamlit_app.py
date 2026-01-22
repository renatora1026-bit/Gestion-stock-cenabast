import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("💊 Radar de Gestión: Mapeo por Nombre Comercial")

if 'conocimiento_hospital' not in st.session_state:
    st.session_state.conocimiento_hospital = None

# --- PASO 1: INDEXAR SSASUR ---
st.header("1️⃣ Paso: Necesidades del Hospital (SSASUR)")
f_ssasur = st.file_uploader("Subir Stock/Consumo", type=["csv"], key="ssasur_v2")

if f_ssasur:
    if st.button("🧐 Indexar Fármacos Locales"):
        df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
        df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
        # Filtramos críticos para que la IA no se pierda en datos irrelevantes
        criticos = df_s[df_s['Saldo Meses'] < 0.8].sort_values('Saldo Meses')
        st.session_state.conocimiento_hospital = criticos[['Producto', 'Saldo Actual', 'Saldo Meses']].to_string()
        st.success(f"✅ Se indexaron {len(criticos)} ítems críticos.")

# --- PASO 2: CRUCE POR NOMBRE COMERCIAL ---
if st.session_state.conocimiento_hospital:
    st.divider()
    st.header("2️⃣ Paso: Cruce con Catálogo CENABAST")
    f_cenabast = st.file_uploader("Subir Archivo CENABAST (ICP)", type=["csv"], key="icp_v2")

    if f_cenabast:
        if st.button("🚀 Ejecutar Mapeo Comercial"):
            with st.spinner("IA analizando marcas y moléculas..."):
                try:
                    # El archivo CENABAST tiene 3 líneas de título antes de la cabecera
                    df_c = pd.read_csv(f_cenabast, sep=';', encoding='latin1', skiprows=3)
                    
                    # Extraemos la columna que tú definiste como clave
                    # Usamos 'NOMBRE COMERCIAL DEL PRODUCTO' y 'ESTADO DEL MATERIAL'
                    columnas_clave = ['NOMBRE COMERCIAL DEL PRODUCTO', 'ESTADO DEL MATERIAL', 'CANTIDAD UNITARIA A DESPACHAR']
                    contexto_comercial = df_c[columnas_clave].to_string()
                    
                    prompt = f"""
                    Eres un Químico Farmacéutico analizando el abastecimiento.
                    
                    MISIÓN:
                    Buscar los siguientes fármacos del Hospital en la lista comercial de CENABAST.
                    
                    FÁRMACOS SOLICITADOS (Desde SSASUR):
                    {st.session_state.conocimiento_hospital}
                    
                    CATÁLOGO COMERCIAL CENABAST:
                    {contexto_comercial[:28000]}
                    
                    INSTRUCCIONES DE RAZONAMIENTO:
                    1. Si el hospital pide 'AAS' o 'A.A.S', búscalo en CENABAST por su nombre comercial (ej. 'ASPIRINA').
                    2. Si el hospital pide 'VITAMINA D', búscalo como 'COLEKAL' u otros nombres comerciales que veas en la lista.
                    3. Genera una respuesta clara: Fármaco Local -> Nombre Comercial Encontrado -> Estado en CENABAST.
                    """
                    
                    response = model.generate_content(prompt)
                    st.subheader("📋 Resultados del Cruce Semántico")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"Error en el cruce comercial: {e}")

# --- FILOSOFÍA DE TRABAJO ---
st.sidebar.info("Renato: Al usar el 'Nombre Comercial', la IA puede detectar si un producto ya viene en camino bajo una marca específica, facilitando tu gestión de recepción.")
