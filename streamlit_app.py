import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
# Usamos 1.5-flash porque es más rápido para analizar bloques grandes de texto
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI v3", layout="wide")
st.title("🚀 Radar de Abastecimiento Inteligente")
st.markdown(f"**Hospital Puerto Saavedra** | Sistema de Cruce Semántico")

# --- 1. CARGA INDIVIDUAL ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 Fuente 1: SSASUR")
    f_ssasur = st.file_uploader("Subir stock local", type=["csv"], key="ssasur")

with col2:
    st.subheader("📦 Fuente 2: CENABAST")
    f_icp = st.file_uploader("Subir reporte ICP", type=["csv"], key="cenabast")

if f_ssasur and f_icp:
    if st.button("🧠 Iniciar Procesamiento con Pensamiento IA"):
        with st.spinner('🤖 Gemini está "leyendo" y entendiendo tus archivos...'):
            try:
                # Paso 1: Extraer texto de SSASUR para identificar críticos
                df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
                df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                criticos = df_s[df_s['Saldo Meses'] < 0.5].sort_values('Saldo Meses').head(15)
                lista_hospital = criticos['Producto'].tolist()

                # Paso 2: Extraer texto de CENABAST (como bloque de conocimiento)
                texto_cenabast = f_icp.getvalue().decode('latin1', errors='ignore')[:25000]

                # Paso 3: El "Pensamiento" de Gemini
                # Aquí le pedimos que haga el mapeo mental que tú sugeriste
                prompt = f"""
                Eres un Químico Farmacéutico experto en bases de datos.
                
                CONTEXTO CENABAST (Datos brutos):
                {texto_cenabast}
                
                LISTA DE NECESIDADES DEL HOSPITAL:
                {lista_hospital}
                
                TAREA:
                1. Analiza los nombres en la lista del hospital.
                2. Busca sus equivalentes en el texto de CENABAST, considerando sinónimos, nombres genéricos, 
                   abreviaturas (ej: AA Salicilico = Aspirina) y errores de digitación.
                3. Para cada acierto, extrae el ESTADO o SEMAFORO.
                
                ENTREGA:
                Una tabla comparativa con: Fármaco Hospital | Nombre encontrado en CENABAST | Estado Real | Acción sugerida.
                """

                response = model.generate_content(prompt)

                # Visualización del resultado
                st.divider()
                st.subheader("📋 Informe de Cruce Semántico (IA)")
                st.markdown(response.text)
                
                with st.expander("Ver datos técnicos procesados"):
                    st.write("Fármacos críticos detectados en SSASUR:", lista_hospital)
                    st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses']])

            except Exception as e:
                st.error(f"Hubo un problema al procesar los archivos: {e}")
