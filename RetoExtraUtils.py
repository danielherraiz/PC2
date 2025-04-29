import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys

import traceback
import re

import os

def startDriver():
    # --- SETUP FIREFOX DRIVER ---
    service = Service(executable_path="C:/Repos/Utils/geckodriver.exe")
    options = Options()
    options.add_argument("-private")
    options.headless = True
    driver = webdriver.Firefox(service=service, options=options)
    # options.headless = False  # Set to True if you don't need the browser window
    #hide firefox window
    return driver

## FUNCTIONS TO OBTAIN CONTENT FROM BOOK STORES ##

def getBooksCasaLibro(driver, query, bookLimit, ebook, itemCondition):
    books = []
    bookDf = pd.DataFrame()
    url = "https://www.casadellibro.com"
    driver.get(url)
    driver.maximize_window()
    # This reduces time while allowing some time for finding elements:
    time.sleep(0.3)
    driver.implicitly_wait(1.4)
    acceptCookies = driver.find_element(By.CSS_SELECTOR, 'button[id="onetrust-accept-btn-handler"]')
    acceptCookies.click()
    try:
        search = driver.find_element(By.XPATH, "//input[@id='empathy-search']")
        search.send_keys(query)
    except:
        search = driver.find_element(By.CSS_SELECTOR, "input[data-test='search-input']")
        search.send_keys(query)
        search.send_keys(Keys.ENTER)

    # --- EXPAND SHADOW DOM ROOT ---
    # def expand_shadow_element(element):

    root1 = driver.find_element(By.XPATH, "//div[@class='x-root-container']")
    shadow_root = driver.execute_script("return arguments[0].shadowRoot", root1)
    try:
        # Interact with right side panel ('Ordenar por)
        # Open right side panel 
        rightPanel = shadow_root.find_element(By.CSS_SELECTOR, 'button[data-test="toggle-facets-button"]')
        rightPanel.click()
        # Sort 
        sortButton = shadow_root.find_element(By.CSS_SELECTOR, 'div[data-test="sort"]')
        sortButton.click()
        # Some margin to load all checkboxes
        time.sleep(0.3)
        for checkbox in sortButton.find_elements(By.CSS_SELECTOR, 'button[data-test="sort-picker-button"]'):
            if checkbox.text == 'Precio: De menor a mayor':
                checkbox.click()
        try:
            availability = shadow_root.find_element(By.CSS_SELECTOR, 'div[data-test="availability"]')
            availability.click()
            time.sleep(0.3)
            # Look for "available" checkbox and click it (the checkbox order changes with the query)
            for checkbox in availability.find_elements(By.CSS_SELECTOR, 'button[data-test="filter"]'):
                if re.search(r"disponible", checkbox.text, re.IGNORECASE):
                    checkbox.click()
                    break
        except (NoSuchElementException , TimeoutException) as e:
            print(e.args)
    except: 
        print('casa del libro no se pudo ordenar')
    # Some margin to load all results (if I only rely on implicit, it might only get the first result)
    time.sleep(0.5)
    shadow_root = driver.execute_script("return arguments[0].shadowRoot", root1)
    results = shadow_root.find_elements(By.CSS_SELECTOR, "li.x-base-grid__item")

    i=0
    # Once the results are loaded, I don't need the implicit wait. Some elements might not be found/needed
    driver.implicitly_wait(0)
    for result in results:
        i+=1
        try:
            article = result.find_element(By.CSS_SELECTOR, "article")
            
            # Title
            titles = article.find_elements(By.CSS_SELECTOR, 'h2[data-test="result-title"]')
            title = titles[0].text if titles else "N/A"

            #Author
            author = titles[1].text if len(titles) > 1 else "N/A"

            #Detail
            try:
                detail_el = article.find_elements(By.CSS_SELECTOR, 'span.x-text1.x-text1-sm.x-font-bold.x-text-lead-50')
                detail = detail_el[0].text.strip() if detail_el else "N/A"
            except (NoSuchElementException , TimeoutException) as e:
                print(e.args)
                detail = "N/A"

            # Image
            try:
                img_elem = article.find_element(By.CSS_SELECTOR, 'img[data-test="result-picture-image"]')
                img_url = img_elem.get_attribute("src")
            except (NoSuchElementException , TimeoutException) as e:
                print(e.args)
                img_url = "N/A"

            #Link
            try:
                link_el = article.find_element(By.CSS_SELECTOR, 'a[data-test="result-link"]')
                link = link_el.get_attribute("href")
                print(link)
            except:
                link = "N/A"
                
            # Price (Current)
            try:
                price_elem = article.find_element(By.CSS_SELECTOR, 'div[data-test="result-current-price"]')
                current_price = price_elem.text.strip()
                if not current_price:
                    print('Exception price empty 1')
                    continue
            except (NoSuchElementException , TimeoutException) as e:
                print(e.args)
                print('Exception no price found 1')
                continue

            #Price (original)
            try:
                original_price_elem = article.find_element(By.CSS_SELECTOR, 'div[data-test="result-previous-price"]')
                original_price = original_price_elem.text.strip()
            except (NoSuchElementException , TimeoutException) as e:
                print(e.args)
                original_price = current_price
            # Build list of dictionaries
            books = includeBook(books,title,author,detail,img_url,link,"Casa del libro",original_price,current_price)
            
        except Exception as e:
            print(f"Error al obtener resultados de {url} : {e}")
        #Exit loop if enough results are retrieved
        if len(books) == bookLimit:
            break
    bookDf = pd.DataFrame(books)
    print(f'tienda 1 size: {bookDf.shape[0]}')
    return bookDf

