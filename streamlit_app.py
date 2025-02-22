#pip install pandas
#pip install shapely
#pip install geopandas

import streamlit as st
import pandas as pd
from shapely import wkt  # Para procesar la geometría de los puntos de interés
from shapely.geometry import Point  # Importar Point
import geopandas as gpd
from math import radians, cos, sin, sqrt, atan2
import math
from pathlib import Path
import folium
from streamlit_folium import folium_static

#----------------------------------------------------
# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='ExpansiON App',
    page_icon='logo.png', # This is an emoji shortcode. Could be a URL too.
)


#----------------------------------------------------
# CSS para estilizar la aplicación
st.markdown("""
    <style>
    .reportview-container {
        background-color: #f2e9f5;  /* Color de fondo suave (lila claro) */
    }
    .stButton>button {
        background-color: #9b59b6;  /* Color lila para botones */
        color: #FFFFFF;  /* Color del texto de los botones */
    }
    .stTextInput>div>input {
        background-color: #FFFFFF;  /* Fondo blanco para inputs */
        color: #3b3b3b;  /* Color del texto (gris oscuro) */
    }
    .stMarkdown {
        color: #000000;  /* Color del texto (negro) */
    }
  
    /* Cambiar el color de la barra del slider */
    .stSlider .my-slider .st-bq {
        background-color: #9b59b6;
    }
  
    /* Estilo para el botón de búsqueda */
    .full-width-button {
        width: 100%;
        background-color: #4CAF50; /* Cambia el color de fondo */
        color: white; /* Cambia el color del texto */
        border: none; /* Elimina el borde */
        padding: 15px; /* Añade espacio interno */
        text-align: center; /* Centra el texto */
        font-size: 16px; /* Tamaño de fuente */
        cursor: pointer; /* Cambia el cursor al pasar el ratón */
        border-radius: 5px; /* Esquinas redondeadas */
    }
    </style>
    """, unsafe_allow_html=True)


#----------------------------------------------------
# Función para calcular la distancia entre dos puntos geográficos
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en kilómetros
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c * 1000  # Devuelve la distancia en metros

# Cargar los datos de los CSV
df_locales = pd.read_csv('fincaraiz_final.csv')
df_puntos_interes = pd.read_csv('bogota_filtered_pois.csv')

# Invertir coordenadas de los locales y separar latitud y longitud
df_locales[['latitud', 'longitud']] = df_locales['location_point'].str.split(', ', expand=True)
df_locales['latitud'] = df_locales['latitud'].astype(float)
df_locales['longitud'] = df_locales['longitud'].astype(float)
df_locales['area'] = df_locales['area'].str.replace(' m²', '', regex=False).astype(float)
df_locales = df_locales.dropna(subset=['estrato'])
df_locales['estrato'] = df_locales['estrato'].astype(str)
df_locales['estrato'] = df_locales['estrato'].replace({' 110.0': '6.0', '110.0 ': '6.0', '110.0': '6.0'})


# Convertir la columna 'geometry' a objetos geométricos usando WKT
df_puntos_interes['geometry'] = df_puntos_interes['geometry'].apply(wkt.loads)

# Filtrar solo los objetos que son de tipo Point
df_puntos_interes = df_puntos_interes[df_puntos_interes['geometry'].apply(lambda x: isinstance(x, Point))]

# Extraer latitud y longitud de los puntos de interés
df_puntos_interes['latitud'] = df_puntos_interes['geometry'].apply(lambda point: point.y)
df_puntos_interes['longitud'] = df_puntos_interes['geometry'].apply(lambda point: point.x)

