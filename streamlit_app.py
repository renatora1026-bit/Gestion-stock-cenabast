import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE CONEXIÓN REFORZADA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Usamos este bloque para asegurar que el modelo cargue sí o sí
try:
    model = genai.GenerativeModel('gemini-1.5-flash-latest') # Agregamos '-latest'
except:
    model = genai.GenerativeModel('gemini-1.5-pro')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- 2. CARGA DE ARCHIVOS ---
f_ssasur = st.file_uploader("📥 1. Cargar SSASUR", type=["csv"])
f_icp = st.file_uploader("📦 2. Cargar CENABAST", type=["csv"])

if f_ssasur and f_icp:
    if st.button("🔍 Ejecutar Análisis de Disponibilidad"):
        with st.spinner('🤖 Procesando cruce de datos...'):
            try:
                # Lectura de SSASUR
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                
                # Identificamos los 10 más críticos
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(10)
                
                # Lectura de CENABAST (como texto para evitar errores de columnas)
                texto_cenabast = f_icp.getvalue().decode('latin1', errors='ignore')
                resumen_cenabast = texto_cenabast[:15000] # Muestra de seguridad

                # --- 3. CONSULTA DE CRUCE ---
                prompt = f"""
                Actúa como experto en farmacia hospitalaria. Analiza este listado de CENABAST:
                {resumen_cenabast}
                
                Y dime el estado de estos productos críticos de mi hospital:
                {criticos['Producto'].tolist()}
                
                Entrega una respuesta clara en formato tabla: 
                Producto Hospital | Hallazgo en CENABAST | Estado (Entregado/Pendiente/Sin Info).
                """

                # Generamos contenido con manejo de errores de conexión
                try:
                    response = model.generate_content(prompt)
                    st.subheader("📋 Resultado del Cruce Inteligente")
                    st.markdown(response.text)
                except Exception as e_api:
                    st.error(f"La IA está temporalmente ocupada o el modelo no responde: {e_api}")
                
                st.divider()
                st.subheader("📉 Resumen de Stock Crítico (SSASUR)")
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Error al leer archivos: {e}")
