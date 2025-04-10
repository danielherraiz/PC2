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

st.title("Hola")
st.header("Título")

#Creo un diccionario con el nº de la página como clave y el contenido como valor
#cachedPageContent = {}
#función para obtener el contenido de la página de cache o via request
def getCacheFilePath():
    pythonFile_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(pythonFile_path, "cacheFile.json")

fromCache = False
def checkCachedFile(pageNumber):
    cachePath = getCacheFilePath()
    if(os.path.isfile(cachePath)):
        with open(cachePath,"r") as cacheFile:
            print("cache read")
            loadedJson = json.load(cacheFile)
            if (pageNumber in loadedJson):  
                #cachedPageContent = cacheFile[pageNumber]
                print("cache info existing")
                fromCache = True
                return BeautifulSoup(cacheFile[str(pageNumber)])
            else:
                return ''
    else:
        return ''



def upsertCachedFile (pageNumber, soup):
    cachePath = getCacheFilePath()
    with open(cachePath, "a") as cacheFile:
        print('en upsert')
        tempDict = {pageNumber:str(soup)}
        #json.dump ({str(pageNumber):str(soup)} , cacheFile)
        json.dump (tempDict , cacheFile)
        # write
        #cacheFile.write(json.dump({pageNumber:soup})


def getPageContent (pageNumber):
    cachedContent = checkCachedFile(pageNumber)
    if cachedContent!= '':
        print(f"pag {pageNumber} obtenida desde cache")
        return cachedContent
    else:  
        # time.sleep(0.05)
        url = f"https://www.scrapethissite.com/pages/forms/?page_num={pageNumber}"
        page = requests.get(url)
        if page.status_code != 200:
            raise Exception(f"Expected 200, got {page.status_code}")
        soup = BeautifulSoup(page.content, "html.parser")
        print (page.status_code)
        upsertCachedFile(pageNumber, soup)
        return soup  
    

#función para obtener el dataframe de una página
def getDfFromPage (pageNumber, withFilter, minGoalDif):
    table = getPageContent(pageNumber).find("table", class_="table")
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
    return pd.DataFrame(teams, columns=columnNames) 

#Función para obtener un dataframe obtenido de un rango de páginas
def getDfFromPageRange (firstPage, lastPage, withFilter, minGoalDif):
    resultDf = pd.DataFrame()
    #try:
    for i in range(firstPage, lastPage + 1):
        pageDf = getDfFromPage(i,withFilter,minGoalDif)
        if resultDf.empty:
            resultDf = pageDf.copy()
        else:
            resultDf = pd.concat([resultDf, pageDf], ignore_index = True)
    #except Exception:
        #print ("Rango inválido de páginas, prueba otros valores")
    return resultDf

#def getCacheDetails(pageNum):
    #return pageNum in cachedPageContent

#def resetCache():
    #cachedPageContent.clear()

tab1, tab2 = st.tabs(["Una página", "Rango de páginas (Extra)"])
filterValue=''

#def resetFilterOnePage():
    #st.session_state.filterValueOnePage = ''
#def resetFilterPageRange():
    #st.session_state.filterValuePageRange = ''

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
        df_onePag = getDfFromPage(pageNumber, filter, filterValue)
        st.write(f"Datos de los equipos ({df_onePag.shape[0]} filas)")
        if fromCache:
            st.write(f"Obenidos desde cache")
        else:
            st.write("Obtenido por request")
        print(df_onePag.shape)
        #df_onePag.head(10)
        st.dataframe(df_onePag)
        #st.write("Cache details")
        #col1, col2 = st.columns(2)
        #with col1:
            #pageIndex = [f"page {pageNumber}"]
            #st.dataframe(pd.DataFrame(cacheData, index = [pageIndex]),use_container_width=False)
       # with col2: 
            #if st.button("Reset Cache",key="resetOnePage"):
              #  resetCache()


with tab2:
    st.header("Datos de un rango de páginas")
    slider_range = st.slider("Selecciona un rango de páginas",min_value=1, max_value=24, value=[1,8])
    filter = st.checkbox("¿Aplicar filtro de diferencia de goles? (Extra)",key="filterPageRange")
    filterValue = st.number_input('Introduce un mínimo de diferencia de goles para el filtro',key='filterValuePageRange',disabled=not filter, step=1)
    
    if st.button("Obtener",key='pageRangeButton'):
        df_multiplePag = getDfFromPageRange(slider_range[0],slider_range[1], filter, filterValue)
        st.write(f"Datos obtenidos ({df_multiplePag.shape[0]} filas)")
        print(df_multiplePag.shape[0])
        #df_multiplePag.head(10)
        st.dataframe(df_multiplePag)
    #if st.button("Reset",key="resetPageRange"):
        #resetFilterPageRange()


    

#else:
    #st.write("¡Adios!")
