import streamlit as st
import pandas as pd

st.set_page_config(page_title="Radar Saavedra Pro", layout="wide")
st.title("🚀 Radar de Abastecimiento Inteligente")
st.write("Hospital de Puerto Saavedra - Gestión Renato Rozas")

# 1. CARGA MULTI-ARCHIVO
archivos = st.file_uploader("Sube tus archivos (SSASUR, Arsenal, ICP)", type=["csv", "xlsx", "xlsm"], accept_multiple_files=True)

if archivos:
    data = {}
    for f in archivos:
        try:
            if "resumenConsumo" in f.name:
                df = pd.read_csv(f, sep=";", encoding='latin1')
                df['Saldo Meses'] = pd.to_numeric(df['Saldo Meses'].astype(str).str.replace(',', '.'), errors='coerce')
                data['ssasur'] = df.dropna(subset=['Saldo Meses'])
            elif "ARSENALES" in f.name:
                data['arsenal'] = pd.read_excel(f, engine='openpyxl')
            elif "ICP" in f.name:
                df_icp = pd.read_csv(f, sep=";", encoding='latin1')
                data['icp'] = pd.concat([data.get('icp', pd.DataFrame()), df_icp])
            st.success(f"✅ Cargado: {f.name}")
        except Exception as e:
            st.error(f"Error en {f.name}: {e}")

    # 2. PROCESAMIENTO E INTELIGENCIA
    if 'ssasur' in data:
        ssasur = data['ssasur']
        
        # Etiquetar Arsenal
        lista_arsenal = data['arsenal']['Descrip. Artículo'].unique() if 'arsenal' in data else []
        ssasur['Tipo'] = ssasur['Producto'].apply(lambda x: "✅ ARSENAL" if any(p in x for p in lista_arsenal) else "⚠️ EXTRA")
        
        # Cruzar con ICP (Próximas entregas)
        lista_icp = data['icp']['Producto'].unique() if 'icp' in data else []
        ssasur['En Camino'] = ssasur['Producto'].apply(lambda x: "🚚 SÍ" if any(p in x for p in lista_icp) else "❌ NO")

        # 3. FILTROS EN LA BARRA LATERAL
        st.sidebar.header("Filtros de Control")
        solo_arsenal = st.sidebar.checkbox("Ver solo productos de MI ARSENAL", value=False)
        solo_criticos = st.sidebar.checkbox("Ver solo CRÍTICOS (Rojo)", value=True)

        df_final = ssasur.copy()
        if solo_arsenal: df_final = df_final[df_final['Tipo'] == "✅ ARSENAL"]
        if solo_criticos: df_final = df_final[df_final['Saldo Meses'] < 0.5]

        # 4. VISUALIZACIÓN
        def color_final(row):
            if row['Saldo Meses'] < 0.5 and row['En Camino'] == "❌ NO":
                return ['background-color: #ff4b4b; color: white'] * len(row)
            elif row['Saldo Meses'] < 0.5 and row['En Camino'] == "🚚 SÍ":
                return ['background-color: #ffa500; color: black'] * len(row)
            return [''] * len(row)

        st.subheader("📋 Plan de Acción Logístico")
        st.dataframe(df_final[['Producto', 'Saldo Actual', 'Saldo Meses', 'Tipo', 'En Camino']].style.apply(color_final, axis=1))

else:
    st.info("👋 Hola Renato. Sube el Arsenal y el SSASUR para filtrar los fármacos ocasionales.")
