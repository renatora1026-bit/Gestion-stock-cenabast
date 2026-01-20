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
with col2: f_icp = st.file_uploader("📦 Cargar CENABAST (Archivo del ICP)", type=["csv"])

if f_ssasur and f_icp:
    with st.spinner('🤖 Gemini analizando datos por posición...'):
        try:
            # --- LECTURA SSASUR ---
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # --- LECTURA CENABAST (POR POSICIÓN DE COLUMNA) ---
            # Saltamos las 3 filas de títulos institucionales
            df_c = pd.read_csv(f_icp, sep=';', skiprows=3, encoding='latin1')
            
            # Usamos índices numéricos porque los nombres fallan por caracteres ocultos:
            # Columna 0: SEMAFORO | Columna 10: NOMBRE GENERICO | Columna 11: ESTADO DEL MATERIAL
            df_c_limpio = df_c.iloc[:, [0, 10, 11]].copy()
            df_c_limpio.columns = ['ESTADO_SEM', 'PRODUCTO_CEN', 'ESTADO_MAT']
            
            # Preparamos el contexto para Gemini (limpio de valores nulos)
            contexto_ia = df_c_limpio.dropna(subset=['PRODUCTO_CEN']).head(200).to_string(index=False)

            # Filtramos los fármacos críticos del Hospital
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(12)
            
            if not criticos.empty:
                st.subheader("⚠️ Análisis de Disponibilidad (Cruce IA)")
                
                def consultar_ia(farma_hosp):
                    prompt = f"""
                    Actúa como Q.F. del Hospital Puerto Saavedra. 
                    En base a esta lista de CENABAST:
                    {contexto_ia}
                    
                    Busca el fármaco '{farma_hosp}'. 
                    Si lo encuentras, dime su estado (revisa las columnas ESTADO_SEM o ESTADO_MAT).
                    Responde SOLO con el estado. Si no está, responde 'SIN INFORMACION'.
                    """
                    try:
                        res = model.generate_content(prompt)
                        return res.text.strip().upper()
                    except:
                        return "ERROR CONEXION"

                criticos['Estado Real'] = criticos['Producto'].apply(consultar_ia)
                
                # Visualización con colores de gestión
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real']].style.applymap(
                    lambda x: 'background-color: #1b5e20; color: white' if any(p in str(x) for p in ['ENTREGADO', 'APROBADO', 'PROGRAMADO']) else 
                              ('background-color: #b71c1c; color: white' if 'SIN' in str(x) else ''),
                    subset=['Estado Real']
                ))
            else:
                st.success("✅ No hay fármacos críticos bajo el umbral de 0.5 meses.")
                
        except Exception as e:
            st.error(f"Error técnico: {e}")
            st.info("Sugerencia: Sube el archivo CSV de CENABAST tal cual lo descargas.")