def getBooksLibCentral(driver, query, bookLimit, ebook, itemCondition):
    books = []
    bookDf = pd.DataFrame()
    baseUrl = 'https://www.libreriacentral.com/'
    queryUrl = query.strip().replace(" ","+")
    url = f"{baseUrl}SearchResults.aspx?st={queryUrl}&cId=0&sm=qck&sort=MEMA"
    page = requests.get(url)
    time.sleep(1)
    soup = BeautifulSoup(page.content,"html.parser")
    results = soup.find_all("div",class_="products-preview-list-item")
    i = 0
    for result in results:
        i+=1
        try:
            #In stock? 
            if result.find_all("span", class_='css-sin-stock') or  result.find_all("span", class_='css-consultar'):
                continue 
            # Title
            name_element = result.find(attrs={"itemprop": "name"})
            title = name_element.get_text().strip()

            #Author
            author = result.find("meta", attrs={"itemprop": "author"})['content'].strip()
            detail = 'N/A'

            # Price 
            try:
                price_substrings = result.find("div", class_="precio").find_all("span")
                current_price = price_substrings[0].get_text().strip() +' '+price_substrings[1].get_text().strip()
                if len(price_substrings) > 2:
                    original_price = price_substrings[2].get_text().strip() +' '+price_substrings[1].get_text().strip()
                else:
                    original_price = current_price
            except e:
                #Book discarded if no price
                continue
            # Image
            try:
                img_url = baseUrl + result.find("img", class_='foto')['src']
            except e:
                img_url = "N/A"
            #Link
            try:
                link = result.find("a", attrs={"itemprop": "url"})["href"].strip()
                link = baseUrl + link
            except:
                link = "N/A"
            books = includeBook(books,title,author,detail,img_url,link,"Librería central",original_price,current_price)
            bookDf = pd.DataFrame(books)
            if len(books) == bookLimit:
                break
        except Exception as e:
            print(f"Error al obtener resultados de {baseUrl} : {e}")
    print(f'tienda 2 size: {bookDf.shape[0]}')
    return bookDf

