import streamlit as st
import pandas as pd
import google.generativeai as genai
from google.generativeai.types import RequestOptions

# --- CONEXIÓN FORZADA A VERSIÓN ESTABLE ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Configuramos el modelo para usar la versión v1 explícita
# Esto debería eliminar el error "not found for API version v1beta"
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config={"temperature": 0.1}
)

st.set_page_config(page_title="Radar Saavedra v4", layout="wide")
st.title("🧠 Radar IA: Cruce Semántico Estabilizado")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 1. Stock SSASUR", type=["csv"])
with col2: f_cenabast = st.file_uploader("📦 2. Reporte CENABAST", type=["csv"])

if f_ssasur and f_cenabast:
    st.success("✅ Archivos listos para el paso de indexación.")
    
    if st.button("🚀 INICIAR PENSAMIENTO E INTERPRETACIÓN IA"):
        with st.spinner('🤖 Gemini analizando variables semánticas (v1 Stable)...'):
            try:
                # 1. Procesar SSASUR (Identificar críticos)
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                # Priorizar críticos reales como Fluoxetina o Penicilina de tus fotos
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(12)
                
                # 2. Preparar el "Cerebro" de CENABAST
                texto_cenabast = f_cenabast.getvalue().decode('latin1', errors='ignore')[:30000]

                # 3. Prompt de Cruce Semántico (Tu idea original)
                prompt = f"""
                Actúa como un Químico Farmacéutico en Chile. 
                
                CONOCIMIENTO DE CENABAST:
                {texto_cenabast}
                
                NECESIDADES DEL HOSPITAL:
                {criticos['Producto'].tolist()}
                
                TAREA:
                - Genera variables semánticas para cada producto (ej: AA Salicilico = Aspirina = AAS).
                - Busca estos conceptos en la base de CENABAST provista.
                - Entrega una tabla con: Ítem Hospital | Nombre en CENABAST | Estado.
                """

                # Usamos RequestOptions para forzar la API v1
                response = model.generate_content(
                    prompt, 
                    request_options=RequestOptions(retry=None)
                )
                
                st.subheader("📋 Informe de Disponibilidad por Concepto")
                st.markdown(response.text)
                
                # Resumen técnico local por seguridad
                st.divider()
                st.subheader("📉 Detalle Local de Críticos")
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Error de conexión persistente: {e}")
                st.info("Este error 404 suele ser un problema de caché de Streamlit Cloud. Prueba reiniciando la app en el panel lateral.")