# Función para buscar locales cerca de un tipo de punto de interés
def buscar_locales_cerca(tipo_punto, rango):
    # Filtrar puntos de interés por tipo
    puntos_interes_filtrados = df_puntos_interes[df_puntos_interes['amenity'].str.lower() == tipo_punto.lower()]
    
    resultados = []

    # Calcular distancias
    for index_local, local in df_locales.iterrows():
        local_lat = local['latitud']
        local_lon = local['longitud']
        
        for index_punto, punto in puntos_interes_filtrados.iterrows():
            punto_lat = punto['latitud']
            punto_lon = punto['longitud']
            
            distancia = haversine(local_lat, local_lon, punto_lat, punto_lon)
            
            if distancia <= rango:
                resultados.append({
                    'Propiedad': local['property_type'],  # Columna de df_locales
                    'Precio': local['price'],  # Columna de df_locales
                    'Area': local['area'],  # Columna de df_locales
                    'Estrato': local['estrato'],  # Columna de df_locales
                    'Baños': local['bathrooms'],  # Columna de df_locales
                    'Imagen': local['main_image'],
                    'Carousel': local['carousel_images'],
                    'Arrendatario': local['publisher'],  # Columna de df_locales
                    'Habitaciones': local['bedrooms'],  # Columna de df_locales
                    'Garaje': local['garage'],  # Columna de df_locales
                    'Tipo de punto': punto['amenity'],
                    'Punto de Interés Nombre': punto['name'],  # Columna de df_puntos_interes
                    'Distancia (metros)': distancia,  # Distancia en metros
                    'Coordenada Local': f"({local['latitud']}, {local['longitud']})",  # Coordenadas del local
                    'Coordenada Punto': f"({punto['latitud']}, {punto['longitud']})"  # Coordenadas del punto de interés
                })

    # Convertir resultados a DataFrame
    df_resultados = pd.DataFrame(resultados)
    return df_resultados


# Streamlit App
st.image("marca.png", use_column_width=True)
st.title("Encuentra espacios con ExpansiON")
st.subheader("Selecciona los siguientes datos:")

# Selector para tipo de punto de interés
tipos_puntos_interes = df_puntos_interes['amenity'].unique()

# Crear dos columnas para el tipo de punto de interés y el rango de búsqueda
col1, col2 = st.columns(2)

# Filtro en la primera columna
with col1:
    tipo_punto_interes = st.selectbox("Tipo de punto de interés:", tipos_puntos_interes)

# Slicer en la segunda columna
with col2:
    rango_busqueda = st.slider("Rango de búsqueda (en metros):", min_value=0, max_value=3000, value=500)

# Filtros (fuera del botón de búsqueda)
col1, col2, col3, col4 = st.columns(4)

# Filtro por Tipo de Propiedad (botones)
with col1:
    tipo_propiedad = st.multiselect("Tipo de propiedad:", df_locales['property_type'].unique().tolist())

# Filtro por Área (slider)
with col2:    
    area_min, area_max = df_locales['area'].min(), df_locales['area'].max()
    area_max = min(area_max, 4000)
    area_min_selected, area_max_selected = st.slider(
        "Rango de área:",
        min_value=float(area_min),
        max_value=float(area_max),
        value=(float(area_min), float(area_max))
    )

# Filtro por Precio (slider)
with col3:
    precio_min, precio_max = st.slider("Rango de precios:", 0, 1000000, (0, 1000000))

# Filtro por Estrato (botones)
with col4:
    estratos_unicos = sorted(df_locales['estrato'].unique().tolist())
    estrato = st.selectbox("Estrato:", options=estratos_unicos) 