def getBooksIberLibro(driver, query, bookLimit, ebook, itemCondition):
    bookDf = pd.DataFrame()
    books = []
    baseUrl = 'https://www.iberlibro.com/'
    queryUrl = query.strip().replace(" ","%20")
    url = f"{baseUrl}servlet/SearchResults?ch_sort=t&cm_sp=sort-_-SRP-_-Results&cond=new&ds=20&fs=es&kn={queryUrl}&n=100046497&pt=book&rollup=on&sortby=2"
    page = requests.get(url)
    time.sleep(1)
    soup = BeautifulSoup(page.content,"html.parser")
    results = soup.find_all("li",class_="cf result-item",limit = bookLimit)
    i = 0
    for result in results:
        i+=1
        try:
            title = result.find(attrs={"itemprop": "name"})['content'].strip()
            author = result.find("meta", attrs={"itemprop": "author"})['content'].strip()
            detail = result.find("meta", attrs={"itemprop": "about"})['content']
            detail = re.split(r'Condic.*', detail)[0].strip()
            try:
                current_price = result.find("p", class_="item-price").text
                original_price = current_price
            except Exception as e:
                #Book discarded if no price
                continue
            # Image
            try:
                img_url = result.find("img", class_='srp-item-image')['src'].strip()
            except Exception as e:
                img_url = "N/A"
            #Link
            try:
                link = result.find("a", attrs={"itemprop": "url"})["href"].strip()
                link = baseUrl + link
            except Exception as e:
                link = "N/A"

            books = includeBook(books,title,author,detail,img_url,link,"Iber Libro",original_price,current_price)
            bookDf = pd.DataFrame(books)
        except Exception as e:
            print(f"Error al obtener resultados de {baseUrl} : {e}")
        if len(books) == bookLimit:
            break
    print(f'tienda 3 size: {bookDf.shape[0]}')
    return bookDf

