import streamlit as st
import pandas as pd
import google.generativeai as genai
from google.generativeai.types import RequestOptions

# --- CONEXIÓN DE ALTA COMPATIBILIDAD ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Usamos el nombre base sin sufijos beta para máxima estabilidad
# Esto soluciona el fallo de tus fotos (image_d9c846.jpg)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra v5", layout="wide")
st.title("🧠 Radar IA: Cruce Semántico Estabilizado")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 1. Stock SSASUR", type=["csv"])
with col2: f_cenabast = st.file_uploader("📦 2. Reporte CENABAST", type=["csv"])

if f_ssasur and f_cenabast:
    st.success("✅ Archivos listos para el análisis semántico.")
    
    if st.button("🚀 EJECUTAR PENSAMIENTO FARMACÉUTICO"):
        with st.spinner('🤖 Gemini analizando variables (v1 Stable)...'):
            try:
                # 1. Procesar SSASUR (Priorizando críticos como Fluoxetina/Penicilina)
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                # Nos enfocamos en los saldos negativos de tus capturas (image_da2257.jpg)
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(12)
                
                # 2. Cargar contexto de CENABAST
                texto_cenabast = f_cenabast.getvalue().decode('latin1', errors='ignore')[:30000]

                # 3. Lógica de "Mapeo Mental" solicitado por Renato
                prompt = f"""
                Actúa como un Jefe de Farmacia experto. 
                
                CONOCIMIENTO CENABAST:
                {texto_cenabast}
                
                NECESIDADES CRÍTICAS:
                {criticos['Producto'].tolist()}
                
                TAREA:
                - Genera sinónimos y variables semánticas para cada crítico.
                - Localiza estos conceptos en el reporte de CENABAST.
                - Reporta: Ítem Hospital | Match en CENABAST | Estado de Compra.
                """

                # Forzamos la petición a través de la versión estable de la API
                response = model.generate_content(
                    prompt, 
                    request_options=RequestOptions(retry=None)
                )
                
                st.subheader("📋 Informe de Disponibilidad Inteligente")
                st.markdown(response.text)
                
                st.divider()
                st.subheader("📉 Resumen Técnico Local (SSASUR)")
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Error de conexión persistente: {e}")
                st.info("Si el error 404 continúa, ve al panel lateral de Streamlit y haz clic en 'Reboot App'.")
