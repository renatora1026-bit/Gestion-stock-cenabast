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
with col2: f_icp = st.file_uploader("📦 CENABAST (CSV o Excel)", type=["csv", "xlsx"])

# --- 3. PROCESAMIENTO ---
if f_ssasur and f_icp:
    with st.spinner('🤖 Analizando stock crítico...'):
        try:
            # Procesar SSASUR
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # Cargar CENABAST de forma ultra-ligera (solo lo esencial)
            if f_icp.name.endswith('csv'):
                df_c = pd.read_csv(f_icp, sep=None, engine='python', encoding='utf-8', on_bad_lines='skip').head(100)
            else:
                df_c = pd.read_excel(f_icp).head(100)
            
            # Limpiamos los datos para la IA
            lista_cenabast = df_c.astype(str).apply(lambda x: ' '.join(x), axis=1).tolist()
            contexto_ia = "\n".join(lista_cenabast)

            # Filtramos solo los críticos (< 0.5)
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(10)
            
            if not criticos.empty:
                st.subheader("⚠️ Estado Real de Fármacos Críticos")
                
                def buscar_en_ia(prod):
                    prompt = f"Busca '{prod}' en esta lista y dime su estado (EJ: ENTREGADO, PENDIENTE). Si no está, di 'NO ENCONTRADO'.\n\nLISTA:\n{contexto_ia}"
                    try:
                        res = model.generate_content(prompt)
                        return res.text.strip().upper()
                    except:
                        return "REINTENTAR"

                # Ejecutamos la búsqueda fármaco por fármaco
                criticos['Estado Real (Cenabast)'] = criticos['Producto'].apply(buscar_en_ia)
                
                # Visualización final
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real (Cenabast)']].style.applymap(
                    lambda x: 'background-color: #004d40; color: white' if x in ['ENTREGADO', 'APROBADO', 'DESPACHADO'] else '',
                    subset=['Estado Real (Cenabast)']
                ))
            else:
                st.success("✅ Todo el stock parece estar en orden.")
                
        except Exception as e:
            st.error(f"Error técnico: {e}")
