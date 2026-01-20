import streamlit as st
import pandas as pd
import google.generativeai as genai

# --- CONFIGURACIÓN IA ---
API_KEY = "AIzaSyBN6sd1xDS8fPfgEBGn9XNh_E-iSd7jAR8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Radar Saavedra AI", layout="wide")
st.title("🚀 Radar de Abastecimiento + IA")
st.markdown(f"**Hospital Puerto Saavedra** | Gestión: Renato Rozas")

# --- CARGA DE ARCHIVOS ---
col1, col2 = st.columns(2)
with col1: f_ssasur = st.file_uploader("📥 Subir SSASUR (CSV)", type=["csv"])
with col2: f_icp = st.file_uploader("📦 Subir CENABAST (Excel)", type=["xlsx", "xls"])

if f_ssasur and f_icp:
    with st.spinner('🤖 Sincronizando con base de datos CENABAST...'):
        try:
            # Procesar SSASUR 
            df_s = pd.read_csv(f_ssasur, sep=None, engine='python', encoding='latin1')
            df_s['Saldo Meses'] = pd.to_numeric(df_s['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
            
            # PROCESAMIENTO INTELIGENTE CENABAST
            # Leemos el Excel y buscamos la fila donde realmente empiezan los datos
            df_c_raw = pd.read_excel(f_icp)
            
            # Buscamos una palabra clave como "Descripción" o "Producto" para fijar el encabezado
            header_idx = 0
            for i, row in df_c_raw.head(15).iterrows():
                if any(k in str(row.values).upper() for k in ["DESCRIPCIÓN", "PRODUCTO", "NOMBRE"]):
                    header_idx = i + 1
                    break
            
            # Re-leemos el archivo desde la fila correcta
            df_c = pd.read_excel(f_icp, skiprows=header_idx).dropna(how='all').head(300)
            contexto_referencia = df_c.astype(str).to_string(index=False)

            # Filtramos los críticos para el Hospital 
            criticos = df_s[df_s['Saldo Meses'] < 0.5].copy().sort_values('Saldo Meses').head(12)
            
            if not criticos.empty:
                st.subheader("⚠️ Estado Real de Gestión (Cruce con CENABAST)")
                
                def consultar_estado_ia(nombre_f):
                    prompt = f"""
                    Actúa como Q.F. del Hospital Puerto Saavedra. 
                    Busca '{nombre_f}' en estos registros de CENABAST:
                    {contexto_referencia}
                    
                    Responde SOLO con una palabra del estado logístico:
                    'ENTREGADO', 'APROBADO', 'PENDIENTE' o 'NO ENCONTRADO'.
                    """
                    try:
                        res = model.generate_content(prompt)
                        return res.text.strip().upper()
                    except:
                        return "ERROR IA"

                criticos['Estado Real (Cenabast)'] = criticos['Producto'].apply(consultar_estado_ia)
                
                # Visualización con colores de alerta 
                st.dataframe(criticos[['Producto', 'Saldo Actual', 'Saldo Meses', 'Estado Real (Cenabast)']].style.applymap(
                    lambda x: 'background-color: #004d40; color: white' if x in ['ENTREGADO', 'APROBADO'] else 
                              ('background-color: #b71c1c; color: white' if x == 'NO ENCONTRADO' else ''),
                    subset=['Estado Real (Cenabast)']
                ))
            else:
                st.success("✅ No se detectan fármacos en nivel crítico.")
                
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}. Verifica que el Excel no esté protegido.")
