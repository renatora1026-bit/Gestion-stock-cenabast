import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN DE IA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("💊 Radar de Gestión Farmacéutica")

# Inicializamos la memoria de la sesión
if 'paso_1_listo' not in st.session_state:
    st.session_state.paso_1_listo = False
if 'necesidades_hospital' not in st.session_state:
    st.session_state.necesidades_hospital = ""

# --- BLOQUE 1: CARGAR CONSUMOS ---
st.header("1️⃣ Paso: Analizar Faltantes (SSASUR)")
f_ssasur = st.file_uploader("Sube el archivo de Consumos o Stock (Paso Inicial)", type=["csv"], key="ssasur_step")

if f_ssasur and not st.session_state.paso_1_listo:
    if st.button("🧐 Procesar Necesidades y Guardar"):
        df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
        df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
        
        # Filtramos críticos para que la IA se enfoque en lo urgente
        criticos = df_s[df_s['Saldo Meses'] < 0.8].sort_values('Saldo Meses')
        
        # Guardamos en la memoria de la IA
        st.session_state.necesidades_hospital = criticos[['Producto', 'Saldo Meses']].to_string()
        st.session_state.paso_1_listo = True
        st.rerun() 

# --- BLOQUE 2: CARGAR CENABAST ---
if st.session_state.paso_1_listo:
    st.success("✅ Paso 1 completado: La IA ya recuerda tus necesidades.")
    st.header("2️⃣ Paso: Buscar en Catálogo CENABAST")
    f_cenabast = st.file_uploader("Sube ahora el archivo ICP de CENABAST", type=["csv"], key="cenabast_step")

    if f_cenabast:
        if st.button("🚀 Ejecutar Cruce por Nombre Comercial"):
            with st.spinner("Gemini buscando marcas y estados en el ICP..."):
                try:
                    # Leemos CENABAST saltando el encabezado (skiprows=3 como vimos en tu archivo)
                    df_c = pd.read_csv(f_cenabast, sep=';', encoding='latin1', skiprows=3)
                    
                    # Usamos 'NOMBRE COMERCIAL DEL PRODUCTO' para que la IA identifique el fármaco
                    # Incluimos 'ESTADO DEL MATERIAL' para ver si está suspendido por deuda
                    info_cenabast = df_c[['NOMBRE COMERCIAL DEL PRODUCTO', 'ESTADO DEL MATERIAL', 'CANTIDAD UNITARIA A DESPACHAR']].to_string()
                    
                    prompt = f"""
                    Actúa como Químico Farmacéutico del Hospital Puerto Saavedra.
                    
                    MEMORIA DEL HOSPITAL (Lo que nos falta):
                    {st.session_state.necesidades_hospital}
                    
                    CATÁLOGO CENABAST (Nombres comerciales y estados):
                    {info_cenabast[:28000]}
                    
                    TAREA:
                    1. Identifica qué 'NOMBRE COMERCIAL DEL PRODUCTO' en CENABAST corresponde a lo que nos falta.
                    2. Crea una tabla resumen: Fármaco Local | Marca en CENABAST | Estado de Entrega | Cantidad.
                    3. Agrega una nota de alerta roja si ves productos 'APROBADO CON SUSPENSION POR DEUDA'.
                    """
                    
                    response = model.generate_content(prompt)
                    st.subheader("📋 Informe Final de Gestión de Abastecimiento")
                    st.markdown(response.text)
                    
                    if st.button("🔄 Empezar de nuevo (Limpiar Memoria)"):
                        st.session_state.paso_1_listo = False
                        st.rerun()

                except Exception as e:
                    st.error(f"Error en el cruce: {e}")
else:
    st.info("💡 Primero debes subir y procesar el archivo SSASUR en el Paso 1 para que la IA 'sepa' qué buscar en CENABAST.")
