import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from groq import Groq

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="EDA Pro + IA", layout="wide")

st.title("📊 EDA Pro: Analizador con Llama 3.3")
st.markdown("""
Esta herramienta analiza cualquier dataset y cuenta con un **Asistente de IA (Groq)** para interpretar los resultados.
""")

# --- SIDEBAR: IA Y CARGA ---
st.sidebar.header("1. Configuración de IA")
groq_api_key = st.sidebar.text_input("Introduce tu Groq API Key:", type="password")

st.sidebar.header("2. Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Sube tu archivo CSV o Excel", type=["csv", "xlsx", "xls"])

# --- FUNCIÓN DE CARGA ---
@st.cache_data
def load_data(file):
    try:
        filename = file.name
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(file)
        else:
            return None, "Formato no soportado."
        return df, None
    except Exception as e:
        return None, str(e)

# --- FLUJO PRINCIPAL ---
if uploaded_file is not None:
    df, error = load_data(uploaded_file)
    
    if error:
        st.error(f"Error al cargar el archivo: {error}")
        st.stop()
        
    st.sidebar.success("✅ Datos cargados correctamente")
    
    # Identificar tipos de columnas
    all_columns = df.columns.tolist()
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

    # --- FILTRO DINÁMICO ---
    st.sidebar.header("3. Filtros Globales")
    filter_col = st.sidebar.selectbox("Filtrar por columna:", ["Ninguno"] + categorical_columns)
    if filter_col != "Ninguno":
        filter_val = st.sidebar.multiselect(f"Valores de '{filter_col}':", options=df[filter_col].unique(), default=df[filter_col].unique())
        if filter_val:
            df = df[df[filter_col].isin(filter_val)]

    # --- PESTAÑAS (DEFINICIÓN ÚNICA) ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Resumen", "📊 Univariable", "📈 Relaciones", "🔥 Correlaciones", "🤖 Asistente IA"
    ])

    # --- TAB 1: RESUMEN ---
    with tab1:
        st.subheader("Vista Previa y Estadísticas")
        st.dataframe(df.head())
        c1, c2, c3 = st.columns(3)
        c1.metric("Filas", df.shape[0])
        c2.metric("Columnas", df.shape[1])
        c3.metric("Nulos", df.isnull().sum().sum())
        st.write("Estadísticas Descriptivas:", df.describe())

    # --- TAB 2: UNIVARIABLE ---
    with tab2:
        col_to_plot = st.selectbox("Selecciona columna:", all_columns)
        if col_to_plot in numeric_columns:
            fig = px.histogram(df, x=col_to_plot, marginal="box", title=f"Distribución de {col_to_plot}")
        else:
            conteo_df = df[col_to_plot].value_counts().reset_index()
            conteo_df.columns = [col_to_plot, 'Conteo']
            fig = px.bar(conteo_df, x=col_to_plot, y='Conteo', title=f"Frecuencia de {col_to_plot}")
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 3: RELACIONES ---
    with tab3:
        x_ax = st.selectbox("Eje X:", all_columns, index=0)
        y_ax = st.selectbox("Eje Y:", all_columns, index=1 if len(all_columns)>1 else 0)
        if x_ax in numeric_columns and y_ax in numeric_columns:
            fig = px.scatter(df, x=x_ax, y=y_ax, title=f"{x_ax} vs {y_ax}")
        else:
            fig = px.box(df, x=x_ax, y=y_ax, title=f"Distribución de {y_ax} por {x_ax}")
        st.plotly_chart(fig, use_container_width=True)

    # --- TAB 4: CORRELACIONES ---
    with tab4:
        if len(numeric_columns) > 1:
            fig_corr = px.imshow(df[numeric_columns].corr(), text_auto=True, title="Matriz de Correlación")
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("No hay suficientes columnas numéricas.")

    # --- TAB 5: ASISTENTE IA (CORREGIDO E INDENTADO) ---
    with tab5:
        st.subheader("Consultar con Llama 3.3 Versatile")
        if not groq_api_key:
            st.warning("Introduce tu API Key en la barra lateral.")
        else:
            pregunta = st.text_area("¿Qué deseas saber sobre estos datos?")
            if st.button("Analizar con IA"):
                try:
                    client = Groq(api_key=groq_api_key)
                    # Enviamos solo un fragmento y el resumen para no exceder límites de tokens
                    resumen_contexto = df.describe(include='all').to_string()
                    
                    prompt = f"Dataset Columns: {all_columns}\nStats Summary:\n{resumen_contexto}\n\nPregunta: {pregunta}"
                    
                    with st.spinner("Analizando..."):
                        chat_completion = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "Eres un experto analista de datos. Responde en español de forma concisa."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        st.markdown("### 📝 Análisis:")
                        st.write(chat_completion.choices[0].message.content)
                except Exception as e:
                    st.error(f"Error de IA: {e}")

else:
    st.info("Por favor, sube un archivo para comenzar.")
