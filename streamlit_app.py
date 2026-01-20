import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE SEGURIDAD ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Función para probar múltiples nombres de modelo (evita el error 404)
def conectar_ia():
    modelos_a_probar = ["gemini-1.5-flash", "gemini-pro"]
    for m_name in modelos_a_probar:
        try:
            m = genai.GenerativeModel(m_name)
            # Prueba de vida mínima
            m.generate_content("test", generation_config={"max_output_tokens": 1})
            return m
        except:
            continue
    return None

st.set_page_config(page_title="Radar Saavedra v4", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown("**Hospital Puerto Saavedra** | Gestión de Stock Crítico")

# --- 2. CARGA DE ARCHIVOS ---
f_ssasur = st.file_uploader("📥 1. Sube SSASUR (CSV)", type=["csv"])
f_icp = st.file_uploader("📦 2. Sube CENABAST (CSV)", type=["csv"])

if f_ssasur and f_icp:
    st.success("✅ Archivos listos para el cruce inteligente.")
    
    if st.button("🔍 ANALIZAR DISPONIBILIDAD REAL"):
        with st.spinner('🤖 Procesando datos y conectando con Gemini...'):
            try:
                # Procesar SSASUR
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                
                # Filtrar los 12 más críticos
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(12)
                lista_busqueda = criticos['Producto'].tolist()

                # Leer CENABAST como texto (para evitar el error de columnas)
                texto_cenabast = f_icp.getvalue().decode('latin1', errors='ignore')[:25000]

                # Intentar conexión con la IA
                ia = conectar_ia()
                
                if ia:
                    prompt = f"""
                    Analiza este reporte de CENABAST:
                    {texto_cenabast}
                    
                    Busca el estado de estos productos: {lista_busqueda}
                    Responde con una tabla: Producto | Estado en CENABAST | Detalle.
                    Si no está, pon 'Sin info'.
                    """
                    resultado = ia.generate_content(prompt)
                    st.subheader("📋 Informe de Disponibilidad Real")
                    st.markdown(resultado.text)
                else:
                    st.error("❌ Error de Conexión: La IA no responde. Revisa la versión de la librería en requirements.txt")
                
                # Siempre mostrar la tabla de SSASUR como respaldo
                st.divider()
                st.subheader("📉 Resumen de Stock Local (SSASUR)")
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Fallo en el procesamiento: {e}")
