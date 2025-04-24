import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Dashboard de Delitos", page_icon="🚨", layout="wide")

# Título del dashboard
st.title('Dashboard de Delitos en Buenos Aires 🚨')
st.markdown("Análisis de datos de delitos entre 2016-2023")

# Leer CSV con manejo mejorado de comunas
@st.cache_data
def cargar_datos():
    import pandas as pd
    import re
    import unicodedata
    
    df = pd.read_csv("datasets_delitos_2019_2023_limpio.csv")
    df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce')
    
    # Guardar el valor original de comuna sin modificaciones
    df['comuna_original'] = df['comuna']
    df['comuna_display'] = df['comuna_original']
    
    # Mapeo oficial de barrios a comunas en Buenos Aires
    mapeo_oficial_barrios = {
        'AGRONOMIA': 15, 'ALMAGRO': 5, 'BALVANERA': 3, 'BARRACAS': 4, 
        'BELGRANO': 13, 'BOEDO': 5, 'CABALLITO': 6, 'CHACARITA': 15, 
        'COGHLAN': 12, 'COLEGIALES': 13, 'CONSTITUCION': 1, 'FLORES': 7, 
        'FLORESTA': 10, 'LA BOCA': 4, 'LA PATERNAL': 15, 'LINIERS': 9, 
        'MATADEROS': 9, 'MONTE CASTRO': 10, 'MONSERRAT': 1, 'NUEVA POMPEYA': 4, 
        'NUÑEZ': 13, 'PALERMO': 14, 'PARQUE AVELLANEDA': 9, 'PARQUE CHACABUCO': 7, 
        'PARQUE CHAS': 15, 'PARQUE PATRICIOS': 4, 'PUERTO MADERO': 1, 'RECOLETA': 2, 
        'RETIRO': 1, 'SAAVEDRA': 12, 'SAN CRISTOBAL': 3, 'SAN NICOLAS': 1, 
        'SAN TELMO': 1, 'VELEZ SARSFIELD': 10, 'VERSALLES': 10, 'VILLA CRESPO': 15, 
        'VILLA DEL PARQUE': 11, 'VILLA DEVOTO': 11, 'VILLA GENERAL MITRE': 11, 
        'VILLA LUGANO': 8, 'VILLA LURO': 10, 'VILLA ORTUZAR': 15, 'VILLA PUEYRREDON': 12, 
        'VILLA REAL': 10, 'VILLA RIACHUELO': 8, 'VILLA SANTA RITA': 11, 
        'VILLA SOLDATI': 8, 'VILLA URQUIZA': 12, 'PARQUE AVELLANEDA': 9
    }
    
    # Función para normalizar nombres de barrios
    def normalizar_texto(texto):
        if pd.isna(texto) or texto == 0 or str(texto).strip() == '0':
            return "Sin datos"
        if isinstance(texto, str):
            # Convertir a mayúsculas
            texto = texto.upper().strip()
            # Normalizar acentos
            texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
            # Eliminar caracteres especiales
            texto = re.sub(r'[^\w\s]', '', texto)
        return texto
    
    # Limpiar valores de barrio
    def limpiar_barrio(valor):
        if pd.isna(valor) or valor == 0 or str(valor).strip() == '0':
            return "Sin datos"
        return str(valor).strip()
    
    # Función para limpiar el valor de comuna
    def limpiar_comuna(valor):
        if pd.isna(valor) or valor == 0:
            return "Sin datos"
        if isinstance(valor, str) and re.match(r'CC-\d+', valor):
            return re.search(r'(\d+)', valor).group(1)
        return str(valor).replace('.0', '')
    
    # Aplicar limpieza y normalización
    df['barrio_original'] = df['barrio']
    df['barrio'] = df['barrio'].apply(limpiar_barrio)
    df['barrio_norm'] = df['barrio'].apply(normalizar_texto)
    df['comuna_limpia'] = df['comuna'].apply(limpiar_comuna)
    
    # Predecir comuna basada en barrio cuando sea necesario
    def asignar_comuna_por_barrio(row):
        # Si ya tiene comuna válida, mantenerla
        if row['comuna_limpia'] not in ["Sin datos", "nan"] and row['comuna_limpia'] != "":
            return row['comuna_limpia']
        
        # Si tiene barrio, intentar predecir la comuna
        if row['barrio_norm'] in mapeo_oficial_barrios:
            return str(mapeo_oficial_barrios[row['barrio_norm']])
            
        return row['comuna_limpia']  # Mantener el valor original si no se puede predecir
    
    # Crear comuna_corregida
    df['comuna_corregida'] = df.apply(asignar_comuna_por_barrio, axis=1)
    
    # Actualizar comuna_display para usar el valor corregido
    df['comuna_display'] = df['comuna_corregida']
    
    return df