def getBooksAmazon(driver, query, bookLimit, ebook, itemCondition):
    books = []
    bookDf = pd.DataFrame()
    url = "https://www.amazon.es/"
    driver.get(url)
    driver.implicitly_wait(1)
    #cookies
    try:
        driver.find_element(By.ID, "sp-cc-accept").click()
    except:
        print("no cookies")

    driver.implicitly_wait(0.8)
    #Category button
    try:
        driver.find_element(By.ID, "searchDropdownBox").click()
        #Select books category
        booksCategory = driver.find_element(By.XPATH, "//option[@value='search-alias=stripbooks']")
        booksCategory.click()
        #Find search input and send query
        search = driver.find_element(By.XPATH, "//input[@id='twotabsearchtextbox']")
        search.send_keys(query)
        #Confirm search
        submit = driver.find_element(By.XPATH, "//input[@id='nav-search-submit-button']")
        submit.click()
    except:
        print('opcion 2')
        #Sometimes the category is not shown until a first search (page load is different)
        search0 = driver.find_element(By.ID, "nav-bb-search")
        search0.click()
        search0.send_keys(query)
        search0.send_keys(Keys.ENTER)
        # driver.find_element(By.ID, "nav-bb-button").click()
        driver.find_element(By.ID, "searchDropdownBox").click()
        driver.find_element(By.XPATH, "//option[@value='search-alias=stripbooks']").click()
        driver.find_element(By.XPATH, "//input[@id='nav-search-submit-button']").click()
        
    if(itemCondition):
        for itemCondButton in driver.find_elements(By.ID, "p_n_condition-type/15144009031"):
            itemCondButton.click()
    
    #Check if there are any results. There might me results for other departments and 
    #give false positive, need to check the text message
    for resultMessage in driver.find_elements(By.XPATH, "//div[contains(@data-cel-widget,'search_result')]"):
        if 'No hay resultados para' in resultMessage.text:
            print('no hay resultados')
            return bookDf
    try:
        sortDropDown = driver.find_element(By.CSS_SELECTOR, "span[class='a-dropdown-container']")
        sortDropDown.click()
        sortButton = driver.find_element(By.CSS_SELECTOR, "a[id='s-result-sort-select_1']")
        sortButton.click()
    except:
        print('No se pudo ordenar en amazon')
    time.sleep(0.5)
    results = driver.find_elements(By.CSS_SELECTOR, "div[data-csa-c-type='item']")
    driver.implicitly_wait(0)
    i=0
    for result in results:
        i+=1
        try:
            title = result.find_element(By.CSS_SELECTOR, "h2[class='a-size-medium a-spacing-none a-color-base a-text-normal']").text
            #Authors might come with different class 
            try:
                author = result.find_element(By.CSS_SELECTOR, "a[class='a-size-base a-link-normal s-underline-text s-underline-link-text s-link-style']").text
            except Exception as e:
                try:
                    author = result.find_elements(By.CSS_SELECTOR, "span[class='a-size-base']")[1].text
                except:
                    continue
            try:
                img_url = result.find_element(By.CSS_SELECTOR, "img[class='s-image']").get_attribute("src")
                print(img_url)
            except:
                print('no image')
            #Different prices for different formats. Will be saved as different book results
            # All detail links
            detail_link_List = result.find_elements(By.XPATH, './/a[contains(@class,"a-text-bold")]')
            # All prices
            price_List = result.find_elements(By.XPATH, './/a[@aria-describedby="price-link"]')
            
            for i in range(len(price_List)):
                try:
                    detail = detail_link_List[i].text
                    #Discard ebooks and others (input checkbox)
                    if ("Kindle" in detail or "Audiolibro" in detail or "Pódcast" in detail) and ebook:
                        continue
                    link = detail_link_List[i].get_attribute("href")
                except:
                    detail = "N/A"
                    link = "N/A" 
                price_text = price_List[i].text.replace("\n", ".").replace(",", ".")
                match = re.match(r"(\d+[.]?\d*)", price_text)
                if match:
                    current_price = float(match.group(1))
                try:
                    original_text = price_List[i].find_element(By.XPATH, './/span[@class="a-price a-text-price"]').text
                    match = re.match(r"(\d+[.]?\d*)", original_text.replace(",", "."))
                    if match:
                        original_price = str(match.group(1))
                    else:
                        original_price = str(current_price)
                except:
                    original_price = str(current_price)

                books = includeBook(books,title,author,detail,img_url,link,"Amazon",original_price,current_price)

                if len(books) == bookLimit:
                    break
        except Exception as e:
            print(f"Error procesando un resultado: {e}")
        if len(books) == bookLimit:
            break
            
    bookDf = pd.DataFrame(books)
    # driver.close()
    print(f'tienda 4 size: {bookDf.shape[0]}')
    return bookDf
    
