import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- PASO 1: CARGA ---
f_ssasur = st.file_uploader("📥 1. Cargar SSASUR (CSV)", type=["csv"])
f_icp = st.file_uploader("📦 2. Cargar CENABAST (CSV)", type=["csv"])

if f_ssasur and f_icp:
    # Botón para iniciar el proceso de "Reconocimiento y Cruce"
    if st.button("🔍 Analizar y Cruzar Datos"):
        with st.spinner('🤖 Paso 1: Gemini reconociendo estructura de archivos...'):
            try:
                # Lectura inicial bruta
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                # Limpiar saldo meses de una vez
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                
                # Leer los primeros pedazos de CENABAST para que la IA los reconozca
                texto_cenabast_muestreo = f_icp.getvalue().decode('latin1', errors='ignore')[:10000]
                
                # --- PASO 2: LA IA MAPEA EL ARCHIVO ---
                mapa_prompt = f"""
                Analiza este fragmento de archivo CSV de CENABAST:
                {texto_cenabast_muestreo}
                
                Dime: ¿En qué columna (número) están los nombres de los fármacos y en cuáles el estado o semáforo?
                Luego, basándote en eso, analiza estos fármacos críticos de mi hospital:
                {df_s[df_s['Saldo Meses'] < 0.5]['Producto'].head(15).tolist()}
                
                Genera un informe detallado con el estado de cada uno.
                """
                
                response = model.generate_content(mapa_prompt)
                
                # --- PASO 3: MOSTRAR RESULTADOS ---
                st.success("✅ Análisis completado con éxito")
                
                col_inf, col_dat = st.columns([2, 1])
                
                with col_inf:
                    st.subheader("📋 Informe de Gestión CENABAST (vía Gemini)")
                    st.markdown(response.text)
                
                with col_dat:
                    st.subheader("📉 Datos Críticos SSASUR")
                    st.dataframe(df_s[df_s['Saldo Meses'] < 0.5][['Producto', 'Saldo Actual', 'Saldo Meses']].head(15))

            except Exception as e:
                st.error(f"Error en el proceso: {e}")