df = cargar_datos()

# Sidebar para filtros
st.sidebar.header("Filtros")

# Filtro por año
años = sorted(df['anio'].unique())
año_seleccionado = st.sidebar.multiselect(
    "Seleccionar Año:",
    options=años,
    default=años[-1]  # Último año por defecto
)

# Filtro por tipo de delito
tipos_delito = sorted(df['tipo'].unique())
tipo_seleccionado = st.sidebar.multiselect(
    "Tipo de Delito:",
    options=tipos_delito,
    default=tipos_delito[:3]  # Primeros 3 tipos por defecto
)

# Filtro por día de la semana
dias = ['Laboral', 'Fin de semana']
dia_seleccionado = st.sidebar.multiselect(
    "Tipo de Día:",
    options=dias,
    default=dias
)

# Aplicar filtros
df_filtrado = df.copy()
if año_seleccionado:
    df_filtrado = df_filtrado[df_filtrado['anio'].isin(año_seleccionado)]
if tipo_seleccionado:
    df_filtrado = df_filtrado[df_filtrado['tipo'].isin(tipo_seleccionado)]
if dia_seleccionado:
    df_filtrado = df_filtrado[df_filtrado['tipo_dia'].isin(dia_seleccionado)]

# Métricas principales
st.header("Métricas Principales")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_delitos = len(df_filtrado)
    st.metric("Total Delitos", f"{total_delitos:,}")

with col2:
    delitos_con_arma = df_filtrado[df_filtrado['uso_arma'] == 'SI'].shape[0]
    porcentaje_arma = (delitos_con_arma / total_delitos * 100) if total_delitos > 0 else 0
    st.metric("Uso de Armas", f"{porcentaje_arma:.1f}%")

with col3:
    delitos_con_moto = df_filtrado[df_filtrado['uso_moto'] == 'SI'].shape[0]
    porcentaje_moto = (delitos_con_moto / total_delitos * 100) if total_delitos > 0 else 0
    st.metric("Uso de Motos", f"{porcentaje_moto:.1f}%")

with col4:
    # Excluir "Sin datos" del conteo de comunas
    comunas_afectadas = df_filtrado[df_filtrado['comuna_display'] != 'Sin datos']['comuna_display'].nunique()
    st.metric("Comunas Afectadas", comunas_afectadas)

# Gráficos
st.header("Análisis de Delitos")

# Gráfico 1: Delitos por tipo (horizontal bar chart)
st.subheader("Delitos por Tipo")
delitos_por_tipo = df_filtrado.groupby('tipo').size().reset_index(name='cantidad')
delitos_por_tipo = delitos_por_tipo.sort_values('cantidad', ascending=True)

fig_tipos = px.bar(
    delitos_por_tipo,
    y='tipo',
    x='cantidad',
    orientation='h',
    color='cantidad',
    color_continuous_scale='Reds',
    title='Cantidad de Delitos por Tipo'
)
fig_tipos.update_layout(height=400)
st.plotly_chart(fig_tipos, use_container_width=True)

# Layout de dos columnas
col1, col2 = st.columns(2)

# Gráfico 2: Delitos por año
with col1:
    delitos_por_año = df_filtrado.groupby('anio').size().reset_index(name='cantidad')
    fig_años = px.line(
        delitos_por_año, 
        x='anio', 
        y='cantidad',
        markers=True,
        title='Evolución de Delitos por Año',
        color_discrete_sequence=['crimson']
    )
    fig_años.update_layout(height=400)
    st.plotly_chart(fig_años, use_container_width=True)

# Gráfico 3: Delitos por tipo de día
with col2:
    delitos_por_dia = df_filtrado.groupby('tipo_dia').size().reset_index(name='cantidad')
    fig_dias = px.pie(
        delitos_por_dia,
        values='cantidad',
        names='tipo_dia',
        hole=0.4,
        title='Distribución por Tipo de Día',
        color_discrete_sequence=['#FF9999', '#66B2FF']
    )
    fig_dias.update_layout(height=400)
    st.plotly_chart(fig_dias, use_container_width=True)

