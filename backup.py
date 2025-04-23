from datetime import datetime
import streamlit as st
import pandas as pd
from RetoExtraUtils import getResults, sortResults, getBooksCasaLibro, getBooksLibCentral, getBooksIberLibro, add_increment_column 

st.set_page_config(
    page_title="Price Comparer",
    page_icon=":book:",
    layout="wide"
    #layout="wide",
)

st.title("PC2 Reto Extra")
st.header("Daniel Herraiz")

def drawDfTable(inputDf,dfkey):

    st.data_editor(
        inputDf,
        use_container_width=True,
        column_order=['Título','Autor','Detalle','Precio base','Precio final','Incremento %','Cubierta','Enlace'],
        column_config={
            "Cubierta": st.column_config.ImageColumn(
                "Cubierta", 
                width="small",
                help="Doble click para ampliar"
            ),
            "Enlace": st.column_config.LinkColumn(
                "Enlace", 
                display_text=r"https://www.(.*?)\.com"
            ),
            
        }, 
        key=dfkey
        # hide_index=True
    )

def showResults(query, bookLimit):

    if query.strip():
        with st.spinner("Buscando libros..."):
            try:
                #Function list for each store
                fetchFuncs = [getBooksCasaLibro, getBooksLibCentral, getBooksIberLibro]
                dfs = [getResults(f, query, bookLimit) for f in fetchFuncs]
                if not dfs:
                    st.warning("No results found.")
                else:

                    # Draw reduced table with first result from each store
                    reducedBookDf = pd.concat([df.iloc[[0]] for df in dfs if not df.empty], ignore_index=True)
                    reducedBookDf = sortResults(reducedBookDf)
                    reducedBookDf, minprice = add_increment_column(reducedBookDf, -1)
                    st.markdown("#### 📘 Los resultados más baratos de cada tienda:")
                    drawDfTable(reducedBookDf.sort_values(by='Precio final', ignore_index=True), 'Reduced')
                    
                    # Show summary
                    st.markdown("*Resumen de resultados por tienda:*")
                    for df in dfs:
                        
                        if not df.empty:
                            store_name = df['Tienda'].iloc[0]
                            st.write(f"  - {store_name}: {len(df)} resultados")

                    #If more than 1 result in a store, include the rest
                    if any(df.shape[0] > 1 for df in dfs) and bookLimit > 1:
                        # Draw expanded table with the rest (up to bookLimit)
                        expandedDfs = [df.iloc[1:bookLimit] for df in dfs if df.shape[0] > 1]
                        if expandedDfs:
                            st.markdown("#### 📚 Resultados adicionales por tienda:")
                            bookDf, minprice = add_increment_column(pd.concat(expandedDfs, ignore_index=True).sort_values(by='Precio final', ignore_index=True), minprice)
                            drawDfTable(bookDf, 'Expanded')
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a book title or ISBN.")

col1, col2 = st.columns(2)
with col1:
    query = st.text_input("Introducir ISBN, título, genero, autor:", "")
    placeholderButton = st.empty()
    
with col2:
    bookLimit = st.number_input("Introducir máximo de libros por tienda (max 20)", min_value=1, max_value=20)

if placeholderButton.button("🔍 Buscar"):
    # Get the current time
    current_time = datetime.now().time()
    print("Current Time:", current_time)

    showResults(query, bookLimit)
    placeholderexception = st.empty()

