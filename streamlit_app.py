import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN DE CONEXIÓN ---
# He cambiado el nombre del modelo a 'gemini-1.5-flash' sin sufijos para mayor estabilidad
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Cerebro Logístico Saavedra", layout="wide")
st.title("🧠 Cerebro de Abastecimiento: Puerto Saavedra")

# --- BASE DE DATOS INTERNA (Memoria de Sesión) ---
if 'base_hospital' not in st.session_state:
    st.session_state.base_hospital = None
if 'base_cenabast' not in st.session_state:
    st.session_state.base_cenabast = None

# --- PASO 1: INDEXAR HOSPITAL (SSASUR) ---
st.header("1️⃣ Paso: Indexar Inventario Hospital")
f1 = st.file_uploader("Sube planilla SSASUR (Consumos)", type=["csv"], key="ssasur")

if f1 and st.button("📥 Indexar Datos Locales"):
    try:
        # Leemos el archivo detectando el separador automáticamente
        df1 = pd.read_csv(f1, sep=None, engine='python', encoding='latin1')
        # Guardamos todo el DataFrame como texto para la base de datos de la IA
        st.session_state.base_hospital = df1.to_string()
        st.success("✅ Datos del Hospital indexados en la base de datos interna.")
    except Exception as e:
        st.error(f"Error al indexar hospital: {e}")

# --- PASO 2: INDEXAR PROVEEDOR (CENABAST) ---
if st.session_state.base_hospital:
    st.divider()
    st.header("2️⃣ Paso: Indexar Catálogo CENABAST")
    f2 = st.file_uploader("Sube planilla ICP CENABAST", type=["csv"], key="cenabast")
    
    if f2 and st.button("📥 Indexar Datos CENABAST"):
        try:
            # Saltamos las 3 líneas de títulos que veo en tus capturas
            df2 = pd.read_csv(f2, sep=';', encoding='latin1', skiprows=3)
            # Solo guardamos columnas clave para no saturar la memoria
            st.session_state.base_cenabast = df2[['NOMBRE GENERICO', 'NOMBRE COMERCIAL DEL PRODUCTO', 'ESTADO DEL MATERIAL']].to_string()
            st.success("✅ Catálogo de CENABAST indexado correctamente.")
        except Exception as e:
            st.error(f"Error al indexar CENABAST: {e}")

# --- PASO 3: CRUCE DE BASES DE DATOS ---
if st.session_state.base_hospital and st.session_state.base_cenabast:
    st.divider()
    st.header("3️⃣ Cruce e Inteligencia de Datos")
    if st.button("🚀 Ejecutar Cruce Semántico"):
        with st.spinner("La IA está analizando equivalencias de nombres y marcas..."):
            # Prompt diseñado para que la IA actúe como tu cerebro de datos
            prompt = f"""
            Actúa como un experto en gestión de stock farmacéutico.
            
            BASE DE DATOS A (Hospital Saavedra):
            {st.session_state.base_hospital[:12000]}
            
            BASE DE DATOS B (CENABAST - Marcas y Estados):
            {st.session_state.base_cenabast[:12000]}
            
            TAREA:
            1. Identifica productos del hospital con 'Saldo Meses' menor a 1.
            2. Busca su equivalente en la base de CENABAST usando 'NOMBRE COMERCIAL' (Ej: AAS = Aspirina).
            3. Entrega una tabla: Fármaco Local | Coincidencia CENABAST | Estado de Entrega.
            4. Alerta si aparece 'APROBADO CON SUSPENSION POR DEUDA'.
            """
            try:
                # Generamos el contenido
                response = model.generate_content(prompt)
                st.markdown("### 📋 Resultados del Cruce Inteligente")
                st.markdown(response.text)
            except Exception as e:
                # Si falla por el 404, mostramos un mensaje claro
                st.error(f"Error de conexión con la IA: {e}. Intenta refrescar la página.")

# Botón para limpiar todo
if st.sidebar.button("🗑️ Resetear Cerebro"):
    st.session_state.base_hospital = None
    st.session_state.base_cenabast = None
    st.rerun()
