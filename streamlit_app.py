import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE CONEXIÓN MAESTRA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Función para encontrar qué modelo está vivo (evita el error 404 de las capturas)
def encontrar_cerebro_ia():
    # Probamos todas las variantes posibles de nombres
    for nombre in ["gemini-1.5-flash", "gemini-pro", "models/gemini-1.5-flash", "models/gemini-pro"]:
        try:
            m = genai.GenerativeModel(nombre)
            # Prueba de pulso mínima
            m.generate_content("hola", generation_config={"max_output_tokens": 1})
            return m
        except:
            continue
    return None

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown("**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- 2. PASO 1: CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 1. Sube SSASUR", type=["csv"])
with col2: f_icp = st.file_uploader("📦 2. Sube CENABAST", type=["csv"])

if f_ssasur and f_icp:
    st.success("✅ Archivos recibidos. Listos para el paso extra de diagnóstico.")
    
    # --- 3. PASO 2: EL "PASO EXTRA" DE RENATO (ANALIZAR Y CRUZAR) ---
    if st.button("🔍 INICIAR ANÁLISIS Y CRUCE INTELIGENTE"):
        with st.spinner('🤖 Identificando estructura y cruzando datos...'):
            try:
                # Lectura de SSASUR para detectar críticos
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(12)
                
                # Lectura de CENABAST como texto bruto (evita errores de columnas)
                # Tomamos los primeros 20 mil caracteres para el diagnóstico
                texto_cenabast = f_icp.getvalue().decode('latin1', errors='ignore')[:20000]

                # Buscamos la IA
                ia = encontrar_cerebro_ia()
                
                if ia:
                    # Le pedimos a la IA que entienda el archivo y cruce los datos
                    prompt = f"""
                    Eres el experto logístico del Hospital Puerto Saavedra. 
                    Analiza este fragmento de reporte CENABAST:
                    ---
                    {texto_cenabast}
                    ---
                    
                    Cruza esa información con esta lista de fármacos críticos:
                    {criticos['Producto'].tolist()}
                    
                    Genera una tabla clara: Fármaco Hospital | Hallazgo en CENABAST | Estado (Entregado/Pendiente/Sin info).
                    """
                    
                    resultado = ia.generate_content(prompt)
                    
                    st.subheader("📋 Informe Consolidado de Disponibilidad")
                    st.markdown(resultado.text)
                else:
                    st.error("❌ Error Crítico: No se pudo conectar con ningún modelo de IA (404).")
                
                # Respaldo: Mostrar siempre la tabla de SSASUR
                st.divider()
                st.subheader("📉 Resumen Técnico Local (SSASUR)")
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Fallo en el diagnóstico: {e}")
