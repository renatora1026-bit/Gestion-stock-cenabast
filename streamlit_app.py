import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE CONEXIÓN TOTAL ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Función para encontrar qué modelo está vivo en tu servidor
def obtener_modelo():
    # Probamos nombres comunes para saltar el error 404 de las fotos
    for nombre in ["models/gemini-1.5-flash", "models/gemini-pro", "gemini-1.5-flash", "gemini-pro"]:
        try:
            m = genai.GenerativeModel(nombre)
            # Prueba rápida de conexión
            m.generate_content("hola", generation_config={"max_output_tokens": 1})
            return m
        except:
            continue
    return None

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- 2. CARGA DE DATOS ---
f_ssasur = st.file_uploader("📥 1. Cargar SSASUR", type=["csv"])
f_icp = st.file_uploader("📦 2. Cargar CENABAST", type=["csv"])

if f_ssasur and f_icp:
    # Mostramos que los archivos están listos antes del "paso extra"
    st.success("✅ Archivos cargados. ¿Iniciamos el cruce inteligente?")
    
    if st.button("🔍 ANALIZAR Y CRUZAR DATOS"):
        with st.spinner('🤖 Buscando conexión con Gemini y cruzando datos...'):
            try:
                # Lectura de SSASUR
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(12)
                
                # Paso extra: Lectura de CENABAST como texto para Gemini
                texto_cenabast = f_icp.getvalue().decode('latin1', errors='ignore')[:20000]

                # Intentamos conectar con la IA
                model = obtener_modelo()
                
                if model:
                    prompt = f"""
                    Analiza este reporte de CENABAST:
                    {texto_cenabast}
                    
                    Y busca el estado de estos fármacos: {criticos['Producto'].tolist()}
                    
                    Responde con una tabla: Fármaco | Estado Real | Observación.
                    """
                    response = model.generate_content(prompt)
                    
                    st.subheader("📋 Informe Consolidado")
                    st.markdown(response.text)
                else:
                    st.error("❌ Error 404 persistente: No se encontró un modelo de IA disponible en esta región.")
                
                st.divider()
                st.subheader("📉 Datos Críticos Detectados")
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Error en el proceso: {e}")
