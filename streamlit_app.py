import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN ESTABLE ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Usamos 'gemini-pro' para evitar el error 404 de las capturas
model = genai.GenerativeModel('gemini-pro')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- 2. CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 1. Cargar SSASUR", type=["csv"])
with col2: f_icp = st.file_uploader("📦 2. Cargar CENABAST", type=["csv"])

if f_ssasur and f_icp:
    # Botón de acción para el "paso extra" que sugeriste
    if st.button("🔍 Iniciar Análisis y Cruce Inteligente"):
        with st.spinner('🤖 Gemini analizando estructuras y cruzando datos...'):
            try:
                # Lectura de SSASUR
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                
                # Identificamos los críticos
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(12)
                lista_hospital = criticos['Producto'].tolist()

                # Leemos CENABAST como texto para que la IA lo "vea" directamente
                texto_cenabast = f_icp.getvalue().decode('latin1', errors='ignore')
                resumen_cenabast = texto_cenabast[:25000] # Tomamos una muestra amplia

                # --- 3. EL CRUCE INTELIGENTE ---
                prompt = f"""
                Actúa como Jefe de Logística. Te entrego dos fuentes de datos.
                
                1. REPORTE CENABAST (Texto Bruto):
                {resumen_cenabast}
                
                2. LISTA DE FÁRMACOS CRÍTICOS DEL HOSPITAL:
                {lista_hospital}
                
                TAREA:
                - Busca cada fármaco de la lista en el reporte de CENABAST.
                - Identifica su estado (Ej: Entregado, Pendiente, Suspendido o Sin Información).
                - Presenta los resultados en una TABLA con: Fármaco | Estado Real | Observación Logística.
                """

                response = model.generate_content(prompt)

                # --- 4. RESULTADOS ---
                st.subheader("📋 Informe de Disponibilidad Real (IA)")
                st.markdown(response.text)
                
                st.divider()
                st.subheader("📉 Datos de Origen (SSASUR)")
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Error de sistema: {e}")
                st.info("Prueba recargar la página y subir los archivos nuevamente.")