# Botón para buscar
if st.button("Buscar Locales"):
    # Llama a la función de búsqueda
    resultados_encontrados = buscar_locales_cerca(tipo_punto_interes, rango_busqueda)

    # Aplicar filtros adicionales a los resultados
    if not resultados_encontrados.empty:
        # Filtrar por tipo de propiedad
        if tipo_propiedad:
            resultados_encontrados = resultados_encontrados[resultados_encontrados['Propiedad'].isin(tipo_propiedad)]
        
        # Filtrar por área
        if area_min_selected and area_max_selected:
            resultados_encontrados = resultados_encontrados[
                (resultados_encontrados['Area'] >= area_min_selected) & 
                (resultados_encontrados['Area'] <= area_max_selected)
            ]
        
        # Filtrar por precio
        if precio_min and precio_max:
            resultados_encontrados = resultados_encontrados[
                (resultados_encontrados['Precio'] >= precio_min) & 
                (resultados_encontrados['Precio'] <= precio_max)
            ]

        # Filtrar por estrato
        if estrato:
            resultados_encontrados = resultados_encontrados[resultados_encontrados['Estrato'] == estrato]
        
       # Eliminar duplicados basados en una columna clave como 'Propiedad' o algún ID único
        resultados_unicos = resultados_encontrados.drop_duplicates(subset=['Coordenada Local'])  # Ajusta la columna clave

        # Generar tarjetas para cada resultado encontrado
        if not resultados_unicos.empty:
            total_inmuebles = len(resultados_unicos)
            st.info(f"El total de inmuebles comerciales en arrendamiento alrededor de este punto de interés es de: {total_inmuebles}")

           # Crear GeoDataFrame para los locales
            geometry_locales = [Point(float(coord.split(',')[1][:-1]), float(coord.split(',')[0][1:])) 
                                for coord in resultados_encontrados['Coordenada Local']]
            gdf_locales = gpd.GeoDataFrame(resultados_encontrados, geometry=geometry_locales, crs="EPSG:4326")
    
            # Crear GeoDataFrame para los puntos de interés
            geometry_pois = [Point(float(coord.split(',')[1][:-1]), float(coord.split(',')[0][1:])) 
                             for coord in resultados_encontrados['Coordenada Punto']]
            gdf_pois = gpd.GeoDataFrame(resultados_encontrados, geometry=geometry_pois, crs="EPSG:4326")
    
            # Crear un mapa centrado en Bogotá
            mapa_bogota = folium.Map(location=[4.711, -74.072], zoom_start=12)
    
            # Añadir locales al mapa
            for idx, row in gdf_locales.iterrows():
                folium.Marker(
                    [row.geometry.y, row.geometry.x],
                    popup=f"{row['Propiedad']} - ${row['Precio']}",
                    icon=folium.Icon(color='purple', icon='home')
                ).add_to(mapa_bogota)
    
            # Añadir puntos de interés al mapa
            for idx, row in gdf_pois.iterrows():
                folium.Marker(
                    [row.geometry.y, row.geometry.x],
                    popup=f"{row['Tipo de punto']}: {row['Punto de Interés Nombre']}",
                    icon=folium.Icon(color='green', icon='info-sign')
                ).add_to(mapa_bogota)
    
            # Mostrar el mapa en Streamlit
            folium_static(mapa_bogota)
            
            # Definir cuántos resultados por fila (en este caso 3 por fila)
            cols_per_row = 3
            rows = [resultados_unicos.iloc[i:i+cols_per_row] for i in range(0, len(resultados_unicos), cols_per_row)]

            for row in rows:
                cols = st.columns(cols_per_row)  # Dividir la fila en 3 columnas
                for index, (col, result) in enumerate(zip(cols, row.iterrows())):
                    _, data = result  # 'data' contiene la fila actual del DataFrame
                    
                    with col:
                        # Crear un contenedor con un tamaño fijo para la imagen
                        st.markdown(f"<div style='width:150px; height:150px; overflow:hidden; text-align:center;'>"
                                    f"<img src='{data['Imagen']}' style='max-width:100%; max-height:100%;'></div>", 
                                    unsafe_allow_html=True)
                        
                        # Mostrar la información de la propiedad debajo de la imagen
                        st.markdown(f"### {data['Propiedad']} - ${data['Precio']}")
                        st.markdown(f"**Área:** {data['Area']} m²  \n"
                                    f"**Estrato:** {data['Estrato']}  \n"
                                    f"**Baños:** {data['Baños']}  \n"
                                    f"**Habitaciones:** {data['Habitaciones']}  \n"
                                    f"**Garaje:** {data['Garaje']}  \n"
                                    f"**Arrendatario:** {data['Arrendatario']}  \n"
                                    f"**Tipo de Punto de Interés:** {data['Tipo de punto']}  \n"
                                    f"**Punto de Interés Nombre:** {data['Punto de Interés Nombre']}  \n"
                                    f"**Distancia (metros):** {data['Distancia (metros)']:.2f}  \n")
                        st.markdown("---")  # Línea de separación entre resultados

        else:
            st.warning("No se encontraron resultados para los criterios seleccionados.")

