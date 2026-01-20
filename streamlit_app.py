import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE CONEXIÓN ROBUSTA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

def conectar_con_mejor_modelo():
    # Probamos nombres técnicos completos para saltar el error 404
    variantes = [
        "gemini-1.5-flash", 
        "models/gemini-1.5-flash", 
        "gemini-1.5-flash-latest",
        "models/gemini-pro"
    ]
    for v in variantes:
        try:
            m = genai.GenerativeModel(v)
            # Prueba de pulso
            m.generate_content("ok", generation_config={"max_output_tokens": 1})
            return m
        except:
            continue
    return None

st.set_page_config(page_title="Radar Semántico Saavedra", layout="wide")
st.title("🧠 Radar IA: Pensamiento Farmacológico")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- 2. CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 1. Sube SSASUR", type=["csv"])
with col2: f_icp = st.file_uploader("📦 2. Sube CENABAST", type=["csv"])

if f_ssasur and f_icp:
    st.success("✅ Archivos listos para el paso de indexación.")
    
    if st.button("🚀 Iniciar Cruce de Conceptos Inteligentes"):
        with st.spinner('🤖 Gemini creando base de datos semántica...'):
            try:
                # Procesamiento de SSASUR
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(12)
                
                # Leemos CENABAST como conocimiento bruto (Paso solicitado por Renato)
                texto_cenabast = f_icp.getvalue().decode('latin1', errors='ignore')[:25000]

                # Intentar conexión
                ia = conectar_con_mejor_modelo()
                
                if ia:
                    prompt = f"""
                    Actúa como Jefe de Farmacia. Tienes dos tareas:
                    
                    1. ANALIZAR CONTEXTO: En este reporte de CENABAST:
                    {texto_cenabast}
                    Identifica equivalentes semánticos (sinónimos, genéricos, marcas).
                    
                    2. CRUCE INTELIGENTE: Busca estos críticos:
                    {criticos['Producto'].tolist()}
                    
                    Usa tu conocimiento médico: si el hospital pide 'AA SALICILICO', busca 'Aspirina' o 'AAS'. 
                    Si pide 'PARACETAMOL', busca variantes de 500mg o 1g.
                    
                    ENTREGA: Una tabla con: Producto Hospital | Hallazgo Semántico | Estado Real.
                    """
                    response = ia.generate_content(prompt)
                    st.subheader("📋 Informe de Disponibilidad (Cruce Inteligente)")
                    st.markdown(response.text)
                else:
                    st.error("❌ Error 404 persistente: No se encontró un modelo de IA disponible. Revisa la región de tu servidor Streamlit.")
                
                # Respaldo Técnico
                st.divider()
                st.subheader("📉 Resumen Técnico Local (SSASUR)")
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Fallo en el sistema: {e}")