def getBooksEbay(driver, query, bookLimit, ebook, itemCondition):
    books = []
    bookDf = pd.DataFrame()
    baseUrl = 'https://www.ebay.es/'
    queryUrl = query.strip().replace(" ","+")
    itemConditionParam = ''
    if(itemCondition):
        itemConditionParam = "&LH_ItemCondition=1000"
    url = f"{baseUrl}sch/i.html?_nkw={queryUrl}&_sacat=267&_from=R40&_sop=15&rt=nc{itemConditionParam}"

    page = requests.get(url)
    time.sleep(1)
    soup = BeautifulSoup(page.content,"html.parser")
    results = soup.css.select('li[data-marko-key^="0 s0-55-0-9-8-4-4-0-3-0-4"]', limit=bookLimit)
    i = 0
    for result in results:
        i+=1
        print(i)
        try:
            # Title
            name_element = result.find("div", class_="s-item__title")
            title = name_element.get_text().strip()
            print(title)

            if "Libro Electrónico" in title and ebook:
                continue
            #Author
            author = 'N/A'
            print(author)
            detail_element = result.find("div", class_="s-item__subtitle")
            
            
            detail = detail_element.get_text().strip()
            if "|" in detail:
                detail = detail.split("|")[0]

            ##Commented because looking for shipping costs in all stores is way above scope (varies with the total order, location, etc)
            # shipping_element = result.find("span", class_="s-item__shipping s-item__logisticsCost").get_text()
            # print(shipping_element)
            # if "EUR" in shipping_element:
            #     # shipping_element_formatted = shipping_element.replace(",",".").replace(r"[^\d.,]", "", regex=True)
            #     shipping_element_formatted = re.sub(r"[^\d.]", "", shipping_element.replace(",", "."))
            #     detail = detail +'. '+ shipping_element_formatted + '€ envío'
            #     print(detail)
            # Price 
            try:
                price_element = result.find("span", class_="s-item__price")
                current_price = price_element.get_text().strip()
                original_price = current_price
            except:
                #Book discarded if no price
                continue
            print(current_price)
            # Image
            try:
                img_element = result.find("div", class_="s-item__image-wrapper image-treatment")
                img_url = img_element.find('img')["src"]
            except e:
                img_url = "N/A"
            #Link
            try:
                link = result.find("a", class_="s-item__link")["href"]
            except:
                link = "N/A"

            books = includeBook(books,title,author,detail,img_url,link,"eBay",original_price,current_price)

            print(len(books))
            bookDf = pd.DataFrame(books)
            if len(books) == bookLimit:
                break
        except Exception as e:
            print(f"Error al obtener resultados de {baseUrl} : {e.args}")
    print(f'tienda 5 size: {bookDf.shape[0]}')
    return bookDf

def getBooksCorteIngles(driver, query, bookLimit, ebook, itemCondition):
    books = []
    bookDf = pd.DataFrame()
    
    baseUrl = "https://www.elcorteingles.es/"
    queryParam = query.strip().replace(' ', '+')
    url = f"{baseUrl}search-nwx/1/?s={queryParam}&stype=text_box&sorting=priceAsc"
    driver.get(url)
    driver.implicitly_wait(0.6)
    time.sleep(0.6)
    #cookies
    try:
        driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
    except:
        print("no cookies")

    #Categories (if present, not always work if included as url param)
    for categories in driver.find_elements(By.CSS_SELECTOR, "button[class='chip chip--default chip]"):
            if "Libros" in categories.text:
                categories.click()
                break
    time.sleep(0.8)
    results = driver.find_elements(By.CSS_SELECTOR, 'li[class="products_list-item"]')
    driver.implicitly_wait(0.1)
    for result in results:
        try:
            title_element = result.find_element(By.CSS_SELECTOR, 'a[class="product_preview-title"]')
            title, detail = split_title_and_details(title_element.text)
        
            author = result.find_element(By.CSS_SELECTOR, 'p[class="product_preview-brand--text"]').text

            # link = baseUrl + result.find_element(By.CSS_SELECTOR, 'a[class="product_link pointer"]').get_attribute("href")
            link = result.find_element(By.CSS_SELECTOR, 'a[class="product_link pointer"]').get_attribute("data-url")
            
            img_url = result.find_element(By.CSS_SELECTOR, 'img[class="js_preview_image"]').get_attribute("src")

            current_price = result.find_element(By.XPATH, './/span[@class="price-sale" or @class="price-unit--normal"]').text
            original_price = 'N/A'
            try:
                original_price = result.find_element(By.CSS_SELECTOR, 'span[class="price-unit--original"]').text
            except:
                original_price = current_price

            books = includeBook(books,title,author,detail,img_url,link,"El Corte Inglés",original_price,current_price)

            if len(books) == bookLimit:
                break
        except Exception as e:
            print(f"Error procesando un resultado: {e}")
        if len(books) == bookLimit:
            break
            
    bookDf = pd.DataFrame(books)
    print(f'tienda 6 size: {bookDf.shape[0]}')
    return bookDf

