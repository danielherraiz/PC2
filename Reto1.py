from datetime import datetime
import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import os


st.set_page_config(
    page_title="Team Statistics",
    page_icon=":soccer:",
    #layout="wide",
)

st.title("PC2 Reto 1")
st.header("Daniel Herraiz")

## FUNCIONES PARA OBTENCION DE LOS DATOS DESDE REQUEST Y CACHE ##

#función para obtener el path del archivo python (no vale el relativo al ejecutarse streamlit)
def getCacheFolderPath():
    pythonFile_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(pythonFile_path, "cached_pages")

#Buscar si existe un archivo en cache para la página solicitada
def checkCachedFile(pageNumber):
    cacheFolderPath = getCacheFolderPath()
    cacheFilePath = os.path.join(cacheFolderPath, f"cachedPage_{pageNumber}.html")
    if(os.path.exists(cacheFilePath)):
        with open(cacheFilePath,"r") as cacheFile:
            print("cache read")
            return cacheFile.read()
    else:
        return ''
    
#Guardar información en cache
def upsertCachedFile (pageNumber, pageContent):
    # os.makedirs(data, exist_ok=True)
    cacheFolderPath = getCacheFolderPath()
    os.makedirs(cacheFolderPath, exist_ok=True)
    cacheFilePath = os.path.join(cacheFolderPath, f"cachedPage_{pageNumber}.html")
    with open(cacheFilePath, "wb") as cacheFile:
        print('en upsert')
        cacheFile.write(pageContent)

#Obtener el contenido de la página
origin_list = []
def getPageContent (pageNumber):
    cachedContent = checkCachedFile(pageNumber)
    if cachedContent!= '':
        print(f"pag {pageNumber} obtenida desde cache")
        return cachedContent, 'cache'
    else:  
        url = f"https://www.scrapethissite.com/pages/forms/?page_num={pageNumber}"
        timeout = 5
        retries = 4
        delay = 2
        for attempt in range(1, retries + 1):
            try:
                page = requests.get(url, timeout=timeout)
                if page.status_code != 200:
                    raise Exception(f"Se esperaba 200, se obtuvo {page.status_code}")
                print(f"Status code: {page.status_code}")
                try:
                    upsertCachedFile(pageNumber, page.content)
                except Exception as e:
                    print(f'Error al actualizar cache pag {pageNumber}: {e}')
                return page.content, 'request'
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                print(f"Error de red intento {attempt}: {e}")
                if attempt < retries:
                    time.sleep(delay)
                else:
                    raise Exception(f"Error al obtener página {pageNumber} tras {retries} intentos.")
    

#Obtener el dataframe del contenido
def getDfFromPage (pageNumber, withFilter, minGoalDif):
    pageContent, origin = getPageContent(pageNumber)
    print(f"content ok {pageNumber}")
    table = BeautifulSoup(pageContent,"html.parser").find("table", class_="table")
    #Puedo extraer todas las columnas
    columnNames = [th.get_text(strip=True) for th in table.find_all("th")]
    #O forzar las columnas sugeridas 
    columnNames = ["Team name","Year","Wins","Losses","+/-"]
    #Extraigo las filas
    rows = table.find_all("tr", class_="team")
    #Extraigo la información de cada campo en cada fila
    teams = []
    for row in rows:
        #Extra; primero aplico el filtro +/- si procede 
        if withFilter and int(row.find("td", class_=re.compile("diff")).get_text(strip=True)) <= minGoalDif:
            #filtro por tag y por clase teniendo en cuenta las columnas solicitadas
            continue
        values = [td.get_text(strip=True) for td in row.find_all("td", class_=["name","year","wins","losses",re.compile("diff")])]
        teams.append(values)  
    pageDf = pd.DataFrame(teams, columns=columnNames)
    #  "+/-" a integer
    pageDf["+/-"] = pd.to_numeric(pageDf["+/-"], errors='coerce').fillna(0).astype(int)
    return pageDf, origin

