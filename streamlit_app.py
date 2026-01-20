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
with col2: f_icp = st.file_uploader("📦 Cargar CENABAST (CSV)", type=["csv"])

if f_ssasur and f_icp:
    with st.spinner('🤖 Gemini analizando datos...'):
        try:
            # --- LECTURA SSASUR ---
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # --- LECTURA CENABAST (POR POSICIÓN) ---
            # Saltamos las 3 filas de títulos
            df_c = pd.read_csv(f_icp, sep=';', skiprows=3, encoding='latin1')
            
            # Seleccionamos columnas por su número de índice:
            # Col 0: SEMAFORO | Col 10: NOMBRE GENERICO | Col 11: ESTADO DEL MATERIAL
            df_c_limpio = df_c.iloc[:, [0, 10, 11]].copy()
            df_c_limpio.columns = ['SEMAFORO', 'PRODUCTO_CEN', 'ESTADO_MAT']
            
            # Preparamos el contexto para Gemini
            contexto_ia = df_c_limpio.dropna(subset=['PRODUCTO_CEN']).head(150).to_string(index=False)

            # Filtramos críticos
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(12)
            
            if not criticos.empty:
                st.subheader("⚠️ Estado Real de Fármacos (Cruce con CENABAST)")
                
                def consultar_ia(farma_hosp):
                    prompt = f"""
                    Actúa como Q.F. del Hospital Puerto Saavedra. 
                    En base a esta lista de CENABAST:
                    {contexto_ia}
                    
                    Busca '{farma_hosp}'. 
                    Si lo encuentras, dime su estado (sale en las columnas SEMAFORO o ESTADO_MAT).
                    Responde SOLO con el estado. Si no está, di 'SIN INFORMACION'.
                    """
                    try:
                        res = model.generate_content(prompt)
                        return res.text.strip().upper()
                    except:
                        return "REINTENTAR"

                criticos['Estado Real'] = criticos['Producto'].apply(consultar_ia)
                
                # Tabla con formato visual
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real']].style.applymap(
                    lambda x: 'background-color: #1b5e20; color: white' if any(p in str(x) for p in ['ENTREGADO', 'APROBADO']) else 
                              ('background-color: #b71c1c; color: white' if 'SIN' in str(x) else ''),
                    subset=['Estado Real']
                ))
            else:
                st.success("✅ Stock saludable (> 0.5 meses).")
                
        except Exception as e:
            st.error(f"Error técnico: {e}")
