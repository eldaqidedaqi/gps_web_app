# GPS Web App with Flask

## Descripción:
Esta aplicación web permite:
- Buscar ubicaciones y mostrarlas en un mapa usando coordenadas GPS.
- Calcular la distancia entre dos puntos usando la fórmula Haversine.
- Triangular la posición de un punto usando tres puntos GPS y sus distancias.

## Instalación:
1. Clona el repositorio: 
git clone https://github.com/eldaqidedaqi/gps_web_app.git

2. Instala las dependencias:
pip install -r requirements.txt

3. Ejecuta la aplicación:
python app.py

## Funcionalidades:
- **Buscar ubicaciones:** Muestra una ubicación ingresada en un mapa interactivo.
- **Calcular distancia:** Calcula la distancia entre dos puntos usando coordenadas GPS.
- **Triangulación:** Triangula la posición de un punto usando tres puntos de referencia y sus distancias.

## Dependencias:
- Flask
- Folium
- Geopy

Esto organiza todo el contenido del proyecto, desde la estructura de archivos hasta el código que debe ir en cada uno.

##   /gps_web_app/                        ##
##   │                                    ##
##   ├── /templates/                      ##
##   │   ├── index.html                   ##
##   │   ├── distance_form.html           ##
##   │   ├── distance_result.html         ##
##   │   ├── triangulation_form.html      ##
##   │   └── map.html                     ##
##   │                                    ##
##   ├── /static/                         ##
##   │   └── map.html                     ##
##   │                                    ##
##   ├── app.py                           ##
##   ├── requirements.txt                 ##
##   └── README.md                        ##
###############################################################################################################################