#Obtener un dataframe de un rango de páginas
def getDfFromPageRange (firstPage, lastPage, withFilter, minGoalDif):
    resultDf = pd.DataFrame()
    #try:
    for i in range(firstPage, lastPage + 1):
        my_bar.progress(i/lastPage, text= f"cargando página {i} de {lastPage}")
        pageDf, origin = getDfFromPage(i,withFilter,minGoalDif)
        if resultDf.empty:
            resultDf = pageDf.copy()
        else:
            resultDf = pd.concat([resultDf, pageDf], ignore_index = True)
        origin_list.append({
            "Page": i,
            "Origin": origin
        })
        
    #except Exception:
        #print ("Rango inválido de páginas, prueba otros valores")
    return resultDf, origin_list

#Extra para borrar el cache y testear que funciona el sistema de cache
def reviewDeleteCacheFolder(delete):
    folderPath = getCacheFolderPath()
    print(f'a borrar {folderPath}')
    if os.path.exists(folderPath):
        if(delete):
            st.sidebar.success("Cache vaciado: ")
        else:
            st.sidebar.info("Archivos en cache: ")
        #Check o delete los archivos
        for filename in os.listdir(folderPath):
            file_path = os.path.join(folderPath, filename)
            if os.path.isfile(file_path):
                if delete: os.remove(file_path)
                st.sidebar.write(f"  {filename}")
        #Check o delete la carpeta
        if delete: os.rmdir(folderPath)
        print('vaciado')
        
    else:
        print('no vaciado')
        st.sidebar.warning("No se ha encontrado nada en cache")

### CODIGO PARA INTERACTUAR CON LA APLICACIÓN EN STREAMLIT
st.sidebar.header("Gestión de cache")

tab1, tab2 = st.tabs(["Una página", "Rango de páginas (Extra)"])
filterValue=''

with tab1:
    st.header("Datos de una página")
    pageNumber = st.number_input('Introduce un número', step=1, min_value=1, max_value=24)
    filter = st.checkbox("¿Aplicar filtro de diferencia de goles? (Extra)",key="filterOnePage")
    placeholderFilter1 = st.empty()
    #if st.button("Reset",key="resetOnePage"):
        #resetFilterOnePage()
    filterValue = placeholderFilter1.number_input('Introduce un mínimo de diferencia de goles para el filtro',key='filterValueOnePage',disabled=not filter, step=1,)
   
    if st.button("Obtener",key='onePageButton'):
        with st.spinner("Buscando datos de equipos..."):
            fromCache = False
            #cacheData={'From Cache':getCacheDetails(pageNumber)}
            df_onePag, origin = getDfFromPage(pageNumber, filter, filterValue)
            if df_onePag.shape[0] > 0:
                st.success(f"Se han encontrado {df_onePag.shape[0]} equipos")
            else:
                st.error(f"No se han encontrado equipos")
            print(df_onePag.shape)
            #df_onePag.head(10)
            st.dataframe(df_onePag)
            st.sidebar.info(f'La información fue obtenida desde {origin}')

with tab2:
    st.header("Datos de un rango de páginas")
    slider_range = st.slider("Selecciona un rango de páginas",min_value=1, max_value=24, value=[1,8])
    filter = st.checkbox("¿Aplicar filtro de diferencia de goles? (Extra)",key="filterPageRange")
    filterValue = st.number_input('Introduce un mínimo de diferencia de goles para el filtro',key='filterValuePageRange',disabled=not filter, step=1)
    
    if st.button("Obtener",key='pageRangeButton'):
        current_time = datetime.now().time()
        print(current_time)
        with st.spinner("Buscando datos de equipos..."):
            my_bar = st.progress(0,text=f'Cargando {slider_range[1]} páginas')
            df_multiplePag, origin_list = getDfFromPageRange(slider_range[0],slider_range[1], filter, filterValue)
            if df_multiplePag.shape[0] > 0:
                st.success(f"Se han encontrado {df_multiplePag.shape[0]} equipos")
            else:
                st.error(f"No se han encontrado equipos")
            print(df_multiplePag.shape[0])
            #df_multiplePag.head(10)
            st.dataframe(df_multiplePag)
            df_origin = pd.DataFrame(origin_list)
            st.sidebar.info('La información fue obtenida desde:')
            st.sidebar.dataframe(df_origin,hide_index=True,use_container_width=False)
            my_bar.empty()

#Opciones para revisar o vaciar cache
if st.sidebar.button("Revisar Cache"):
    reviewDeleteCacheFolder(False)
if st.sidebar.button("Resetear Cache"):
    reviewDeleteCacheFolder(True)
