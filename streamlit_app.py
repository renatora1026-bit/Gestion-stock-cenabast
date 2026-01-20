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
with col2: f_icp = st.file_uploader("📦 CENABAST (CSV del ICP)", type=["csv"])

if f_ssasur and f_icp:
    with st.spinner('🤖 Procesando cruce de datos...'):
        try:
            # Leer SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # Leer CENABAST (Ajustado a tu archivo: fila 4 y separador ;)
            df_c = pd.read_csv(f_icp, sep=';', skiprows=3, encoding='latin1')
            
            # Limpiamos nombres de columnas por si acaso
            df_c.columns = df_c.columns.str.strip()
            
            # Tomamos una muestra de los estados para la IA
            contexto_icp = df_c[['NOMBRE GENERICO', 'SEMAFORO', 'ESTADO DEL MATERIAL']].head(150).to_string(index=False)

            # Filtramos críticos (< 0.5 meses)
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(12)
            
            if not criticos.empty:
                st.subheader("⚠️ Estado Real en CENABAST (IA)")
                
                def consultar_ia(farma):
                    prompt = f"""
                    Busca el fármaco '{farma}' en esta lista de CENABAST:
                    {contexto_icp}
                    
                    Dime el estado que aparece en 'SEMAFORO' o 'ESTADO DEL MATERIAL'.
                    Si no está, responde 'NO EN LISTA'. Solo una palabra.
                    """
                    try:
                        res = model.generate_content(prompt)
                        return res.text.strip().upper()
                    except:
                        return "REINTENTAR"

                criticos['Estado Real'] = criticos['Producto'].apply(consultar_ia)
                
                # Tabla con colores
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real']].style.applymap(
                    lambda x: 'background-color: #1b5e20; color: white' if x in ['ENTREGADO', 'APROBADO'] else 
                              ('background-color: #b71c1c; color: white' if x == 'NO EN LISTA' else ''),
                    subset=['Estado Real']
                ))
            else:
                st.success("✅ Stock saludable.")
                
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
