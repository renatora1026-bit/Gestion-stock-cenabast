import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

# --- 1. CONFIGURACIÓN IA (CON TU CLAVE) ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

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
    Eres un Q.F. experto en logística. Revisa si '{producto}' está en esta lista de CENABAST:
    {contexto_icp}
    
    Responde solo con el ESTADO (ej: ENTREGADO, APROBADO, NO EN LISTA). 
    Sé flexible con los nombres (ej: 'PNC' es 'PENICILINA').
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "Error de Conexión"

# --- 4. PROCESAMIENTO ---
if f_ssasur and f_icp:
    with st.spinner('🤖 Gemini está cruzando los datos...'):
        try:
            # Procesar SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # Procesar CENABAST (IA lee las primeras 50 filas)
            if f_icp.name.endswith('csv'):
                df_c = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip').head(50)
            else:
                df_c = pd.read_excel(f_icp).head(50)
            
            contexto_icp = df_c.to_string()

            # Solo aplicar IA a los Críticos (< 0.5 meses) para que sea rápido
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy()
            
            if not criticos.empty:
                st.subheader("⚠️ Análisis IA de Stock Crítico")
                criticos['Estado Real (Cenabast)'] = criticos['Producto'].apply(
                    lambda x: consultar_ia_estado(x, contexto_icp)
                )
                
                # Mostrar resultados
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real (Cenabast)']].style.applymap(
                    lambda x: 'background-color: #ff4b4b; color: white' if x == 'NO EN LISTA' else '', 
                    subset=['Estado Real (Cenabast)']
                ))
            else:
                st.success("✅ Todo bajo control. No hay stock crítico inmediato.")
                
        except Exception as e:
            st.error(f"Error en el proceso: {e}")
