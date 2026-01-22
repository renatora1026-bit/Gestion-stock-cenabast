import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN DE CONEXIÓN ULTRA-ESTABLE ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)

# Función para listar y conectar con el modelo vivo
def conectar_ia():
    try:
        # Forzamos la versión flash que es la más compatible actualmente
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config={"temperature": 0.1}
        )
        # Prueba de conexión rápida
        model.generate_content("test", generation_config={"max_output_tokens": 1})
        return model
    except Exception as e:
        # Si falla, intentamos con el nombre largo técnico
        try:
            return genai.GenerativeModel('models/gemini-1.5-flash')
        except:
            st.error(f"Error Crítico de Conexión: {e}")
            return None

st.set_page_config(page_title="Radar Semántico v2", layout="wide")
st.title("🧠 Radar de Abastecimiento Inteligente")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- 2. CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 1. Stock Local (SSASUR)", type=["csv"])
with col2: f_cenabast = st.file_uploader("📦 2. Disponibilidad (CENABAST)", type=["csv"])

if f_ssasur and f_cenabast:
    # Mostramos el "Paso de Indexación" que propusiste
    st.success("✅ Archivos listos para el análisis de variables.")
    
    if st.button("🔍 INICIAR INDEXACIÓN Y CRUCE SEMÁNTICO"):
        with st.spinner('🤖 Gemini está "pensando" las equivalencias...'):
            try:
                # Procesamos SSASUR para buscar los críticos de tus capturas
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                
                # Tomamos los 15 más críticos (como la Fluoxetina y Penicilina de tu foto)
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(15)
                lista_nombres = criticos['Producto'].tolist()

                # Leemos CENABAST como "base de conocimiento"
                texto_cenabast = f_cenabast.getvalue().decode('latin1', errors='ignore')[:30000]

                # Conexión con la IA
                ia = conectar_ia()
                
                if ia:
                    prompt = f"""
                    Eres un experto en farmacia hospitalaria chilena.
                    
                    CONTEXTO CENABAST:
                    {texto_cenabast}
                    
                    PRODUCTOS A BUSCAR:
                    {lista_nombres}
                    
                    TAREA:
                    1. Para cada producto, genera sus sinónimos (ej: AA Salicilico = Aspirina = AAS).
                    2. Busca coincidencias en el contexto de CENABAST usando estos sinónimos.
                    3. Devuelve una tabla con: Fármaco Hospital | Match en CENABAST | Estado.
                    """
                    
                    respuesta = ia.generate_content(prompt)
                    st.subheader("📋 Informe de Cruce de Variables")
                    st.markdown(respuesta.text)
                
                # Siempre mostrar la tabla local por seguridad
                st.divider()
                st.subheader("📉 Resumen Técnico Local (SSASUR)")
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Fallo en el procesamiento de datos: {e}")
