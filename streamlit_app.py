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
with col1: f_ssasur = st.file_uploader("📥 SSASUR (CSV)", type=["csv"])
with col2: f_icp = st.file_uploader("📦 CENABAST (ICP-Intermediacion)", type=["csv"])

if f_ssasur and f_icp:
    with st.spinner('🤖 Sincronizando datos con IA...'):
        try:
            # --- LECTURA SSASUR ---
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # --- LECTURA CENABAST BLINDADA ---
            # Leemos el archivo completo como texto para limpiar caracteres ocultos
            bytes_data = f_icp.getvalue()
            try:
                text_data = bytes_data.decode('latin1')
            except:
                text_data = bytes_data.decode('utf-16')
            
            # Convertimos a DataFrame saltando las 3 filas de título
            df_c = pd.read_csv(io.StringIO(text_data), sep=';', skiprows=3)
            
            # Limpieza profunda de nombres de columnas
            df_c.columns = [str(c).strip().upper() for c in df_c.columns]
            
            # Preparamos contexto para la IA
            # Usamos 'NOMBRE GENERICO', 'SEMAFORO' y 'ESTADO DEL MATERIAL'
            info_icp = df_c[['NOMBRE GENERICO', 'SEMAFORO', 'ESTADO DEL MATERIAL']].dropna().head(200)
            contexto_txt = info_icp.to_string(index=False)

            # Filtramos críticos (< 0.5 meses)
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(12)
            
            if not criticos.empty:
                st.subheader("⚠️ Análisis de Disponibilidad Real")
                
                def consultar_ia(farma):
                    prompt = f"""
                    Busca '{farma}' en esta lista de CENABAST:
                    {contexto_txt}
                    
                    Responde SOLO con el estado (ej: ENTREGADO, APROBADO, PENDIENTE).
                    Si no está, responde 'SIN REGISTRO'.
                    """
                    try:
                        res = model.generate_content(prompt)
                        return res.text.strip().upper()
                    except:
                        return "ERROR"

                criticos['Estado Real'] = criticos['Producto'].apply(consultar_ia)
                
                # Visualización final con colores
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real']].style.applymap(
                    lambda x: 'background-color: #1b5e20; color: white' if x in ['ENTREGADO', 'APROBADO'] else 
                              ('background-color: #b71c1c; color: white' if x == 'SIN REGISTRO' else ''),
                    subset=['Estado Real']
                ))
            else:
                st.success("✅ Stock saludable.")
                
        except Exception as e:
            st.error(f"Error de lectura: {e}")
