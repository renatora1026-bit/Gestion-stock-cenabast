import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

# --- 1. CONFIGURACIÓN IA (CON TU CLAVE) ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Ajuste de seguridad para evitar el "Error de Conexión"
generation_config = {
  "temperature": 0,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 100,
}

# Desactivamos filtros de seguridad para términos médicos
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    safety_settings=safety_settings
)

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- 2. CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 SSASUR (CSV)", type=["csv"])
with col2: f_icp = st.file_uploader("📦 CENABAST (CSV o Excel)", type=["csv", "xlsx"])

# --- 3. FUNCIÓN DE CRUCE SEMÁNTICO CON IA ---
def consultar_ia_estado(producto, contexto_icp):
    """Gemini analiza si el producto existe aunque cambie el nombre"""
    prompt = f"""
    Actúa como un Químico Farmacéutico chileno. 
    Revisa si este fármaco de SSASUR: '{producto}' 
    está presente en esta lista de CENABAST:
    {contexto_icp}
    
    Responde ÚNICAMENTE con una de estas opciones: 
    ENTREGADO, APROBADO, EN CURSO o NO EN LISTA.
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)[:20]}"

# --- 4. PROCESAMIENTO ---
if f_ssasur and f_icp:
    with st.spinner('🤖 Gemini está analizando los fármacos críticos...'):
        try:
            # Procesar SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # Procesar CENABAST (Primeras 80 filas para darle más contexto)
            if f_icp.name.endswith('csv'):
                df_c = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip').head(80)
            else:
                df_c = pd.read_excel(f_icp).head(80)
            
            contexto_icp = df_c.to_string()

            # Analizamos los Críticos (< 0.5 meses)
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy()
            
            if not criticos.empty:
                st.subheader("⚠️ Análisis IA de Stock Crítico")
                # Limitamos a los primeros 10 para evitar saturar la API en la prueba
                criticos = criticos.head(10) 
                criticos['Estado Real (Cenabast)'] = criticos['Producto'].apply(
                    lambda x: consultar_ia_estado(x, contexto_icp)
                )
                
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real (Cenabast)']].style.applymap(
                    lambda x: 'background-color: #ff4b4b; color: white' if x == 'NO EN LISTA' else '', 
                    subset=['Estado Real (Cenabast)']
                ))
            else:
                st.success("✅ Todo bajo control.")
                
        except Exception as e:
            st.error(f"Error técnico: {e}")
