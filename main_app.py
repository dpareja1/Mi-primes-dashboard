import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
from groq import Groq  # Importamos Groq

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Analizador de Datos Genérico", layout="wide")

st.title("📊 EDA Pro: Analizador Exploratorio de Datos")
st.markdown("""
Esta herramienta acepta **cualquier conjunto de datos** y genera un reporte automático.
Sube tu archivo CSV o Excel para comenzar.
""")

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

# --- SIDEBAR: CARGA Y FILTROS GLOBALES ---
st.sidebar.header("1. Carga de Datos")
uploaded_file = st.sidebar.file_uploader("Sube tu archivo", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    # Cargar datos
    df, error = load_data(uploaded_file)
    
    if error:
        st.error(f"Error al cargar el archivo: {error}")
        st.stop()
        
    st.sidebar.success("✅ Datos cargados correctamente")
    
    # Identificar tipos de columnas
    all_columns = df.columns.tolist()
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()

    # --- FILTRO DINÁMICO GENÉRICO ---
    st.sidebar.header("2. Filtros Globales")
    # Permitimos al usuario elegir una columna para filtrar (opcional)
    filter_col = st.sidebar.selectbox("Filtrar por columna (Opcional):", ["Ninguno"] + categorical_columns)
    
    if filter_col != "Ninguno":
        filter_val = st.sidebar.multiselect(
            f"Valores de '{filter_col}':", 
            options=df[filter_col].unique(),
            default=df[filter_col].unique()
        )
        if filter_val:
            df = df[df[filter_col].isin(filter_val)]

    # --- PESTAÑAS DEL DASHBOARD ---
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Resumen de Datos", "📊 Análisis Univariable", "📈 Relaciones (Bivariable)", "🔥 Correlaciones"])

    # --- TAB 1: RESUMEN DE DATOS ---
    with tab1:
        st.subheader("Vista Previa del Dataset")
        st.dataframe(df.head())
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Filas", df.shape[0])
        col2.metric("Columnas", df.shape[1])
        col3.metric("Valores Nulos Totales", df.isnull().sum().sum())
        
        with st.expander("Ver tipos de datos y nulos por columna"):
            info_df = pd.DataFrame({
                'Tipo de Dato': df.dtypes,
                'Nulos': df.isnull().sum(),
                '% Nulos': (df.isnull().sum() / len(df)) * 100
            })
            st.dataframe(info_df)
            
        with st.expander("Estadísticas Descriptivas"):
            st.dataframe(df.describe())

    # --- TAB 2: ANÁLISIS UNIVARIABLE (CORREGIDO) ---
    with tab2:
        st.subheader("Explorar una sola variable")
        column_to_plot = st.selectbox("Selecciona una columna:", all_columns, key="univ_col")
    
        col_graph, col_stats = st.columns([3, 1])
    
    with col_graph:
        if column_to_plot in numeric_columns:
            st.write(f"Distribución de **{column_to_plot}** (Numérica)")
            fig = px.histogram(df, x=column_to_plot, marginal="box", title=f"Histograma de {column_to_plot}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write(f"Conteo de **{column_to_plot}** (Categórica)")
            
            # --- SOLUCIÓN AL ERROR ---
            # Preparamos los datos de conteo de forma segura
            conteo_df = df[column_to_plot].value_counts().reset_index()
            # Renombramos explícitamente para evitar conflictos con 'index'
            conteo_df.columns = [column_to_plot, 'Conteo'] 
            
            fig = px.bar(
                conteo_df, 
                x=column_to_plot, # La categoría
                y='Conteo',       # El valor contado
                title=f"Frecuencia de {column_to_plot}",
                labels={column_to_plot: 'Categoría', 'Conteo': 'Cantidad de Registros'},
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)
            # ---------------------------
                
    with col_stats:
        st.write("Estadísticas rápidas:")
        if column_to_plot in numeric_columns:
            st.write(df[column_to_plot].describe())
        else:
            st.write(df[column_to_plot].value_counts())

    # --- TAB 3: RELACIONES (BIVARIABLE) ---
    with tab3:
        st.subheader("Comparar dos variables")
        c1, c2, c3 = st.columns(3)
        x_axis = c1.selectbox("Eje X:", all_columns, index=0)
        y_axis = c2.selectbox("Eje Y:", all_columns, index=1 if len(all_columns) > 1 else 0)
        color_col = c3.selectbox("Color (Agrupación):", ["Ninguno"] + categorical_columns)
        
        color_arg = None if color_col == "Ninguno" else color_col
        
        st.markdown("---")
        
        # Lógica automática de gráficos según tipos de datos
        if x_axis in numeric_columns and y_axis in numeric_columns:
            st.caption("Gráfico de Dispersión (Numérico vs Numérico)")
            fig = px.scatter(df, x=x_axis, y=y_axis, color=color_arg, title=f"{x_axis} vs {y_axis}")
            st.plotly_chart(fig, use_container_width=True)
            
        elif (x_axis in categorical_columns and y_axis in numeric_columns) or (x_axis in numeric_columns and y_axis in categorical_columns):
            st.caption("Gráfico de Caja (Categórico vs Numérico)")
            # Asegurar que la categoría quede en el eje correcto para boxplot visualmente
            if x_axis in categorical_columns:
                fig = px.box(df, x=x_axis, y=y_axis, color=color_arg, title=f"Distribución de {y_axis} por {x_axis}")
            else:
                fig = px.box(df, x=y_axis, y=x_axis, color=color_arg, orient='h', title=f"Distribución de {x_axis} por {y_axis}")
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.warning("Selecciona al menos una variable numérica para gráficos XY estándar, o usa el análisis univariable.")

    # --- TAB 4: CORRELACIONES ---
    with tab4:
        st.subheader("Mapa de Calor de Correlaciones")
        if len(numeric_columns) > 1:
            corr_matrix = df[numeric_columns].corr()
            
            # Usamos Plotly para heatmap interactivo
            fig_corr = px.imshow(corr_matrix, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r', title="Matriz de Correlación")
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.info("Se necesitan al menos 2 columnas numéricas para calcular correlaciones.")

else:
    # Pantalla de bienvenida
    st.info("Esperando archivo... Por favor sube un CSV o Excel en la barra lateral.")
    st.markdown("### ¿Qué hace esta app?")
    st.markdown("""
    1.  **Detección automática**: Identifica columnas numéricas y de texto.
    2.  **Calidad de datos**: Muestra nulos y tipos de datos.
    3.  **Gráficos dinámicos**: Tú eliges qué variables cruzar (X vs Y).
    4.  **Soporte de archivos**: Acepta CSV y Excel.
    """)
    # --- TAB 5: ASISTENTE DE ANÁLISIS IA ---
    with tab5:
        st.subheader("Análisis Inteligente con Llama 3.3 Versatile")
        
        if not groq_api_key:
            st.warning("⚠️ Por favor, introduce tu API Key de Groq en la barra lateral para activar el asistente.")
        else:
            st.markdown("Pregunta lo que quieras sobre tus datos o solicita un análisis general.")
            
            user_question = st.text_area("Ejemplo: '¿Qué tendencias observas en la capacidad instalada?' o 'Resume este dataset'.")
            
            if st.button("Generar Análisis"):
                if user_question:
                    try:
                        # Inicializar cliente de Groq
                        client = Groq(api_key=groq_api_key)
                        
                        # Preparamos un resumen estadístico para enviarlo como contexto
                        # Solo enviamos el describe() y info para no saturar los tokens
                        contexto_datos = df.describe(include='all').to_string()
                        columnas_info = ", ".join(all_columns)
                        
                        prompt = f"""
                        Actúa como un experto científico de datos. Analiza el siguiente resumen estadístico de un dataset
                        y responde a la pregunta del usuario.
                        
                        Nombres de columnas: {columnas_info}
                        
                        Resumen estadístico:
                        {contexto_datos}
                        
                        Pregunta del usuario: {user_question}
                        
                        Proporciona una respuesta detallada, profesional y en español.
                        """
                        
                        with st.spinner("Llama está pensando..."):
                            completion = client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=[
                                    {"role": "system", "content": "Eres un asistente experto en análisis de datos."},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0.7,
                                max_tokens=2048
                            )
                            
                            st.markdown("### 📝 Respuesta del Asistente:")
                            st.write(completion.choices[0].message.content)
                            
                    except Exception as e:
                        st.error(f"Ocurrió un error con la IA: {e}")
                else:
                    st.info("Escribe una pregunta para comenzar.")

            else:
                st.info("Esperando archivo... Por favor sube un CSV o Excel en la barra lateral.")