# Gráfico 4: Mapa de calor por franja horaria y día de la semana
st.subheader("Patrones Temporales")
# Asegurar que día de semana y franja horaria son numéricos para el heatmap
df_heatmap = df_filtrado.copy()
df_heatmap['dia_semana_num'] = pd.to_numeric(df_heatmap['dia_semana_num'], errors='coerce')

# Crear heatmap de delitos por día de la semana y hora
heatmap_data = df_heatmap.groupby(['dia_semana_num', 'franja']).size().reset_index(name='cantidad')
heatmap_pivot = heatmap_data.pivot_table(
    values='cantidad', 
    index='franja', 
    columns='dia_semana_num', 
    fill_value=0
)

# Mapeo para etiquetas de días
dias_semana = {0: 'Lun', 1: 'Mar', 2: 'Mié', 3: 'Jue', 4: 'Vie', 5: 'Sáb', 6: 'Dom'}
nuevas_columnas = [dias_semana.get(col, col) for col in heatmap_pivot.columns]
heatmap_pivot.columns = nuevas_columnas

fig_heatmap = px.imshow(
    heatmap_pivot,
    labels={'y': 'Hora del día', 'x': 'Día de la semana', 'color': 'Cantidad de delitos'},
    color_continuous_scale="Reds",
    title="Mapa de calor: Delitos por día de la semana y hora"
)
fig_heatmap.update_layout(height=500)
st.plotly_chart(fig_heatmap, use_container_width=True)

# Gráfico 5: Mapa de delitos
st.header("Mapa de Delitos")

# Comprobar si hay suficientes datos
if not df_filtrado.empty:
    # Crear una copia para trabajar con el mapa
    df_mapa = df_filtrado.copy()
    
    # 1. Convertir coordenadas a formato numérico si no lo están
    df_mapa['latitud'] = pd.to_numeric(df_mapa['latitud'], errors='coerce')
    df_mapa['longitud'] = pd.to_numeric(df_mapa['longitud'], errors='coerce')
    
    # 2. Detectar y corregir el formato de las coordenadas
    # Verificar si hay coordenadas extremas que necesiten normalización
    lat_min, lat_max = df_mapa['latitud'].min(), df_mapa['latitud'].max()
    lon_min, lon_max = df_mapa['longitud'].min(), df_mapa['longitud'].max()
    
    # Normalizar solo si los valores son extremos
    if abs(lat_min) > 100 or abs(lat_max) > 100:
        # Crear nuevas columnas normalizadas
        df_mapa['latitud_map'] = df_mapa['latitud'] / 1000000
    else:
        df_mapa['latitud_map'] = df_mapa['latitud']
    
    if abs(lon_min) > 100 or abs(lon_max) > 100:
        df_mapa['longitud_map'] = df_mapa['longitud'] / 1000000
    else:
        df_mapa['longitud_map'] = df_mapa['longitud']
    
    # 3. Filtrar solo valores razonables para Buenos Aires
    df_mapa = df_mapa[(df_mapa['latitud_map'] > -35) & (df_mapa['latitud_map'] < -34) & 
                     (df_mapa['longitud_map'] > -59) & (df_mapa['longitud_map'] < -58)]
    
    # 4. Preparar datos para el mapa coroplético
