import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN DE CONEXIÓN ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Usamos el nombre de modelo más universal para evitar el 404
MODEL_NAME = 'gemini-1.5-flash'

st.set_page_config(page_title="Radar Saavedra v3", layout="wide")
st.title("🧠 Radar IA: Pensamiento Farmacológico")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- CARGA DE DATOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 1. Stock SSASUR", type=["csv"])
with col2: f_cenabast = st.file_uploader("📦 2. Archivo CENABAST", type=["csv"])

if f_ssasur and f_cenabast:
    st.success("✅ Archivos listos para el paso de indexación.")
    
    if st.button("🚀 Iniciar Cruce de Conceptos Inteligentes"):
        with st.spinner('🤖 Gemini analizando variables semánticas...'):
            try:
                # Procesar Stock Local (SSASUR)
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                # Priorizamos fármacos críticos como Fluoxetina o Penicilina de tus fotos
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(12)
                
                # Cargar conocimiento de CENABAST (Paso de indexación solicitado)
                # Leemos los primeros 30k caracteres para no saturar la conexión
                conocimiento_cenabast = f_cenabast.getvalue().decode('latin1', errors='ignore')[:30000]

                # Llamada a la IA con lógica de Químico Farmacéutico
                model = genai.GenerativeModel(MODEL_NAME)
                
                prompt = f"""
                Eres el Jefe de Farmacia del Hospital Puerto Saavedra. 
                
                CONOCIMIENTO DISPONIBLE (CENABAST):
                {conocimiento_cenabast}
                
                PRODUCTOS CRÍTICOS A GESTIONAR:
                {criticos['Producto'].tolist()}
                
                TAREA:
                1. Analiza semánticamente los críticos. (Ej: 'AA SALICILICO' es 'Aspirina' o 'AAS').
                2. Busca estos conceptos en el conocimiento de CENABAST.
                3. Genera un informe con: Producto Hospital | Hallazgo en CENABAST | Estado Real.
                """

                response = model.generate_content(prompt)
                
                st.subheader("📋 Informe de Disponibilidad (Cruce Inteligente)")
                st.markdown(response.text)
                
                st.divider()
                st.subheader("📉 Detalle Técnico Local")
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Error de conexión: {e}")
                st.info("Asegúrate de haber actualizado el archivo requirements.txt en GitHub.")
