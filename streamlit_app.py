import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN IA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("💊 Radar de Abastecimiento: Hospital Puerto Saavedra")

# Usamos session_state para que los datos no se borren al subir el segundo archivo
if 'criticos_texto' not in st.session_state:
    st.session_state.criticos_texto = None

# --- PASO 1: SSASUR (STOCK LOCAL) ---
st.header("1️⃣ Paso: Analizar Necesidades (SSASUR)")
f_ssasur = st.file_uploader("Sube el archivo de Stock o Consumos", type=["csv"], key="ssasur")

if f_ssasur and st.session_state.criticos_texto is None:
    if st.button("🧐 Procesar e Identificar Críticos"):
        try:
            # Detección automática de separador
            df = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            
            # Buscamos columnas de forma inteligente (sin importar mayúsculas)
            col_saldo = [c for c in df.columns if 'saldo' in c.lower() and 'mes' in c.lower()]
            col_prod = [c for c in df.columns if 'producto' in c.lower() or 'articulo' in c.lower()]
            
            if col_saldo and col_prod:
                df[col_saldo[0]] = pd.to_numeric(df[col_saldo[0]].astype(str).str.replace(',', '.'), errors='coerce')
                # Filtramos productos con menos de 1 mes de stock
                criticos = df[df[col_saldo[0]] < 1.0].sort_values(col_saldo[0])
                st.session_state.criticos_texto = criticos[[col_prod[0], col_saldo[0]]].to_string()
                st.success(f"✅ Se identificaron {len(criticos)} ítems críticos. ¡Ahora puedes subir CENABAST!")
                st.rerun()
            else:
                st.error("No encontré columnas de 'Producto' o 'Saldo Meses'. Revisa tu archivo.")
        except Exception as e:
            st.error(f"Error en Paso 1: {e}")

# --- PASO 2: CENABAST (CRUCE SEMÁNTICO) ---
if st.session_state.criticos_texto:
    st.divider()
    st.header("2️⃣ Paso: Cruzar con Disponibilidad CENABAST (ICP)")
    f_cenabast = st.file_uploader("Sube el archivo ICP de CENABAST", type=["csv"], key="cenabast")
    
    if f_cenabast:
        if st.button("🚀 Ejecutar Cruce por Nombre Comercial"):
            with st.spinner("Gemini analizando marcas y estados..."):
                try:
                    # Leemos CENABAST saltando las 3 líneas de título detectadas en tu archivo
                    df_c = pd.read_csv(f_cenabast, sep=';', encoding='latin1', skiprows=3)
                    
                    # Seleccionamos columnas comerciales para el cruce
                    contexto = df_c[['NOMBRE GENERICO', 'NOMBRE COMERCIAL DEL PRODUCTO', 'ESTADO DEL MATERIAL']].to_string()
                    
                    prompt = f"""
                    Eres el Jefe de Farmacia. Cruza estos datos:
                    
                    QUIEBRES HOSPITAL:
                    {st.session_state.criticos_texto}
                    
                    CATÁLOGO CENABAST:
                    {contexto[:25000]}
                    
                    TAREA:
                    1. Identifica qué marca comercial en CENABAST corresponde a nuestros quiebres.
                    2. Haz una tabla: Producto Local | Marca CENABAST | Estado de Entrega.
                    3. Destaca en ROJO o NEGRITA si el estado es 'SUSPENSION POR DEUDA'.
                    """
                    
                    response = model.generate_content(prompt)
                    st.subheader("📋 Informe Final de Gestión")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"Error en el cruce: {e}")

    if st.sidebar.button("🗑️ Reiniciar Radar"):
        st.session_state.criticos_texto = None
        st.rerun()
