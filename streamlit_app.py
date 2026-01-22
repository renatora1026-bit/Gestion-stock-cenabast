import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN DE CONEXIÓN ROBUSTA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Probamos con la versión más estable del modelo para evitar el error 404
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Cerebro Logístico Saavedra", layout="wide")
st.title("🧠 Cerebro de Abastecimiento: Puerto Saavedra")

# --- BASE DE DATOS INTERNA (Session State) ---
if 'base_hospital' not in st.session_state:
    st.session_state.base_hospital = None
if 'base_cenabast' not in st.session_state:
    st.session_state.base_cenabast = None

# --- PASO 1: CARGA DE DATOS (SIN LLAMAR A IA AÚN) ---
st.header("1️⃣ Paso: Cargar Planillas para Indexar")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Hospital (SSASUR)")
    f1 = st.file_uploader("Sube resumenConsumo.csv", type=["csv"], key="ssasur")
    if f1:
        try:
            df1 = pd.read_csv(f1, sep=None, engine='python', encoding='latin1')
            st.session_state.base_hospital = df1.to_string()
            st.success("✅ Datos locales cargados.")
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    st.subheader("Proveedor (CENABAST)")
    f2 = st.file_uploader("Sube ICP-Intermediacion.csv", type=["csv"], key="cenabast")
    if f2:
        try:
            # Saltamos las 3 líneas de títulos que veo en tus capturas
            df2 = pd.read_csv(f2, sep=';', encoding='latin1', skiprows=3)
            # Limpiamos nombres de columnas
            df2.columns = df2.columns.str.strip()
            st.session_state.base_cenabast = df2[['NOMBRE GENERICO', 'NOMBRE COMERCIAL DEL PRODUCTO', 'ESTADO DEL MATERIAL']].to_string()
            st.success("✅ Catálogo CENABAST cargado.")
        except Exception as e:
            st.error(f"Error: {e}")

# --- PASO 2: EL CRUCE INTELIGENTE ---
if st.session_state.base_hospital and st.session_state.base_cenabast:
    st.divider()
    st.header("2️⃣ Generar Análisis y Cruce de Datos")
    st.info("La IA comparará ahora ambas bases de datos internas para encontrar equivalencias comerciales.")
    
    if st.button("🚀 Iniciar Cruce Semántico"):
        with st.spinner("La IA está razonando las equivalencias (esto puede tardar 10-15 segundos)..."):
            # Prompt optimizado para que la IA actúe como tu cerebro de datos
            prompt = f"""
            Actúa como el Jefe de Farmacia del Hospital Puerto Saavedra. 
            Tienes dos bases de datos que acabamos de cargar:
            
            BASE HOSPITAL:
            {st.session_state.base_hospital[:15000]}
            
            BASE CENABAST:
            {st.session_state.base_cenabast[:15000]}
            
            TAREA:
            1. Cruza la información. Busca productos que el Hospital necesite (Saldo Meses bajo).
            2. Busca su 'NOMBRE COMERCIAL' en CENABAST (Ej: Si el hospital pide Vitamina D, busca 'COLEKAL').
            3. Crea una tabla con: Producto Hospital | Marca en CENABAST | Estado de Entrega.
            4. Reporta cualquier 'SUSPENSION POR DEUDA' detectada.
            """
            try:
                # Llamada directa al modelo
                response = model.generate_content(prompt)
                st.markdown("### 📋 Resultados del Cruce de Bases de Datos")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Error de API: {e}. Intenta guardar el código de nuevo.")

# Botón de reset
if st.sidebar.button("🗑️ Resetear Bases de Datos"):
    st.session_state.base_hospital = None
    st.session_state.base_cenabast = None
    st.rerun()