try:
    # Agrupar delitos por barrio para el mapa
    delitos_por_barrio = df_filtrado[df_filtrado['barrio'] != "Sin datos"].groupby('barrio').size().reset_index(name='cantidad')
    
    # Cargar GeoJSON con los límites de los barrios de Buenos Aires
    import requests
    
    # URL del GeoJSON de barrios de Buenos Aires
    url_geojson = "https://cdn.buenosaires.gob.ar/datosabiertos/datasets/ministerio-de-educacion/barrios/barrios.geojson"
    
    # Descargar el GeoJSON
    response = requests.get(url_geojson)
    barrios_geojson = response.json()
    
    # Examinar la estructura del GeoJSON para asegurar compatibilidad
    # Identificar la propiedad que contiene los nombres de barrios
    properties_keys = barrios_geojson['features'][0]['properties'].keys()
    
    # Buscar la clave más apropiada para los nombres de barrios
    barrio_key = next((k for k in properties_keys if 'barrio' in k.lower() or 'nombre' in k.lower()), None)
    if not barrio_key:
        barrio_key = list(properties_keys)[0]  # Usar la primera propiedad si no se encuentra una específica
    
    # Mostrar los primeros barrios del GeoJSON para verificar
    barrios_en_geojson = [feature['properties'][barrio_key] for feature in barrios_geojson['features'][:5]]
    
    # Ajustar el GeoJSON para que coincida con los nombres de barrios
    for feature in barrios_geojson['features']:
        feature['id'] = feature['properties'][barrio_key].upper()  # Convertir a mayúsculas para coincidir
    
    # Normalizar nombres de barrios para mejorar coincidencia
    delitos_por_barrio['barrio_norm'] = delitos_por_barrio['barrio'].str.upper().str.strip()
    
    # Verificar coincidencias entre nuestros datos y el GeoJSON
    barrios_geojson_set = set()
    for feature in barrios_geojson['features']:
        barrios_geojson_set.add(feature['id'])
    barrios_datos_set = set(delitos_por_barrio['barrio_norm'])

    barrios_coincidentes = barrios_geojson_set.intersection(barrios_datos_set)

    # Filtrar solo los barrios que coinciden con el GeoJSON para evitar errores
    delitos_por_barrio_filtrado = delitos_por_barrio[delitos_por_barrio['barrio_norm'].isin(barrios_coincidentes)]

    # Verificar si hay suficientes coincidencias
    if len(barrios_coincidentes) == 0 or len(delitos_por_barrio_filtrado) == 0:
        st.error("No se encontraron coincidencias entre los barrios de tus datos y el GeoJSON.")
        st.warning("Intentando con un método alternativo de normalización...")
        
        # Método alternativo: usar aproximaciones de nombres
        # Remover acentos, espacios y caracteres especiales
        import unicodedata
        import re
        
        def normalizar_texto(texto):
            if isinstance(texto, str):
                # Normalizar a NFD y eliminar diacríticos
                texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('ascii')
                # Convertir a mayúsculas y eliminar caracteres no alfanuméricos
                texto = re.sub(r'[^A-Z0-9]', '', texto.upper())
                return texto
            return str(texto).upper()  # Manejar casos de valores no string
        
        # Normalizar ambos conjuntos
        for feature in barrios_geojson['features']:
            feature['id'] = normalizar_texto(feature['properties'][barrio_key])
        
        delitos_por_barrio['barrio_norm'] = delitos_por_barrio['barrio'].apply(normalizar_texto)
        
        # Verificar nuevamente las coincidencias
        barrios_geojson_set = set()
        for feature in barrios_geojson['features']:  # Corregido para evitar usar solo el último
            barrios_geojson_set.add(feature['id'])
        barrios_datos_set = set(delitos_por_barrio['barrio_norm'])
        barrios_coincidentes = barrios_geojson_set.intersection(barrios_datos_set)
        st.write(f"Tras normalización adicional, coincidencias: {len(barrios_coincidentes)} de {len(barrios_datos_set)} barrios")
        
        # Actualizar el DataFrame filtrado con los nuevos barrios coincidentes
        delitos_por_barrio_filtrado = delitos_por_barrio[delitos_por_barrio['barrio_norm'].isin(barrios_coincidentes)]

    # Ahora verificamos si tenemos datos para mostrar después de todos los intentos de coincidencia
    if len(delitos_por_barrio_filtrado) > 0:
        # Crear el mapa coroplético
        fig_mapa = px.choropleth_mapbox(
            delitos_por_barrio_filtrado,
            geojson=barrios_geojson,
            locations='barrio_norm',  # Usar la versión normalizada
            featureidkey='id',
            color='cantidad',
            color_continuous_scale="Reds",
            mapbox_style="carto-positron",
            zoom=9.5,
            center={"lat": -34.6, "lon": -58.4},
            opacity=0.7,
            title="Mapa Coroplético: Delitos por Barrio"
        )
        
        # Centrar en Buenos Aires
        fig_mapa.update_layout(
            mapbox=dict(
                center=dict(lat=-34.6, lon=-58.4),
                zoom=10
            ),
            height=600
        )
        
        st.plotly_chart(fig_mapa, use_container_width=True)
        
        # Información adicional sobre los datos mostrados en el mapa
        st.info(f"El mapa muestra {delitos_por_barrio_filtrado['cantidad'].sum():,} delitos distribuidos en {len(delitos_por_barrio_filtrado)} barrios.")
    else:
        st.error("No se pudieron mapear los barrios. Mostrando mapa alternativo.")
        raise Exception("Sin coincidencias de barrios para el mapa coroplético")
        
