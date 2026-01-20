import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN IA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")

# --- 2. CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 SSASUR (CSV)", type=["csv"])
with col2: f_icp = st.file_uploader("📦 CENABAST (CSV)", type=["csv"])

if f_ssasur and f_icp:
    with st.spinner('🤖 Sincronizando datos...'):
        try:
            # Leer SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # --- LECTURA CIEGA DE CENABAST ---
            # Leemos el archivo saltando las 3 filas de títulos
            df_c = pd.read_csv(f_icp, sep=';', skiprows=3, encoding='latin1', header=0)
            
            # SELECCIÓN POR POSICIÓN (No por nombre para evitar el KeyError)
            # Col 0 = SEMAFORO | Col 10 = NOMBRE GENERICO | Col 11 = ESTADO DEL MATERIAL
            df_c_datos = df_c.iloc[:, [0, 10, 11]].copy()
            df_c_datos.columns = ['SEM', 'NOM', 'EST'] # Renombramos nosotros
            
            # Preparamos el contexto para Gemini
            contexto_ia = df_c_datos.dropna().head(200).to_string(index=False)

            # Filtramos críticos (< 0.5 meses)
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(12)
            
            if not criticos.empty:
                st.subheader("⚠️ Análisis de Disponibilidad Real")
                
                def consultar_ia(farma):
                    prompt = f"""
                    Busca el fármaco '{farma}' en esta lista de CENABAST:
                    {contexto_ia}
                    Dime su estado (lo que sale en las columnas SEM o EST). 
                    Responde SOLO con el estado. Si no está, responde 'SIN INFO'.
                    """
                    try:
                        res = model.generate_content(prompt)
                        return res.text.strip().upper()
                    except:
                        return "ERROR"

                criticos['Estado Real'] = criticos['Producto'].apply(consultar_ia)
                
                # Visualización
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real']].style.applymap(
                    lambda x: 'background-color: #1b5e20; color: white' if any(p in str(x) for p in ['ENTREGADO', 'APROBADO']) else 
                              ('background-color: #b71c1c; color: white' if 'SIN' in str(x) else ''),
                    subset=['Estado Real']
                ))
            else:
                st.success("✅ Stock saludable.")
                
        except Exception as e:
            st.error(f"Error detectado: {e}")
            # Si vuelve a fallar, mostramos qué columnas ve el programa para arreglarlo
            st.write("Columnas detectadas en el archivo:", list(df_c.columns))
