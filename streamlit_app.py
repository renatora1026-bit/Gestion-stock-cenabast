import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN DE IA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra - Inteligencia de Datos", layout="wide")
st.title("🧠 Cerebro Logístico: Indexación y Cruce Semántico")

# MEMORIA DE DATOS (Nuestra base de datos interna temporal)
if 'db_hospital' not in st.session_state:
    st.session_state.db_hospital = None
if 'db_cenabast' not in st.session_state:
    st.session_state.db_cenabast = None

# --- PASO 1: INDEXAR HOSPITAL (SSASUR) ---
st.header("1️⃣ Crear Base de Datos Local (SSASUR)")
f_ssasur = st.file_uploader("Cargar Planilla de Stock/Consumos", type=["csv"], key="u_ssasur")

if f_ssasur and st.button("📥 Paso 1: Extraer y Normalizar"):
    with st.spinner("IA analizando y agrupando conceptos del hospital..."):
        df = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
        # Enviamos los nombres de los productos a la IA para que "entienda" qué son
        lista_productos = df.iloc[:, 0].dropna().unique().tolist() # Asumiendo columna 1 es producto
        
        prompt_norm = f"Analiza esta lista de fármacos y extrae su principio activo puro, sin dosis ni formatos: {lista_productos[:100]}"
        res = model.generate_content(prompt_norm)
        
        st.session_state.db_hospital = df.to_string()
        st.success("✅ Base de datos local creada con éxito.")

# --- PASO 2: INDEXAR CENABAST (ICP) ---
if st.session_state.db_hospital:
    st.divider()
    st.header("2️⃣ Crear Base de Datos Externa (CENABAST)")
    f_cenabast = st.file_uploader("Cargar Planilla CENABAST", type=["csv"], key="u_cenabast")
    
    if f_cenabast and st.button("📥 Paso 2: Extraer y Mapear Marcas"):
        with st.spinner("IA analizando marcas comerciales y genéricos de CENABAST..."):
            # Usamos el separador ';' y saltamos 3 líneas como vimos en tu archivo
            df_c = pd.read_csv(f_cenabast, sep=';', encoding='latin1', skiprows=3)
            # Guardamos el mapeo de Nombre Genérico vs Nombre Comercial
            st.session_state.db_cenabast = df_c[['NOMBRE GENERICO', 'NOMBRE COMERCIAL DEL PRODUCTO', 'ESTADO DEL MATERIAL']].to_string()
            st.success("✅ Base de datos de CENABAST indexada.")

# --- PASO 3: EL CRUCE FINAL ---
if st.session_state.db_hospital and st.session_state.db_cenabast:
    st.divider()
    st.header("3️⃣ Cruce de Información e Inteligencia")
    if st.button("🚀 Ejecutar Cruce Semántico Final"):
        with st.spinner("Cruzando ambas bases de datos..."):
            prompt_final = f"""
            Actúa como un Químico Farmacéutico experto en bases de datos.
            
            BASE DE DATOS HOSPITAL:
            {st.session_state.db_hospital[:15000]}
            
            BASE DE DATOS CENABAST:
            {st.session_state.db_cenabast[:20000]}
            
            TAREA:
            1. Cruza ambas bases de datos. No busques nombres idénticos, busca conceptos (ej: si hospital pide AAS, busca en CENABAST por 'ACIDO ACETILSALICILICO' o 'ASPIRINA').
            2. Genera una tabla: Fármaco Local | Coincidencia en CENABAST (Genérico/Marca) | Estado actual.
            3. Indica si hay discrepancias de nombres para mejorar la base de datos futura.
            """
            
            response = model.generate_content(prompt_final)
            st.subheader("📋 Informe de Abastecimiento Resultante")
            st.markdown(response.text)

# Reinicio
if st.sidebar.button("🗑️ Borrar Bases de Datos"):
    st.session_state.db_hospital = None
    st.session_state.db_cenabast = None
    st.rerun()
