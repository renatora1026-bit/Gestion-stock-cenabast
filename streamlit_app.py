# --- REEMPLAZA TU BLOQUE DE CENABAST CON ESTE ---
if f_icp:
    try:
        f_icp.seek(0)
        # Si es el archivo CSV que acabas de guardar
        if f_icp.name.endswith('.csv'):
            try:
                # Intenta con punto y coma (típico de Excel en Chile)
                data_icp = pd.read_csv(f_icp, sep=";", encoding='utf-8')
            except:
                f_icp.seek(0)
                # Si falla, intenta con coma
                data_icp = pd.read_csv(f_icp, sep=",", encoding='utf-8')
            st.success("✅ ICP sincronizado desde CSV")
        else:
            # Si intentas el original, usamos la lectura web
            data_icp = pd.read_html(f_icp)[0]
            st.success("✅ ICP sincronizado (Modo Portal)")
            
    except Exception as e:
        st.warning("⚠️ Casi lo tenemos. Sube el archivo que guardaste como '.csv' en tu Mac.")
