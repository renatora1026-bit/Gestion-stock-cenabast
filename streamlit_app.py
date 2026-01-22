import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN DE IA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra Final", layout="wide")
st.title("🧠 Radar de Abastecimiento Puerto Saavedra")

# Usamos memoria de sesión para separar los archivos
if 'archivo_1_datos' not in st.session_state:
    st.session_state.archivo_1_datos = None

# --- BLOQUE 1: SSASUR ---
st.header("1️⃣ Paso: Cargar Consumos (SSASUR)")
f1 = st.file_uploader("Sube el archivo de Stock/Consumos", type=["csv"], key="f1")

if f1 and st.session_state.archivo_1_datos is None:
    if st.button("💾 Guardar Necesidades"):
        try:
            df1 = pd.read_csv(f1, sep=None, engine='python', encoding='latin1')
            # Buscamos cualquier columna que contenga "Producto" y "Saldo"
            col_prod = [c for c in df1.columns if 'Producto' in c][0]
            st.session_state.archivo_1_datos = df1[[col_prod]].head(20).to_string()
            st.success("✅ Necesidades guardadas en memoria.")
            st.rerun()
        except Exception as e:
            st.error(f"Error en Paso 1: {e}")

# --- BLOQUE 2: CENABAST ---
if st.session_state.archivo_1_datos is not None:
    st.divider()
    st.header("2️⃣ Paso: Cargar Reporte CENABAST (ICP)")
    f2 = st.file_uploader("Sube el archivo de CENABAST", type=["csv"], key="f2")
    
    if f2:
        if st.button("🚀 Ejecutar Cruce Inteligente"):
            with st.spinner("Gemini analizando marcas comerciales..."):
                try:
                    # Leemos CENABAST saltando los encabezados
                    df2 = pd.read_csv(f2, sep=';', encoding='latin1', skiprows=3)
                    # Tomamos las columnas de Marca y Estado
                    datos_cenabast = df2[['NOMBRE COMERCIAL DEL PRODUCTO', 'ESTADO DEL MATERIAL']].to_string()
                    
                    prompt = f"""
                    Eres Químico Farmacéutico. Cruza estos datos:
                    
                    LO QUE NOS FALTA: {st.session_state.archivo_1_datos}
                    
                    MARCAS EN CENABAST: {datos_cenabast[:20000]}
                    
                    TAREA:
                    1. Busca qué marca de CENABAST corresponde a nuestros faltantes.
                    2. Haz una tabla: Fármaco Local | Marca CENABAST | Estado.
                    3. Avisa si hay 'SUSPENSION POR DEUDA'.
                    """
                    
                    res = model.generate_content(prompt)
                    st.markdown(res.text)
                except Exception as e:
                    st.error(f"Error en el cruce: {e}")

    if st.sidebar.button("🗑️ Limpiar Memoria"):
        st.session_state.archivo_1_datos = None
        st.rerun()
