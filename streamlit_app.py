import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE CONEXIÓN (NOMBRE COMPLETO PARA EVITAR 404) ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Usamos el nombre técnico completo que requiere la API v1beta
MODELO_ESTABLE = "models/gemini-1.5-flash-latest"

st.set_page_config(page_title="Radar Semántico Saavedra", layout="wide")
st.title("🧠 Radar IA: Pensamiento Farmacológico")
st.markdown("Hospital Puerto Saavedra | Gestión Semántica de Stock")

# --- 2. CARGA DE ARCHIVOS ---
f_ssasur = st.file_uploader("📥 1. Cargar SSASUR", type=["csv"])
f_icp = st.file_uploader("📦 2. Cargar CENABAST", type=["csv"])

if f_ssasur and f_icp:
    st.success("✅ Archivos listos para el paso de indexación.")
    
    # --- 3. EL PASO EXTRA: PENSAMIENTO IA ---
    if st.button("🚀 Iniciar Cruce de Conceptos Inteligentes"):
        with st.spinner('🤖 Gemini creando base de datos semántica...'):
            try:
                # Procesamiento de SSASUR
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(12)
                
                # Leemos CENABAST como conocimiento bruto
                texto_cenabast = f_icp.getvalue().decode('latin1', errors='ignore')[:30000]

                # Llamada a la IA
                model = genai.GenerativeModel(MODELO_ESTABLE)
                
                prompt = f"""
                Actúa como Jefe de Farmacia. Tienes dos tareas:
                
                1. ANALIZAR CONTEXTO: En este texto de CENABAST:
                {texto_cenabast}
                Identifica qué nombres corresponden a fármacos y sus estados.
                
                2. CRUCE SEMÁNTICO: Busca equivalencias para estos críticos:
                {criticos['Producto'].tolist()}
                
                Usa tu conocimiento médico: si el hospital pide 'AA SALICILICO', busca 'Aspirina' o 'AAS'. 
                Si pide 'PENICILINA G SODICA', busca variantes inyectables.
                
                ENTREGA: Una tabla con: Producto Hospital | Hallazgo Semántico | Estado Real.
                """

                response = model.generate_content(prompt)
                
                st.subheader("📋 Informe de Disponibilidad (Cruce Inteligente)")
                st.markdown(response.text)
                
                # Respaldo Técnico
                st.divider()
                st.subheader("📉 Resumen Técnico Local (SSASUR)")
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Fallo en el sistema: {e}")
                st.info("Asegúrate de que la API Key sea válida y el modelo esté disponible.")
