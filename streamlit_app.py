import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN IA ---
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

# --- 3. PROCESAMIENTO ---
if f_ssasur and f_icp:
    with st.spinner('🤖 Inteligencia Artificial analizando estados...'):
        try:
            # Procesar SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # Procesar CENABAST - Extraemos solo texto clave para que la IA no se maree
            if f_icp.name.endswith('csv'):
                df_c = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip').head(100)
            else:
                df_c = pd.read_excel(f_icp).head(100)
            
            # Creamos una lista simplificada para la IA
            contexto_reducido = df_c.to_string(index=False)

            # Filtramos solo los críticos (< 0.5) para el análisis
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy()
            
            if not criticos.empty:
                st.subheader("⚠️ Análisis IA de Stock Crítico")
                
                # Función de consulta optimizada
                def obtener_estado_real(prod):
                    prompt = f"Basado en esta lista:\n{contexto_reducido}\n\n¿Cuál es el ESTADO de '{prod}'? Responde solo la palabra del estado."
                    try:
                        res = model.generate_content(prompt)
                        return res.text.strip().upper()
                    except:
                        return "CONSULTAR MANUAL"

                # Aplicamos a los primeros 15 más urgentes
                criticos = criticos.sort_values('Saldo Meses').head(15)
                criticos['Estado Real (Cenabast)'] = criticos['Producto'].apply(obtener_estado_real)
                
                # Resultado visual
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real (Cenabast)']].style.applymap(
                    lambda x: 'background-color: #1e3d59; color: white' if x != 'CONSULTAR MANUAL' else '',
                    subset=['Estado Real (Cenabast)']
                ))
            else:
                st.success("✅ Stock al día.")
                
        except Exception as e:
            st.error(f"Ajuste necesario: {e}")
