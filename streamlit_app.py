import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN IA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- 2. CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 SSASUR (CSV)", type=["csv"])
with col2: f_icp = st.file_uploader("📦 CENABAST (Archivo: ICP-Intermediacion...)", type=["csv"])

if f_ssasur and f_icp:
    with st.spinner('🤖 Procesando cruce de datos con IA...'):
        try:
            # Leer SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # --- AJUSTE CLAVE PARA TU ARCHIVO ---
            # Saltamos 3 filas y usamos separador ; según tu archivo
            df_c = pd.read_csv(f_icp, sep=';', skiprows=3, encoding='latin1')
            
            # Limpiamos nombres de columnas (eliminamos espacios invisibles)
            df_c.columns = df_c.columns.str.strip()
            
            # Extraemos la información relevante para que la IA la procese
            # Usamos 'NOMBRE GENERICO', 'SEMAFORO' y 'ESTADO DEL MATERIAL'
            columnas_ia = ['NOMBRE GENERICO', 'SEMAFORO', 'ESTADO DEL MATERIAL']
            contexto_icp = df_c[columnas_ia].head(200).to_string(index=False)

            # Filtramos los críticos (< 0.5 meses)
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(15)
            
            if not criticos.empty:
                st.subheader("⚠️ Estado Real en CENABAST (Análisis Semántico)")
                
                def consultar_ia(farma):
                    prompt = f"""
                    Actúa como Químico Farmacéutico. Busca el fármaco '{farma}' en esta lista de CENABAST:
                    {contexto_icp}
                    
                    Dime qué dice en 'SEMAFORO' o 'ESTADO DEL MATERIAL'.
                    Responde SOLO con el estado (ej: ENTREGADO, APROBADO, PENDIENTE).
                    Si no existe en la lista, responde 'NO EN LISTA'.
                    """
                    try:
                        res = model.generate_content(prompt)
                        return res.text.strip().upper()
                    except:
                        return "REINTENTAR"

                # Aplicamos la inteligencia al listado
                criticos['Estado Real'] = criticos['Producto'].apply(consultar_ia)
                
                # Visualización con colores institucionales
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real']].style.applymap(
                    lambda x: 'background-color: #1b5e20; color: white' if x in ['ENTREGADO', 'APROBADO'] else 
                              ('background-color: #b71c1c; color: white' if x == 'NO EN LISTA' else ''),
                    subset=['Estado Real']
                ))
            else:
                st.success("✅ Todo el stock crítico está cubierto.")
                
        except Exception as e:
            st.error(f"Error de lectura: {e}")