except Exception as e:
    st.error(f"Error al crear el mapa coroplético: {str(e)}")
    st.info("Mostrando mapa de densidad alternativo...")
    
    # Si hay un error con el mapa coroplético, mostrar un mapa de densidad
    if not df_mapa.empty:
        # Mapa de densidad como alternativa
        fig_mapa = px.density_mapbox(
            df_mapa,
            lat='latitud_map',
            lon='longitud_map',
            z='cantidad',
            radius=10,
            center={"lat": -34.6, "lon": -58.4},
            zoom=10,
            mapbox_style="carto-positron",
            title="Mapa de Densidad de Delitos (alternativo)"
        )
        
        fig_mapa.update_layout(height=600)
        st.plotly_chart(fig_mapa, use_container_width=True)
    else:
        st.error("No hay datos válidos para mostrar en el mapa después de la corrección de coordenadas.")
        st.write("Prueba seleccionando diferentes tipos de delitos o años.")

# Análisis por comunas
st.header("Análisis por Comuna")
# Filtrar comunas sin datos antes de agrupar
df_comunas_filtrado = df_filtrado[df_filtrado['comuna_display'] != 'Sin datos']
# Usar comuna_display en lugar de comuna para evitar duplicados con decimales
delitos_por_comuna = df_comunas_filtrado.groupby('comuna_display').size().reset_index(name='cantidad')
delitos_por_comuna = delitos_por_comuna.sort_values('cantidad', ascending=False)

fig_comunas = px.bar(
    delitos_por_comuna.head(10),
    x='comuna_display',  # Usar comuna_display
    y='cantidad',
    color='cantidad',
    color_continuous_scale='Reds',
    title='Top 10 Comunas con Mayor Número de Delitos',
    labels={"comuna_display": "Comuna"}  # Etiqueta mejorada
)
# Añadir prefijo "Comuna" a las etiquetas del eje x
fig_comunas.update_xaxes(tickprefix="Comuna ")
st.plotly_chart(fig_comunas, use_container_width=True)

# Pie chart para tipos de delito por comuna seleccionada
col1, col2 = st.columns(2)

with col1:
    # Permitir seleccionar una comuna - usar comuna_display (excluyendo "Sin datos")
    comunas_lista = sorted([c for c in df_filtrado['comuna_display'].unique() 
                          if c != 'nan' and c != 'Sin datos'])
    if comunas_lista:
        comuna_seleccionada = st.selectbox("Selecciona una comuna para analizar:", comunas_lista)
        
        # Filtrar por la comuna seleccionada - usar comuna_display para evitar problemas de tipo
        df_comuna = df_filtrado[df_filtrado['comuna_display'] == comuna_seleccionada]
        
        # Gráfico de delitos por tipo en la comuna seleccionada
        delitos_comuna_tipo = df_comuna.groupby('tipo').size().reset_index(name='cantidad')
        
        fig_comuna_tipo = px.pie(
            delitos_comuna_tipo,
            values='cantidad',
            names='tipo',
            title=f'Tipos de Delito en Comuna {comuna_seleccionada}'
        )
        st.plotly_chart(fig_comuna_tipo, use_container_width=True)

with col2:
    # Evolución temporal para la comuna seleccionada
    if 'comuna_seleccionada' in locals() and not df_comuna.empty:
        df_comuna['mes_año'] = df_comuna['fecha'].dt.strftime('%Y-%m')
        delitos_comuna_tiempo = df_comuna.groupby('mes_año').size().reset_index(name='cantidad')
        
        fig_comuna_tiempo = px.line(
            delitos_comuna_tiempo,
            x='mes_año',
            y='cantidad',
            markers=True,
            title=f'Evolución Temporal de Delitos en Comuna {comuna_seleccionada}'
        )
        st.plotly_chart(fig_comuna_tiempo, use_container_width=True)

