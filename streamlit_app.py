import streamlit as st
import pandas as pd
import google.generativeai as genai
import os

# --- CONFIGURACIÓN DE CONEXIÓN ---
# Usamos la configuración estándar para evitar el error de versión v1beta
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Definimos el modelo de forma estable
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Cerebro Logístico Saavedra", layout="wide")
st.title("🧠 Cerebro de Abastecimiento: Puerto Saavedra")

# --- BASE DE DATOS INTERNA (Session State) ---
if 'db_hospital' not in st.session_state:
    st.session_state.db_hospital = None
if 'db_cenabast' not in st.session_state:
    st.session_state.db_cenabast = None

# --- PASO 1: CARGA E INDEXACIÓN ---
st.header("1️⃣ Cargar y Aprender Planillas")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Hospital (SSASUR)")
    f1 = st.file_uploader("Sube resumenConsumo.csv", type=["csv"], key="u_ssasur")
    if f1:
        try:
            # Leemos detectando el separador automáticamente
            df1 = pd.read_csv(f1, sep=None, engine='python', encoding='latin1')
            st.session_state.db_hospital = df1.to_string()
            st.success("✅ Datos locales indexados.")
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    st.subheader("CENABAST (ICP)")
    f2 = st.file_uploader("Sube ICP-Intermediacion.csv", type=["csv"], key="u_cenabast")
    if f2:
        try:
            # Saltamos 3 líneas y usamos ; como detectamos en tus archivos
            df2 = pd.read_csv(f2, sep=';', encoding='latin1', skiprows=3)
            # Guardamos solo lo vital para el cruce (Genérico, Marca y Estado)
            st.session_state.db_cenabast = df2[['NOMBRE GENERICO', 'NOMBRE COMERCIAL DEL PRODUCTO', 'ESTADO DEL MATERIAL']].to_string()
            st.success("✅ Catálogo CENABAST indexado.")
        except Exception as e:
            st.error(f"Error: {e}")

# --- PASO 2: EL CRUCE SEMÁNTICO (EL "CEREBRO") ---
if st.session_state.db_hospital and st.session_state.db_cenabast:
    st.divider()
    st.header("2️⃣ Ejecutar Inteligencia de Cruce")
    
    if st.button("🚀 Iniciar Cruce de Bases de Datos"):
        with st.spinner("La IA está razonando las equivalencias comerciales..."):
            
            # El "Cerebro" recibe ambas bases de datos indexadas
            prompt = f"""
            Actúa como Jefe de Farmacia del Hospital Puerto Saavedra. 
            Cruza estas dos bases de datos internas que hemos indexado:
            
            DATOS HOSPITAL:
            {st.session_state.db_hospital[:10000]}
            
            DATOS CENABAST:
            {st.session_state.db_cenabast[:10000]}
            
            TAREA:
            1. Analiza los productos del hospital con stock crítico.
            2. Busca el 'NOMBRE COMERCIAL' equivalente en la base de CENABAST (Ej: Vitamina D -> COLEKAL).
            3. Genera una tabla con: Fármaco Hospital | Coincidencia CENABAST | Estado actual.
            4. Reporta de forma destacada cualquier 'SUSPENSION POR DEUDA'.
            """
            
            try:
                # Generación de contenido con la sintaxis más estable
                response = model.generate_content(prompt)
                st.markdown("### 📋 Resultados del Análisis Inteligente")
                st.markdown(response.text)
            except Exception as e:
                st.error("⚠️ Error crítico en la conexión con el cerebro de IA.")
                st.info(f"Detalle: {e}")

if st.sidebar.button("🗑️ Resetear Memoria"):
    st.session_state.db_hospital = None
    st.session_state.db_cenabast = None
    st.rerun()
