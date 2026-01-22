import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN DE IA ---
# Usamos tu API Key y un sistema de conexión robusto
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

def get_model():
    # Probamos el modelo más estable para evitar errores 404
    try:
        return genai.GenerativeModel('gemini-1.5-flash')
    except:
        return genai.GenerativeModel('gemini-pro')

st.set_page_config(page_title="Radar Semántico Saavedra", layout="wide")
st.title("🧠 Radar de Abastecimiento: Inteligencia Semántica")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- PASO 1: CARGA E INDEXACIÓN ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 1. Stock Hospital (SSASUR)")
    f_ssasur = st.file_uploader("Subir archivo de stock", type=["csv"], key="ssasur")

with col2:
    st.subheader("📦 2. Disponibilidad (CENABAST)")
    f_cenabast = st.file_uploader("Subir reporte CENABAST", type=["csv"], key="cenabast")

if f_ssasur and f_cenabast:
    st.info("✅ Archivos cargados. Gemini está listo para indexar los conceptos.")
    
    if st.button("🚀 Iniciar Cruce Semántico Inteligente"):
        with st.spinner('🤖 Analizando variables y creando equivalencias...'):
            try:
                # Lectura de datos
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                # Limpiamos 'Saldo Meses' para identificar críticos
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(15)
                
                # Preparamos el "conocimiento" para la IA
                lista_hospital = criticos['Producto'].tolist()
                texto_cenabast = f_cenabast.getvalue().decode('latin1', errors='ignore')[:25000]

                model = get_model()
                
                # EL PROMPT MAESTRO: Aquí ocurre la "magia" que pediste
                prompt = f"""
                Actúa como un Químico Farmacéutico experto en informática médica.
                
                TAREA 1: Analiza esta lista de fármacos críticos del Hospital: {lista_hospital}.
                Genera mentalmente sus variables (sinónimos, nombres genéricos y abreviaturas comunes en Chile).
                
                TAREA 2: Escanea este reporte de CENABAST:
                ---
                {texto_cenabast}
                ---
                
                TAREA 3: Cruza la información. No busques coincidencias exactas de texto. 
                Busca coincidencias de CONCEPTO (ej: si el hospital pide 'AAS' y CENABAST tiene 'A. Acetilsalicilico', es un match).
                
                PRESENTACIÓN:
                Devuelve una tabla con estas columnas:
                1. Fármaco Solicitado (Hospital)
                2. Hallazgo en CENABAST (Nombre exacto que aparece allá)
                3. Estado/Semáforo
                4. Nota de la IA (Ej: "Coincidencia por sinónimo", "No encontrado", etc.)
                """

                response = model.generate_content(prompt)

                # --- RESULTADOS ---
                st.divider()
                st.subheader("📋 Informe de Disponibilidad por Conceptos")
                st.markdown(response.text)
                
                with st.expander("Ver detalle técnico de SSASUR"):
                    st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Error en el procesamiento: {e}")
                st.info("Tip: Asegúrate de que los archivos CSV no estén abiertos en Excel al subirlos.")

# --- SECCIÓN DE FILOSOFÍA DE GESTIÓN (Bonus Bryan Tracy) ---
st.sidebar.markdown("---")
st.sidebar.subheader("💡 Mentalidad de Gestión")
st.sidebar.info("'La calidad de tu vida depende de la calidad de tu gestión del tiempo y tus prioridades.' - Bryan Tracy. \n\nUsa este radar para enfocarte en el 20% de fármacos que causan el 80% del impacto clínico.")