# Análisis Bidireccional Comuna - Barrio
st.header("Relación Comuna - Barrio")

# Crear tabs para navegar entre las dos vistas
tab_comuna, tab_barrio = st.tabs(["Explorar por Comuna", "Explorar por Barrio"])

# Tab 1: Explorar por Comuna
with tab_comuna:
    # Seleccionar comuna - usar comuna_display (excluyendo "Sin datos")
    comunas_lista = sorted([c for c in df_filtrado['comuna_display'].unique() 
                          if c != 'nan' and c != 'Sin datos'])
    if comunas_lista:
        comuna_seleccionada_tab = st.selectbox(
            "Selecciona una comuna:", 
            comunas_lista,
            key="comuna_tab"
        )
        
        # Obtener barrios de la comuna seleccionada - asegurar comparación correcta
        barrios_comuna = df_filtrado[df_filtrado['comuna_display'] == comuna_seleccionada_tab]['barrio'].unique()
        
        # Mostrar lista de barrios en esta comuna
        st.subheader(f"Barrios en Comuna {comuna_seleccionada_tab}")
        
        # Contar delitos por barrio en esta comuna - usar comuna_display
        barrios_delitos = df_filtrado[(df_filtrado['comuna_display'] == comuna_seleccionada_tab) & 
                            (df_filtrado['barrio'] != "Sin datos")].groupby('barrio').size().reset_index(name='cantidad')
        barrios_delitos = barrios_delitos.sort_values('cantidad', ascending=False)
        
        # Gráfico de barras horizontal para los barrios
        fig_barrios = px.bar(
            barrios_delitos,
            y='barrio',
            x='cantidad',
            orientation='h',
            color='cantidad',
            color_continuous_scale='Blues',
            title=f'Distribución de Delitos por Barrio en Comuna {comuna_seleccionada_tab}'
        )
        fig_barrios.update_layout(height=min(600, len(barrios_comuna) * 30 + 200))
        st.plotly_chart(fig_barrios, use_container_width=True)
        
        # Tabla con información adicional (opcional)
        with st.expander("Ver tabla detallada de barrios"):
            st.write(barrios_delitos)