def getBooksBuscaLibre(driver, query, bookLimit, ebook, itemCondition):
    books = []
    bookDf = pd.DataFrame()
    
    baseUrl = "https://www.buscalibre.es/"
    queryParam = query.strip().replace(' ', '+')
    itemConditionParam = ''
    if (itemCondition):
        itemConditionParam = '-asc&condition=new'
    url = f"{baseUrl}libros/search/?q={queryParam}&sort=64_price-asc{itemConditionParam}"
    driver.get(url)
    driver.implicitly_wait(1)
    time.sleep(0.6)
    
    #Prueba con un resultado
    try:
        title = driver.find_element(By.CSS_SELECTOR, 'p[class="tituloProducto"]').text
        driver.implicitly_wait(0.1)
        subtitle_element = driver.find_element(By.CSS_SELECTOR, 'p[class="font-weight-light margin-0 font-size-h1"]')
        author = subtitle_element.find_element(By.CSS_SELECTOR, 'a[class="font-color-bl link-underline"]').text
        detail = subtitle_element.text.replace(f"{author} (Autor) · ", "").replace(" · ", ", ").strip()

        link = driver.current_url
        img_url = driver.find_element(By.ID, 'imgPortada').get_attribute('src')
       
        price_element = driver.find_element(By.ID, 'opciones')
        for price_subelement in price_element.find_elements(By.XPATH, 'div[contains(@class, "opcionPrecio")]'):
            if "Libro Usado" in price_subelement.text and itemCondition == False:
                current_price = price_element.find_element(By.CSS_SELECTOR, 'span[class="ped"]').text
                original_price = current_price
                books = includeBook(books,title,author,detail,img_url,link,"Busca Libre",original_price,current_price)
                if len(books) == bookLimit:
                    break
            if "Libro Nuevo" in price_subelement.text:
                current_price = price_element.find_element(By.CSS_SELECTOR, 'span[class="ped"]').text
                original_price = price_element.find_element(By.CSS_SELECTOR, 'span[class="pvp"]').text
                books = includeBook(books,title,author,detail,img_url,link,"Busca Libre",original_price,current_price)
                if len(books) == bookLimit:
                    break

    #Si no se ha encontrado, es un elemento distinto con varios resultados
    except:
        for result in driver.find_elements(By.XPATH, "//div[contains(@class,'box-producto producto')]"):
            try:

                title = result.find_element(By.CSS_SELECTOR, 'h3[class="nombre margin-top-10 text-align-left"]').text
                author = result.find_element(By.CSS_SELECTOR, 'div[class="autor"]').text
                link = result.find_element(By.XPATH, 'a[contains(@href, "https://www.buscalibre.es")]').get_attribute('href')
                try:
                    img_url_parent = result.find_element(By.CSS_SELECTOR, 'div[class="imagen"]')
                    img_url = img_url_parent.find_element(By.CSS_SELECTOR, 'img[class=" lazyloaded"]').get_attribute('src')
                except:
                    img_url = ''
                try:
                    detail = result.find_element(By.CSS_SELECTOR, 'div[class="autor color-dark-gray metas hide-on-hover"]').text
                except:
                    detail = ''
                    
                price_element = result.find_element(By.CSS_SELECTOR, 'div[class="box-precio-v2 row margin-top-10 hide-on-hover"]')
                current_price = price_element.find_element(By.CSS_SELECTOR, 'p[class = "precio-ahora hide-on-hover margin-0 font-size-medium"]').text
                original_price = price_element.find_element(By.CSS_SELECTOR, 'p[class = "precio-antes hide-on-hover margin-0 color-dark-gray font-weight-normal"]').text
                if not original_price:
                    original_price = current_price
                # price_element = result.find_element(By.XPATH, 'div[contains(@class, "box-precios")]')
                # current_price = price_element.find_element(By.XPATH, 'p[contains(@class, "precio-ahora")]').text
                # original_price = price_element.find_element(By.XPATH, 'p[contains(@class, "precio-antes")]').text
               
                books = includeBook(books,title,author,detail,img_url,link,"Busca Libre",original_price,current_price)

            except Exception as e:
                print(f"Error procesando un resultado: {e}")
            if len(books) == bookLimit:
                break
            
    bookDf = pd.DataFrame(books)
    print(f'tienda 7 size: {bookDf.shape[0]}')
    return bookDf

