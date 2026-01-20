import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

# --- 1. CONFIGURACIÓN IA (CON TU CLAVE) ---
# Usamos tu clave confirmada
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Configuración del modelo corregida para evitar el Error 404
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- 2. CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 SSASUR (CSV)", type=["csv"])
with col2: f_icp = st.file_uploader("📦 CENABAST (CSV o Excel)", type=["csv", "xlsx"])

# --- 3. FUNCIÓN DE CRUCE SEMÁNTICO ---
def consultar_ia_estado(producto, contexto_icp):
    """Gemini analiza la coincidencia entre SSASUR y CENABAST"""
    prompt = f"""
    Eres un Químico Farmacéutico chileno. 
    Busca este fármaco: '{producto}' en la siguiente lista de CENABAST:
    {contexto_icp}
    
    Responde solo con: ENTREGADO, APROBADO, EN CURSO o NO EN LISTA.
    """
    try:
        # Usamos generate_content con el nombre de modelo corregido
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return "Pendiente de validación"

# --- 4. PROCESAMIENTO ---
if f_ssasur and f_icp:
    with st.spinner('🤖 Inteligencia Artificial analizando stock crítico...'):
        try:
            # Procesar SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # Cargar contexto de Cenabast (primeras 50 filas para velocidad)
            if f_icp.name.endswith('csv'):
                df_c = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip').head(50)
            else:
                df_c = pd.read_excel(f_icp).head(50)
            
            contexto_icp = df_c.to_string()

            # Analizar solo los que tienen saldo bajo
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().head(10)
            
            if not criticos.empty:
                st.subheader("⚠️ Análisis IA de Stock Crítico")
                criticos['Estado Real (Cenabast)'] = criticos['Producto'].apply(
                    lambda x: consultar_ia_estado(x, contexto_icp)
                )
                
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real (Cenabast)']].style.applymap(
                    lambda x: 'background-color: #ff4b4b; color: white' if x == 'NO EN LISTA' else '', 
                    subset=['Estado Real (Cenabast)']
                ))
            else:
                st.success("✅ Stock saludable según registros.")
                
        except Exception as e:
            st.error(f"Error técnico: {e}")