# Tab 2: Explorar por Barrio
with tab_barrio:
    # Filtrar por barrio
    barrios_lista = sorted([b for b in df_filtrado['barrio'].unique() if b != "Sin datos"])
    if barrios_lista:
        barrio_seleccionado = st.selectbox(
            "Selecciona un barrio:", 
            barrios_lista
        )
        
       # Obtener comuna(s) del barrio seleccionado - filtrar "Sin datos"
        comunas_barrio = df_filtrado[(df_filtrado['barrio'] == barrio_seleccionado) & 
                                  (df_filtrado['comuna_display'] != 'Sin datos')]['comuna_display'].unique()

        # Si hay comunas para este barrio
        if len(comunas_barrio) > 0:
            # Contar ocurrencias de cada comuna para este barrio - usar comuna_display
            # Excluir "Sin datos" del conteo
            comuna_counts = df_filtrado[(df_filtrado['barrio'] == barrio_seleccionado) & 
                                     (df_filtrado['comuna_display'] != 'Sin datos')]['comuna_display'].value_counts()
            comuna_principal = comuna_counts.idxmax()  # Comuna con más registros
            
            # Definir comuna_barrio como la más frecuente
            comuna_barrio = comuna_principal
            
            # En caso de que un barrio aparezca en múltiples comunas
            if len(comunas_barrio) > 1:
                st.warning(f"⚠️ El barrio {barrio_seleccionado} aparece en {len(comunas_barrio)} comunas diferentes.")
                
                # Crear DataFrame para mostrar la distribución
                comuna_data = []
                for comuna in comunas_barrio:
                    count = df_filtrado[(df_filtrado['barrio'] == barrio_seleccionado) & 
                                      (df_filtrado['comuna_display'] == comuna)].shape[0]
                    porcentaje = (count / df_filtrado[(df_filtrado['barrio'] == barrio_seleccionado) & 
                                                   (df_filtrado['comuna_display'] != 'Sin datos')].shape[0]) * 100
                    comuna_data.append({
                        "Comuna": f"Comuna {comuna}",
                        "Cantidad": count,
                        "Porcentaje": f"{porcentaje:.1f}%"
                    })
                
                # Mostrar tabla de distribución
                st.write("Distribución de delitos por comuna para este barrio:")
                st.table(pd.DataFrame(comuna_data))
                
                # Mostrar distribución como gráfico de pastel (excluyendo "Sin datos")
                comuna_barrio_count = df_filtrado[(df_filtrado['barrio'] == barrio_seleccionado) & 
                                               (df_filtrado['comuna_display'] != 'Sin datos')].groupby('comuna_display').size().reset_index(name='cantidad')
                
                fig_comunas_barrio = px.pie(
                    comuna_barrio_count,
                    values='cantidad',
                    names='comuna_display',  # Usar comuna_display
                    title=f'Distribución de Delitos por Comuna en el Barrio {barrio_seleccionado}',
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                st.plotly_chart(fig_comunas_barrio, use_container_width=True)
                
                # Mensaje aclaratorio
                st.info(f"📌 Para los análisis siguientes, se considerará la Comuna {comuna_principal} (la más frecuente).")
            else:
                # Solo hay una comuna - mostrar mensaje normal
                st.subheader(f"El barrio {barrio_seleccionado} pertenece a la Comuna {comuna_barrio}")
        else:
            # No hay comunas disponibles para este barrio
            st.error(f"No se encontraron datos de comunas para el barrio {barrio_seleccionado}")
            comuna_barrio = "No disponible"
        
        # Análisis de delitos en este barrio
        df_barrio = df_filtrado[df_filtrado['barrio'] == barrio_seleccionado]
        
        # Crear visualizaciones para el barrio
        col1, col2 = st.columns(2)
        
        with col1:
            # Tipos de delito en el barrio
            tipos_barrio = df_barrio.groupby('tipo').size().reset_index(name='cantidad')
            tipos_barrio = tipos_barrio.sort_values('cantidad', ascending=False)
            
            fig_tipos_barrio = px.bar(
                tipos_barrio,
                x='tipo',
                y='cantidad',
                color='cantidad',
                color_continuous_scale='Greens',
                title=f'Tipos de Delito en el Barrio {barrio_seleccionado}'
            )
            st.plotly_chart(fig_tipos_barrio, use_container_width=True)
            
        with col2:
            # Evolución temporal de delitos en el barrio
            df_barrio['mes_año'] = df_barrio['fecha'].dt.strftime('%Y-%m')
            delitos_barrio_tiempo = df_barrio.groupby('mes_año').size().reset_index(name='cantidad')
            
            fig_barrio_tiempo = px.line(
                delitos_barrio_tiempo,
                x='mes_año',
                y='cantidad',
                markers=True,
                title=f'Evolución Temporal de Delitos en {barrio_seleccionado}',
                color_discrete_sequence=['green']
            )
            st.plotly_chart(fig_barrio_tiempo, use_container_width=True)
        
        # Comparativa con otros barrios de la misma comuna
        if comuna_barrio != "No disponible":
            st.subheader(f"Comparativa con otros barrios de la Comuna {comuna_barrio}")
            
            # Obtener todos los barrios de esta comuna - usar comuna_display para correcta comparación
            barrios_misma_comuna = df_filtrado[(df_filtrado['comuna_display'] == comuna_barrio) & 
                                 (df_filtrado['barrio'] != "Sin datos")].groupby('barrio').size().reset_index(name='cantidad')
            barrios_misma_comuna = barrios_misma_comuna.sort_values('cantidad', ascending=False)
            
            # Resaltar el barrio seleccionado
            barrios_misma_comuna['color'] = barrios_misma_comuna['barrio'].apply(
                lambda x: '#1F77B4' if x != barrio_seleccionado else '#FF7F0E'
            )
            
            fig_comp_barrios = px.bar(
                barrios_misma_comuna,
                x='barrio',
                y='cantidad',
                color='barrio',
                title=f'Delitos en los Barrios de la Comuna {comuna_barrio}',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            # Resaltar el barrio seleccionado
            for i, bar in enumerate(fig_comp_barrios.data):
                if bar.name == barrio_seleccionado:
                    fig_comp_barrios.data[i].marker.color = 'red'
            
            st.plotly_chart(fig_comp_barrios, use_container_width=True)

# Nota al pie
st.markdown("---")
st.caption("Dashboard creado con Streamlit y Plotly Express. Datos de delitos 2016-2023.")