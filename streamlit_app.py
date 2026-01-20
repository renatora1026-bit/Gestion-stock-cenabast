import streamlit as st
import pandas as pd
import google.generativeai as genai
import io

# --- 1. CONFIGURACIÓN IA (Gemini sigue al mando) ---
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
    with st.spinner('🤖 Gemini analizando el cumplimiento de CENABAST...'):
        try:
            # --- LECTURA SSASUR ---
            # Usamos encoding latin1 por si vienen acentos en los nombres de fármacos
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # --- LECTURA CENABAST (Ajustada a tu archivo real) ---
            # Forzamos latin1, separador ; y saltamos 3 filas de títulos
            df_c = pd.read_csv(f_icp, sep=';', skiprows=3, encoding='latin1')
            
            # Limpiamos nombres de columnas de espacios invisibles
            df_c.columns = [c.strip() for c in df_c.columns]
            
            # Preparamos el resumen que leerá la IA
            # Usamos 'NOMBRE GENERICO', 'SEMAFORO' y 'ESTADO DEL MATERIAL'
            columnas_necesarias = ['NOMBRE GENERICO', 'SEMAFORO', 'ESTADO DEL MATERIAL']
            resumen_cenabast = df_c[columnas_necesarias].dropna(how='all').head(200).to_string(index=False)

            # Filtramos los fármacos con stock más crítico (< 0.5 meses)
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(12)
            
            if not criticos.empty:
                st.subheader("⚠️ Estado Real de Fármacos Críticos (Cruce IA)")
                
                def consultar_ia(farma_hospital):
                    # Aquí Gemini hace la magia de comparar nombres técnicos
                    prompt = f"""
                    Actúa como experto en farmacia clínica. En base a esta lista de CENABAST:
                    {resumen_cenabast}
                    
                    ¿Cuál es el estado de gestión de '{farma_hospital}'? 
                    Busca por coincidencia de nombre (ej: A.A SALICILIC es ASPIRINA).
                    Responde SOLO con lo que dice en 'SEMAFORO' o 'ESTADO DEL MATERIAL'.
                    Si no está, responde 'SIN REGISTRO'. Solo una palabra o frase corta.
                    """
                    try:
                        response = model.generate_content(prompt)
                        return response.text.strip().upper()
                    except:
                        return "ERROR IA"

                # Ejecutar la consulta para cada crítico
                criticos['Estado en CENABAST'] = criticos['Producto'].apply(consultar_ia)
                
                # Visualización con colores de gestión
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado en CENABAST']].style.applymap(
                    lambda x: 'background-color: #1b5e20; color: white' if any(palabra in str(x) for palabra in ['ENTREGADO', 'APROBADO', 'PROGRAMADO']) else 
                              ('background-color: #b71c1c; color: white' if 'SIN' in str(x) else ''),
                    subset=['Estado en CENABAST']
                ))
            else:
                st.success("✅ No hay fármacos bajo el nivel crítico de 0.5 meses.")
                
        except Exception as e:
            st.error(f"Error técnico: {e}. Asegúrate de subir el archivo CSV original de Cenabast.")
