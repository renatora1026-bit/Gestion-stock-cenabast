import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONEXIÓN REFORZADA (Evita Error 404) ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

def obtener_cerebro():
    # Probamos variantes para saltar el error 404 de las capturas
    for m_name in ["gemini-1.5-flash", "gemini-pro", "models/gemini-1.5-flash"]:
        try:
            m = genai.GenerativeModel(m_name)
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m
        except: continue
    return None

st.set_page_config(page_title="Radar Semántico Saavedra", layout="wide")
st.title("🧠 Radar IA: Pensamiento Farmacológico")
st.markdown("Hospital Puerto Saavedra | Gestión Semántica de Stock")

# --- 2. CARGA Y PROCESAMIENTO INDIVIDUAL ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 1. Cargar SSASUR", type=["csv"])
with col2: f_icp = st.file_uploader("📦 2. Cargar CENABAST", type=["csv"])

if f_ssasur and f_icp:
    if st.button("🚀 Iniciar Cruce de Conceptos Inteligentes"):
        with st.spinner('🤖 Gemini creando base de datos semántica...'):
            try:
                # Paso A: Limpieza de nombres locales
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(12)
                
                # Paso B: La IA "lee" CENABAST y genera su propia base de equivalencias
                texto_cenabast = f_icp.getvalue().decode('latin1', errors='ignore')[:25000]
                
                cerebro = obtener_cerebro()
                if cerebro:
                    prompt = f"""
                    Actúa como un experto Químico Farmacéutico.
                    
                    DATOS CENABAST:
                    {texto_cenabast}
                    
                    TAREA:
                    Busca equivalentes para estos fármacos críticos: {criticos['Producto'].tolist()}
                    
                    INSTRUCCIÓN DE PENSAMIENTO:
                    - Si el hospital pide 'AA SALICILICO', busca 'Aspirina', 'AAS', 'Ácido Acetilsalicílico'.
                    - Si pide 'PARACETAMOL', busca marcas comerciales o combinaciones.
                    - Genera una tabla: Fármaco Local | Equivalente en CENABAST | Estado (Semaforo) | Nota.
                    """
                    
                    resultado = cerebro.generate_content(prompt)
                    st.subheader("📋 Resultado del Análisis Semántico")
                    st.markdown(resultado.text)
                else:
                    st.error("❌ Error de Conexión (404): No se pudo encontrar un modelo de IA activo.")

                st.divider()
                st.subheader("📉 Resumen Técnico Local")
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Error en el proceso: {e}")
