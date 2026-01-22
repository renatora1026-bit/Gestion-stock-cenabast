import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN DE IA ---
# Usamos 'gemini-1.5-flash-latest' para evitar el error 404 de tu imagen
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

st.set_page_config(page_title="Cerebro Farmacéutico Saavedra", layout="wide")
st.title("🧠 Cerebro Logístico: Creación de Base de Datos Propia")

# --- BASE DE DATOS INTERNA (Memoria de Sesión) ---
if 'memoria_hospital' not in st.session_state:
    st.session_state.memoria_hospital = None
if 'memoria_cenabast' not in st.session_state:
    st.session_state.memoria_cenabast = None

# --- PASO 1: INDEXAR SSASUR ---
st.header("1️⃣ Cargar y Aprender: Hospital (SSASUR)")
f1 = st.file_uploader("Sube el archivo de Stock", type=["csv"], key="ssasur_upload")

if f1 and st.button("📥 Indexar Datos Hospital"):
    try:
        df1 = pd.read_csv(f1, sep=None, engine='python', encoding='latin1')
        # La IA extrae los datos y crea su "base de conocimiento"
        st.session_state.memoria_hospital = df1.to_string()
        st.success("✅ Datos del Hospital guardados en la base de datos interna.")
    except Exception as e:
        st.error(f"Error al indexar hospital: {e}")

# --- PASO 2: INDEXAR CENABAST ---
if st.session_state.memoria_hospital:
    st.divider()
    st.header("2️⃣ Cargar y Aprender: Proveedor (CENABAST)")
    f2 = st.file_uploader("Sube el archivo ICP", type=["csv"], key="cenabast_upload")
    
    if f2 and st.button("📥 Indexar Datos CENABAST"):
        try:
            # Saltamos 3 líneas por los títulos del ICP
            df2 = pd.read_csv(f2, sep=';', encoding='latin1', skiprows=3)
            # Guardamos marcas comerciales y genéricos
            st.session_state.memoria_cenabast = df2[['NOMBRE GENERICO', 'NOMBRE COMERCIAL DEL PRODUCTO', 'ESTADO DEL MATERIAL']].to_string()
            st.success("✅ Datos de CENABAST indexados con éxito.")
        except Exception as e:
            st.error(f"Error al indexar CENABAST: {e}")

# --- PASO 3: CRUCE DE BASES DE DATOS ---
if st.session_state.memoria_hospital and st.session_state.memoria_cenabast:
    st.divider()
    st.header("3️⃣ Cruce Semántico Final")
    if st.button("🚀 Comparar Bases de Datos"):
        with st.spinner("La IA está razonando las equivalencias..."):
            prompt = f"""
            Actúa como un experto en logística farmacéutica.
            
            BASE DATOS A (Hospital):
            {st.session_state.memoria_hospital[:15000]}
            
            BASE DATOS B (CENABAST):
            {st.session_state.memoria_cenabast[:15000]}
            
            TAREA:
            1. Analiza qué fármacos del Hospital faltan (Saldo < 1).
            2. Busca equivalencias en CENABAST por 'NOMBRE COMERCIAL' (Ej: AAS = Aspirina).
            3. Crea una tabla: Producto Local | Coincidencia CENABAST | Estado Entrega.
            4. Destaca si hay SUSPENSIÓN POR DEUDA.
            """
            try:
                response = model.generate_content(prompt)
                st.markdown(response.text)
            except Exception as e:
                st.error(f"Error en el razonamiento de la IA: {e}")

if st.sidebar.button("🗑️ Resetear Cerebro"):
    st.session_state.memoria_hospital = None
    st.session_state.memoria_cenabast = None
    st.rerun()
