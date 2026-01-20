import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

# --- 1. CONFIGURACIÓN IA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- 2. CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 Cargar SSASUR (CSV)", type=["csv"])
with col2: f_icp = st.file_uploader("📦 Cargar Archivo CENABAST (CSV)", type=["csv"])

if f_ssasur and f_icp:
    with st.spinner('🤖 Sincronizando datos con Gemini...'):
        try:
            # --- LECTURA SSASUR ---
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # --- LECTURA CENABAST (A PRUEBA DE TODO) ---
            # Leemos el archivo saltando 3 filas y forzando el separador ;
            df_c = pd.read_csv(f_icp, sep=';', skiprows=3, encoding='latin1')
            
            # Limpiamos los nombres de las columnas quitando tildes y espacios
            df_c.columns = df_c.columns.str.strip().str.replace('É', 'E').str.replace('Ó', 'O')
            
            # Seleccionamos las columnas clave (usando los nombres que vimos en tu archivo)
            # NOMBRE GENERICO, SEMAFORO, ESTADO DEL MATERIAL
            df_c_limpio = df_c[['NOMBRE GENERICO', 'SEMAFORO', 'ESTADO DEL MATERIAL']].dropna(subset=['NOMBRE GENERICO'])
            
            # Preparamos el texto para que la IA lo entienda
            contexto_ia = df_c_limpio.head(150).to_string(index=False)

            # Filtramos los fármacos críticos
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(12)
            
            if not criticos.empty:
                st.subheader("⚠️ Estado Real en CENABAST (Cruce IA)")
                
                def consultar_ia(farma):
                    prompt = f"""
                    Actúa como Q.F. En base a esta lista de CENABAST:
                    {contexto_ia}
                    
                    ¿Cuál es el estado de '{farma}'? 
                    Dime lo que sale en SEMAFORO o ESTADO DEL MATERIAL.
                    Si no está, responde 'SIN REGISTRO'. Solo una palabra.
                    """
                    try:
                        res = model.generate_content(prompt)
                        return res.text.strip().upper()
                    except:
                        return "REINTENTAR"

                criticos['Estado Real'] = criticos['Producto'].apply(consultar_ia)
                
                # Visualización con colores
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real']].style.applymap(
                    lambda x: 'background-color: #1b5e20; color: white' if any(p in str(x) for p in ['ENTREGADO', 'APROBADO']) else 
                              ('background-color: #b71c1c; color: white' if 'SIN' in str(x) else ''),
                    subset=['Estado Real']
                ))
            else:
                st.success("✅ Stock saludable.")
                
        except Exception as e:
            st.error(f"Error detectado: {e}")
            st.info("Asegúrate de que el archivo de Cenabast sea el mismo que me enviaste (separado por punto y coma).")
