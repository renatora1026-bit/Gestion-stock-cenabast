import streamlit as st
import pandas as pd

# Configuración profesional
st.set_page_config(page_title="Gestión de Stock QF Saavedra", page_icon="📊", layout="wide")

# Logo e Identidad (Recuerda subir el logo a este nuevo repo también)
try:
    st.image("logo.png", width=120)
except:
    st.info("💡 Consejo: Sube el logo.png a este repositorio para personalizarlo.")

st.title("📊 Sistema de Inteligencia de Inventario")
st.subheader("Hospital de Puerto Saavedra - Área de Abastecimiento")

st.markdown("""
Esta herramienta está diseñada para procesar exportaciones de **SSASUR** y optimizar 
la programación de **CENABAST**, facilitando la toma de decisiones basada en datos reales.
""")

st.divider()

# Sección de Carga de Datos
st.header("1. Carga de Planillas SSASUR")
archivo_ssasur = st.file_uploader("Arrastra aquí tu reporte de consumo o stock (Excel/CSV)", type=["xlsx", "csv"])

if archivo_ssasur:
    try:
        # Lectura inteligente
        if archivo_ssasur.name.endswith('xlsx'):
            df = pd.read_excel(archivo_ssasur)
        else:
            df = pd.read_csv(archivo_ssasur)
            
        st.success(f"✅ Se han cargado {len(df)} registros exitosamente.")
        
        # Dashboard Inicial
        st.header("2. Vista Previa de Información")
        st.dataframe(df.head(20)) # Mostramos los primeros 20 para validar
        
        # Aquí es donde la IA empezará a trabajar
        st.info("🤖 **Próximo Paso**: Configurar el análisis de stock crítico y sugerencias de pedido para CENABAST.")

    except Exception as e:
        st.error(f"Hubo un error al procesar el archivo: {e}")

else:
    st.warning("Esperando archivo de SSASUR para iniciar el análisis...")
