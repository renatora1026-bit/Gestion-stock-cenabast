import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- 1. CONFIGURACIÓN IA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
# Usamos el modelo flash que ya confirmamos que conecta
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- 2. CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 SSASUR (CSV)", type=["csv"])
with col2: f_icp = st.file_uploader("📦 CENABAST (CSV o Excel)", type=["csv", "xlsx"])

# --- 3. PROCESAMIENTO ---
if f_ssasur and f_icp:
    with st.spinner('🤖 IA analizando concordancias semánticas...'):
        try:
            # Procesar SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # Cargamos más datos de CENABAST para que la IA tenga de dónde elegir
            if f_icp.name.endswith('csv'):
                df_c = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip').head(150)
            else:
                df_c = pd.read_excel(f_icp).head(150)
            
            # Convertimos la tabla de Cenabast en un texto fácil de leer para la IA
            contexto_icp = df_c.to_string(index=False)

            # Filtramos los críticos (< 0.5 meses)
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses')
            
            if not criticos.empty:
                st.subheader("⚠️ Análisis IA de Stock Crítico")
                
                # INSTRUCCIONES REFORZADAS PARA LA IA
                def razonamiento_farmaceutico(producto):
                    prompt = f"""
                    Eres un Químico Farmacéutico en Chile. Tu tarea es buscar este producto de SSASUR: '{producto}' 
                    en la siguiente lista de CENABAST:
                    
                    {contexto_icp}
                    
                    INSTRUCCIONES:
                    1. Sé flexible. 'PNC' es Penicilina, 'SF' es Suero Fisiológico, etc.
                    2. Si encuentras el producto, responde SOLO con su ESTADO (ej: ENTREGADO, APROBADO, PROGRAMADO).
                    3. Si después de analizarlo bien NO está, responde 'NO EN LISTA'.
                    4. Responde con UNA SOLA PALABRA.
                    """
                    try:
                        response = model.generate_content(prompt)
                        return response.text.strip().upper()
                    except:
                        return "ERROR IA"

                # Analizamos los primeros 10 más críticos para asegurar velocidad
                resumen_ia = criticos.head(10).copy()
                resumen_ia['Estado Real (Cenabast)'] = resumen_ia['Producto'].apply(razonamiento_farmaceutico)
                
                # Mostrar resultados con estilo
                st.dataframe(resumen_ia[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real (Cenabast)']].style.applymap(
                    lambda x: 'background-color: #2e7d32; color: white' if x in ['ENTREGADO', 'APROBADO'] else ('background-color: #c62828; color: white' if x == 'NO EN LISTA' else ''),
                    subset=['Estado Real (Cenabast)']
                ))
            else:
                st.success("✅ No se detectan quiebres inminentes.")
                
        except Exception as e:
            st.error(f"Error en el cruce: {e}")
