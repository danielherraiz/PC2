import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import selenium
import re
import time
import scipy
import os
import json


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
        time.sleep(0.05)
        url = f"https://www.scrapethissite.com/pages/forms/?page_num={pageNumber}"
        page = requests.get(url)
        if page.status_code != 200:
            raise Exception(f"Expected 200, got {page.status_code}")
        print (page.status_code)
        upsertCachedFile(pageNumber, page.content)
        return page.content, 'request'
    

#Obtener el dataframe del contenido
def getDfFromPage (pageNumber, withFilter, minGoalDif):
    pageContent, origin = getPageContent(pageNumber)
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
    return pd.DataFrame(teams, columns=columnNames), origin

#Obtener un dataframe de un rango de páginas
def getDfFromPageRange (firstPage, lastPage, withFilter, minGoalDif):
    resultDf = pd.DataFrame()
    #try:
    for i in range(firstPage, lastPage + 1):
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
def deleteCacheFolder():
    folderPath = getCacheFolderPath()
    print(f'a borrar {folderPath}')
    if os.path.exists(folderPath):
        st.write("Cache vaciado: ")
        # First delete all files
        for filename in os.listdir(folderPath):
            file_path = os.path.join(folderPath, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                st.write(f"{filename}")
        # Then delete the folder itself
        os.rmdir(folderPath)
        print('vaciado')
        
    else:
        print('no vaciado')
        st.write("No se ha encontrado nada en cache")

### CODIGO PARA INTERACTUAR CON LA APLICACIÓN EN STREAMLIT33

tab1, tab2, tab3= st.tabs(["Una página", "Rango de páginas (Extra)", "Vaciar Cache"])
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
        fromCache = False
        #cacheData={'From Cache':getCacheDetails(pageNumber)}
        df_onePag, origin = getDfFromPage(pageNumber, filter, filterValue)
        st.write(f"Datos de los equipos ({df_onePag.shape[0]} filas)")
        print(df_onePag.shape)
        #df_onePag.head(10)
        st.dataframe(df_onePag)
        st.write(f'La información fue obtenida desde {origin}')

with tab2:
    st.header("Datos de un rango de páginas")
    slider_range = st.slider("Selecciona un rango de páginas",min_value=1, max_value=24, value=[1,8])
    filter = st.checkbox("¿Aplicar filtro de diferencia de goles? (Extra)",key="filterPageRange")
    filterValue = st.number_input('Introduce un mínimo de diferencia de goles para el filtro',key='filterValuePageRange',disabled=not filter, step=1)
    
    if st.button("Obtener",key='pageRangeButton'):
        df_multiplePag, origin_list = getDfFromPageRange(slider_range[0],slider_range[1], filter, filterValue)
        st.write(f"Datos obtenidos ({df_multiplePag.shape[0]} filas)")
        print(df_multiplePag.shape[0])
        #df_multiplePag.head(10)
        st.dataframe(df_multiplePag)
        df_origin = pd.DataFrame(origin_list)
        st.write('La información fue obtenida desde:')
        st.dataframe(df_origin,hide_index=True,use_container_width=False)

with tab3:
    if st.button("Resetear Cache"):
        deleteCacheFolder()