## FUNCTIONS FOR DATA MANIPULATION ##

def add_increment_column(df, min_price):
    try:
        if df.empty:
            df["Incremento %"] = []
            return df
        if(min_price==-1):
            min_price = df["Precio final"].min()
        
        df["Incremento %"] = (df["Precio final"] - min_price).round(2).astype(str) + ' € (' +((df["Precio final"] - min_price) / min_price * 100).round(2).astype(str) + " %)"
        
        # df["Incremento %"] = (
        # (df["Precio final"] - min_price).astype(str) + ' € (' +
        # ((df["Precio final"] - min_price) / min_price * 100).round(2).astype(str) + " %)")
        
        df["Precio base"] = df["Precio base"].str.replace(",", ".").replace(r"[^\d.,]", "", regex=True) + " €"
        df["Precio final"] = df["Precio final"].round(2).astype(str) + " €"
    except Exception as e:
        traceback.print_exc()
    return df, min_price

def sortResults(df):
    #Apply float format so the sorting works properly
    if not df.empty and 'Precio final' in df.columns:
        df["Precio final"] = (
        df["Precio final"]
        .astype(str)
        .str.replace(r"[^\d.,]", "", regex=True)  # Remove currency symbols or other chars
        .str.replace(",", ".")                    # Handle decimal commas 
        .astype(float) 
        )
        print('sorted')
        return df.sort_values(by='Precio final', ignore_index=True)
    else:
        print('no sorted')
        return df

def getResults(query, bookLimit, ebook, itemCondition, storeDic):
    # Receives a dictionary with value True or False for each store, from app input
    # Mapping keys from the dictionary to their corresponding functions:
    store_functions = {
        'include_amazon': getBooksAmazon,
        'include_casalibro': getBooksCasaLibro,
        'include_libcentral': getBooksLibCentral,
        'include_iberlibro': getBooksIberLibro,
        'include_ebay': getBooksEbay,
        'include_corteingles': getBooksCorteIngles,
        'include_buscalibre' : getBooksBuscaLibre
    }

    results = []

    driver = startDriver()

    for key, fetch_func in store_functions.items():
        # Only call if store checkbox is true
        if storeDic.get(key):
            try:
                df = fetch_func(driver, query, bookLimit, ebook, itemCondition)
                df = sortResults(df) 
                results.append(df)
            except Exception as e:
                st.warning(f"Error al obtener resultados de {key.split("_")[1]}: {e}")
    driver.close()
    return results

def split_title_and_details(title):
        
    # Find all text inside parentheses
    parts = re.findall(r"\(([^()]*)\)", title)

    # Keywords to keep as details
    keywords = ["tapa blanda", "tapa dura", "bolsillo"]

    # Keep only parts that contain those keywords
    details = [part for part in parts if any(keyword in part.lower() for keyword in keywords)]

    # Remove those parts from the title
    for part in details:
        title = title.replace(f"({part})", "")

    # Clean extra spaces and parentheses left behind
    title = re.sub(r"\s+", " ", title).strip()  # remove double spaces
    title = title.strip("() ").strip()          # remove extra () or trailing spaces

    # Join details nicely, or return None if empty
    detail_str = ". ".join(details) if details else None

    return title, detail_str

def includeBook (books, title, author, detail, img_url, link, store, original_price, current_price):
    books.append({
        "Título": title,
        "Autor": author,
        "Comentarios": detail,
        "Cubierta": img_url,
        "Enlace": link,
        "Tienda": store,
        "Precio base": original_price,
        "Precio final": current_price
    })
    return books