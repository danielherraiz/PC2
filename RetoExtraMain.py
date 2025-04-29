from datetime import datetime
import streamlit as st
import pandas as pd
from RetoExtraUtils import getResults, sortResults, add_increment_column 

st.set_page_config(
    page_title="Price Comparer",
    page_icon=":book:",
    layout="wide"
    #layout="wide",
)

st.title("PC2 Reto Extra")
st.header("Comparador de precios para libros")

def drawDfTable(inputDf,dfkey):

    st.data_editor(
        inputDf,
        use_container_width=True,
        column_order=['Título','Autor','Comentarios','Precio base','Precio final','Incremento %','Cubierta','Enlace'],
        column_config={
            "Cubierta": st.column_config.ImageColumn(
                "Cubierta", 
                width="small",
                help="Doble click para ampliar"
            ),
            "Enlace": st.column_config.LinkColumn(
                "Enlace", 
                display_text = r"https://www\.(.*?)\.(com|es)"
            ),
            
        }, 
        key=dfkey
        # hide_index=True
    )

def showResults(query, bookLimit, ebook, itemCondition, storeDic):

    if query.strip():
        with st.spinner("Buscando libros..."):
            try:
                dfs = getResults(query, bookLimit, ebook, itemCondition, storeDic)

                if all(df.empty for df in dfs):
                    print()
                    st.warning("No results found.")
                    return
                else:

                    # Draw reduced table with first result from each store
                    reducedDf = pd.concat([df.iloc[[0]] for df in dfs if not df.empty], ignore_index=True)
                    reducedDf = sortResults(reducedDf)
                    reducedDf, minprice = add_increment_column(reducedDf, -1)
                    st.markdown("#### 📘 Los resultados más baratos de cada tienda:")
                    reducedDf.index = range(1, len(reducedDf) + 1)
                    drawDfTable(reducedDf, 'Reduced')
                    
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
                            bookDf.index = range(1, len(bookDf) + 1)
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
    st.write("\n")
    with st.expander("Opciones de búsqueda:"):
        bookLimit = st.number_input("Introducir máximo de libros por tienda (max 15)", min_value=1, max_value=15)
        ebook = st.checkbox("Descartar e-books y audiolibros", value=True, key='ebook')
        itemCondition = st.checkbox("Descartar 2ª mano", value=True, key='2mano')
        st.write('Seleccionar tiendas:')
        storeDic = {
            'include_casalibro' : st.checkbox('Casa del libro', value = 'True', key='casalibro'),
            'include_libcentral' : st.checkbox('Libreria central', value = 'True', key='libcentral'),
            'include_iberlibro' : st.checkbox('Iber libro', value = 'True', key='iberlibro'),
            'include_amazon' : st.checkbox('Amazon', value = 'True', key='amazon'),
            'include_ebay' : st.checkbox('eBay', value = 'True', key='ebay'),
            'include_corteingles' : st.checkbox('El Corte Inglés', value = 'True', key='corteingles'),
            'include_buscalibre' : st.checkbox('Busca Libre', value = 'True', key='buscalibre')
        }

        
if placeholderButton.button("🔍 Buscar"):
    # Get the current time
    current_time = datetime.now().time()
    print(current_time)
    showResults(query, bookLimit, ebook, itemCondition, storeDic)
    placeholderexception = st.empty()

