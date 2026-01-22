import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN IA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("💊 Radar de Abastecimiento: Hospital Puerto Saavedra")

# Usamos session_state para que los datos sobrevivan al cambio de archivo
if 'criticos_texto' not in st.session_state:
    st.session_state.criticos_texto = None

# --- PASO 1: SSASUR ---
st.header("1️⃣ Paso: Analizar Stock Local (SSASUR)")
f_ssasur = st.file_uploader("Sube el archivo de Stock o Consumos", type=["csv"], key="ssasur")

if f_ssasur and st.session_state.criticos_texto is None:
    if st.button("🧐 Procesar e Identificar Quiebres"):
        try:
            # Leemos intentando detectar el separador automáticamente
            df = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            
            # Buscamos la columna de Saldo sin importar mayúsculas
            col_saldo = [c for c in df.columns if 'saldo' in c.lower() and 'mes' in c.lower()]
            col_prod = [c for c in df.columns if 'producto' in c.lower() or 'articulo' in c.lower()]
            
            if col_saldo and col_prod:
                df[col_saldo[0]] = pd.to_numeric(df[col_saldo[0]].astype(str).str.replace(',', '.'), errors='coerce')
                # Filtramos críticos
                criticos = df[df[col_saldo[0]] < 0.8].sort_values(col_saldo[0])
                st.session_state.criticos_texto = criticos[[col_prod[0], col_saldo[0]]].to_string()
                st.success(f"✅ Se identificaron {len(criticos)} productos críticos. Pasando al Paso 2...")
                st.rerun()
            else:
                st.error("No encontré las columnas necesarias (Producto o Saldo Meses).")
        except Exception as e:
            st.error(f"Error leyendo SSASUR: {e}")

# --- PASO 2: CENABAST ---
if st.session_state.criticos_texto:
    st.divider()
    st.header("2️⃣ Paso: Cruzar con Disponibilidad CENABAST")
    f_cenabast = st.file_uploader("Sube el archivo ICP de CENABAST", type=["csv"], key="cenabast")
    
    if f_cenabast:
        if st.button("🚀 Ejecutar Cruce por Nombre Comercial"):
            with st.spinner("Gemini analizando marcas comerciales y estados..."):
                try:
                    # Cargamos el ICP saltando las líneas de título (usamos skiprows=4 para ir directo a los datos)
                    df_c = pd.read_csv(f_cenabast, sep=';', encoding='latin1', skiprows=3)
                    
                    # Extraemos las columnas clave que vimos en tu archivo
                    contexto = df_c[['NOMBRE COMERCIAL DEL PRODUCTO', 'ESTADO DEL MATERIAL']].to_string()
                    
                    prompt = f"""
                    Actúa como Químico Farmacéutico.
                    
                    PRODUCTOS EN QUIEBRE (Hospital):
                    {st.session_state.criticos_texto}
                    
                    DATOS CENABAST (Marcas y Estados):
                    {contexto[:28000]}
                    
                    TAREA:
                    1. Busca qué 'NOMBRE COMERCIAL' de la lista de CENABAST corresponde a los fármacos que nos faltan.
                    2. Haz una tabla: Fármaco Local | Marca en CENABAST | Estado de Entrega.
                    3. Si ves que dice 'SUSPENSION POR DEUDA', ponlo en negrita.
                    """
                    
                    response = model.generate_content(prompt)
                    st.subheader("📋 Informe de Gestión de Abastecimiento")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"Error en el cruce: {e}")

    if st.sidebar.button("🗑️ Reiniciar Todo"):
        st.session_state.criticos_texto = None
        st.rerun()
