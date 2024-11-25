#==================================================================================================================================
# IMPORTAR BIBLIOTECAS
#==================================================================================================================================
import streamlit as st
import pandas as pd
import base64
import fpdf
from fpdf import FPDF
import requests


#==================================================================================================================================
# CONFIGURACIÓN DE LA PÁGINA
#==================================================================================================================================
st.set_page_config(layout="wide", page_icon='Logo_pagina.png', page_title="Cardiogene")

# Asegúrate de que la imagen esté en la ruta correcta
import streamlit as st

col1, col2 = st.columns([1, 2])

with col1:
    st.image("app/Logo_pagina.png", width=300)

with col2:
    st.markdown("""
    <h1 style="font-family: Cambria; color: #4A007E;">Plataforma Cardiogene</h1>
    <p style="font-family: Cambria; font-size: 18px; color: #6A0DAD;">Exploración farmacogenómica para un tratamiento personalizado</p>
    """, unsafe_allow_html=True)


# Encabezado estilizado
#st.markdown("""
#<div style='text-align: center;'>
    #<h1 style='font-family: Cambria; color: #4A007E;'>Plataforma Cardiogene</h1>
    #<p style='font-family: Cambria; font-size: 18px; color: #6A0DAD;'>Exploración farmacogenómica para un tratamiento personalizado</p>
#</div>
#""", unsafe_allow_html=True)

# Layout de columnas
left, right = st.columns([1, 1], gap="large")

#==================================================================================================================================
# COLUMNA IZQUIERDA: DATOS IDENTIFICATIVOS DEL PACIENTE
#==================================================================================================================================
with left:
    st.markdown("<h3 style='font-family: Cambria; color: #4A007E;'>Datos Identificativos del Paciente</h3>", unsafe_allow_html=True)
    nombre = st.text_input(label="Nombre", placeholder="Nombre")
    apellidos = st.text_input(label="Apellidos", placeholder="Introduzca los apellidos separados por un espacio")
    nhi = st.text_input(label="Nº Historia Clínica", placeholder="Nº Historia Clínica")
    sexo = st.selectbox("Sexo", ['-', 'Hombre', 'Mujer', 'Otro'])
    fecha_n = st.text_input(label="Fecha de nacimiento", placeholder="(dd/mm/yyyy)")

#==================================================================================================================================
# COLUMNA DERECHA: DATOS PATOLÓGICOS
#==================================================================================================================================
with right:
    st.markdown("<h3 style='font-family: Cambria; color: #4A007E;'>Datos Patológicos</h3>", unsafe_allow_html=True)
    enfermedad = st.text_input(label="Enfermedad Actual", placeholder="Escriba la principal patología del paciente")
    otras_e = st.text_input(label="Otras Patologías", placeholder="Introduzca las patologías separadas por comas")
    tratamiento = st.text_input(label="Tratamiento", placeholder="Introduzca los fármacos separados por comas")
    farmacos = [i.strip().lower() for i in tratamiento.split(',')]
    
#==================================================================================================================================
#PARTE INFERIOR
#==================================================================================================================================

#DEFINICIÓN DE FUNCIONES
#_________________________________________________________________________________________________________________________________

def buscarAlelosGen(gen):
    import json
    import requests
    listaAlelos=[]
    url="https://api.cpicpgx.org/v1/allele?genesymbol=eq."+gen
    response = requests.get(url)
    json_obtenido = response.json()
    datos=json_obtenido
    for i in range(len(datos)):
        alelo=datos[i]["name"]
        listaAlelos.append(alelo)
    setAlelos=set(listaAlelos)
    ListaFiltradaAlelos=(list(setAlelos))
    ListaFiltradaAlelos.sort()
    return ListaFiltradaAlelos

def ID_CPIC_Farmaco(nombreFarmaco):
    import json
    import requests
    url="https://api.cpicpgx.org/v1/drug?name=eq."+nombreFarmaco
    response = requests.get(url)
    json_obtenido = response.json()
    datos=json_obtenido
    if len(datos) != 0:
        ID_Farmaco=datos[0]['drugid']
        return ID_Farmaco
    else:
        return ''

def fenotipoSegunAlelos(gen,alelo1,alelo2):
    import json
    import requests
    listaAlelos=[]
    #url="https://api.cpicpgx.org/v1/diplotype?genesymbol=eq.CYP2C19&diplotype=eq.*17/*17"
    url="https://api.cpicpgx.org/v1/diplotype?genesymbol=eq."+gen+"&diplotype=eq."+alelo1+"/"+alelo2
    response= requests.get(url)
    json_obtenido = response.json()
    datos=json_obtenido
    return datos

def urlGuia(farmaco,ID):
    import json
    import requests
    url = 'https://api.cpicpgx.org/v1/drug?name=eq.'+farmaco+'&select=drugid,name,guideline_for_drug(*)'
    response = requests.get(url)
    json_obtenido = response.json()
    datos = json_obtenido
    for i in datos:
        if i['guideline_for_drug']['id'] == ID:
            return i['guideline_for_drug']['url']
        
def recomendacionClinica(gen,alelo1,alelo2,farmaco):
    lista = []
    fenotipo = fenotipoSegunAlelos(gen, alelo1, alelo2)
    if len(fenotipo) != 0:
        lookupkey = fenotipo[0]['lookupkey']
        ID_Farmaco = ID_CPIC_Farmaco(farmaco)
        import json
        import requests
        url = 'https://api.cpicpgx.org/v1/recommendation?drugid=eq.' + ID_Farmaco + '&lookupkey=cs.{\"' + list(lookupkey.keys())[0] + '\":\"' + list(lookupkey.values())[0] + '\"}'
        response = requests.get(url)
        json_obtenido = response.json()
        datos = json_obtenido
        #print(datos[0])
        if len(datos) != 0:
            lista.append(fenotipo[0]['generesult'])
            lista.append(datos[0]['drugrecommendation'].encode('latin-1', 'ignore').decode('latin-1'))
            lista.append(datos[0]['implications'][gen])
            lista.append(urlGuia(farmaco, datos[0]['guidelineid']))
    return lista

def BuscarFarmacosRelacionadosGen(gen):
    import json
    import requests
    listaFarmacos=[]
    url="https://api.pharmgkb.org/v1/data/clinicalAnnotation?location.genes.symbol="+gen
    response = requests.get(url)
    json_obtenido = response.json()
    datos=json_obtenido
    if datos['status'] == 'success':
        for i in range(len(datos["data"])):
            farmaco=datos["data"][i]["relatedChemicals"][0]["name"]
            listaFarmacos.append(farmaco)
    setFarmacos=set(listaFarmacos)
    ListaFiltradaFarmacos=(list(setFarmacos))
    ListaFiltradaFarmacos.sort()
    return ListaFiltradaFarmacos






#CÓDIGO DE STREAMLIT
#_________________________________________________________________________________________________________________________________

col1, col2, col3, col4, = st.columns([1,1,1,1], gap="large")

with col1:
    gen1 = st.text_input(label="Gen 1", placeholder = "Introduzca el gen")
    lista1 = buscarAlelosGen(gen1)
    alelo1_1 = st.selectbox("Alelo 1",['-']+lista1, key = 11)
    alelo1_2 = st.selectbox("Alelo 2",['-']+lista1, key = 12)
    
with col2:
    gen2 = st.text_input(label="Gen 2", placeholder = "Introduzca el gen")
    lista2 = buscarAlelosGen(gen2)
    alelo2_1 = st.selectbox("Alelo 1",['-']+lista2, key = 21)
    alelo2_2 = st.selectbox("Alelo 2",['-']+lista2, key = 22)

with col3:
    gen3 = st.text_input(label="Gen 3", placeholder = "Introduzca el gen")
    lista3 = buscarAlelosGen(gen3)
    alelo3_1 = st.selectbox("Alelo 1",['-']+lista3, key = 31)
    alelo3_2 = st.selectbox("Alelo 2",['-']+lista3, key = 32)
    
with col4:
    gen4 = st.text_input(label="Gen 4", placeholder = "Introduzca el gen")
    lista4 = buscarAlelosGen(gen4)
    alelo4_1 = st.selectbox("Alelo 1",['-']+lista4, key = 41)
    alelo4_2 = st.selectbox("Alelo 2",['-']+lista4, key = 42)
    

    
genes = [gen1,gen2,gen3,gen4]
alelos1 = [alelo1_1,alelo2_1,alelo3_1,alelo4_1]
alelos2 = [alelo1_2,alelo2_2,alelo3_2,alelo4_2]

#==================================================================================================================================
#OBTENCIÓN DE RESULTADOS
#==================================================================================================================================

recomendaciones = dict()
for i in farmacos:
    recomendaciones[i] = dict()
    for x, y, z in zip(genes, alelos1, alelos2):
        if y != '-' and z != '-':
            recomendaciones[i][x] = recomendacionClinica(x,y,z,i)
            
relaciones = dict()
for x,y,z in zip(genes, alelos1, alelos2):
    if y != '-' and z != '-':
        relaciones[x] = BuscarFarmacosRelacionadosGen(x)
#====================================================================================================================================
#EXPORTAR COMO PDF
#====================================================================================================================================

st.markdown("***")
 
export_as_pdf = st.button("Generar PDF")

report_text = "Hola"

def create_download_link(val, filename):
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download file</a>'

class PDF(FPDF):
    def header(self):
        # Logo
        self.image('app/Logo_pagina.png', 30, 12, 30)
        self.image('app/HUBU.png', 80, 14, 50)
        # Arial bold 15
        self.set_font('Times', 'I', 9)
        # Move to the right
        self.set_y(self.get_y()-9)
        self.set_x(-20)
        # Title
        self.cell(w = 0, h = 0, txt = 'Informe farmacogenético', border = 0, ln = 0,  align = 'R')
        self.ln(3.5)
        self.cell(w = 0, h = 0, txt = 'Unidad de Medicina de Precisión', border = 0, ln = 0,  align = 'R')
        self.ln(3.5)
        self.cell(w = 0, h = 0, txt = 'HUBU', border = 0, ln = 0,  align = 'R')
        # Line break
        self.ln(10)

    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Página ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')


if export_as_pdf:
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.set_margins(left = 20.0, top = 25.0, right = 20.0)
    pdf.add_page()
    pdf.set_font('Times', 'I', 20)
    pdf.cell(40, 10, 'Datos personales', ln = 1)
    
    pdf.set_fill_color(186, 146, 198)  # Fondo morado suave
    pdf.set_draw_color(128, 0, 128)  # Bordes morados oscuros
    
    pdf.multi_cell(w = 170, h = 30, border = 1, fill = True)
    pdf.set_font('Times', '', 12)
    pdf.set_y(pdf.get_y()-25)
    pdf.cell(w = 0, txt = f'Nombre: {nombre}', align = 'L')
    pdf.set_x(-90)
    pdf.cell(w = 0, txt = f'Sexo: {sexo}', align = 'L')
    pdf.ln(9)
    pdf.cell(w = 0, txt = f'Apellidos: {apellidos}', align = 'L')
    pdf.set_x(-90)
    pdf.cell(w = 0, txt = f'Fecha de nacimiento: {fecha_n}', align = 'L')
    pdf.ln(9)
    pdf.cell(w = 0, txt = f'Nº Historia Clínica: {nhi}', align = 'L', ln = 1)
    pdf.ln(9)
    
    pdf.set_font('Times', 'I', 20)
    pdf.cell(40, 10, 'Datos patológicos', ln = 1)
    pdf.set_font('Times', '', 12)
    pdf.multi_cell(w = 170, h = 10, txt = f'Enfermedad actual: {enfermedad}\nOtras patologías: {otras_e}\nTratamiento: {tratamiento}', border = 1, fill = True)
    pdf.ln(3)
    
    pdf.set_font('Times', 'I', 20)
    pdf.cell(40, 10, 'Fenotipo y recomendación de dosis', ln = 1)
    texto = ''
    for i in recomendaciones:
        texto += 'En relación con el fármaco ' + i + ':\n'       
        for x in recomendaciones[i]:
            if len(recomendaciones[i][x]) == 0:
                texto += 'No hay información sobre interacciones con '+ x +' para esos alelos.\n'
            else:
                texto += '- El fenotipo para '+ x +' es '+ recomendaciones[i][x][0] + '. \n- Recomendación clínica: ' + recomendaciones[i][x][1]+' \n- Fuente de información: '+recomendaciones[i][x][2]+' ('+recomendaciones[i][x][3]+').\n'
        texto += '\n'
    pdf.set_font('Times', '', 12)
    pdf.multi_cell(w = 170, h = 6, txt = texto, border = 1, fill = True, align = 'L')
    pdf.ln(3)
    
    pdf.set_font('Times', 'I', 20)
    pdf.cell(40,10,'Interacciones con fármacos',ln=1)
    texto = ''
    for i in relaciones:
        texto += 'Fármacos metabolizados por ' + i + ': ' + str(', '.join(relaciones[i]))+'.\n\n'
    pdf.set_font('Times', '', 12)
    pdf.multi_cell(w = 170, h = 6, txt = texto, border = 1, fill = True, align = 'L')
        
    
    html = create_download_link(pdf.output(dest="S").encode('latin-1'), f"Informe paciente {nhi}")

    st.markdown(html, unsafe_allow_html=True)
    
#==================================================================================================================================
#MOSTRAR RESULTADOS
#==================================================================================================================================   
texto = '<center><p style="font-family:Cambria; font-size: 35px;">Informe Final</p></center>'
st.write(texto,unsafe_allow_html = True)
#--------------------------------------------------------------------------------------------------------------------------
texto = '<i><p style="font-family:Cambria; font-size: 22px;"><u>Fenotipo y recomendación de dosis</u></p></i>'
st.write(texto,unsafe_allow_html = True)

for i in recomendaciones:
    texto = '<p style="text-indent: 30px; font-family:Cambria; font-size: 18px;">En relación con el fármaco <b>'+i+'</b>:</p>'
    st.write(texto,unsafe_allow_html = True)          
    for x in recomendaciones[i]:
        if len(recomendaciones[i][x]) == 0:
            texto = '<p style="text-indent: 50px; font-family:Cambria; font-size: 15px;">No hay información sobre interacciones con <b>'+x+'</b> para esos alelos.</p>'
            st.write(texto,unsafe_allow_html = True)
        else:
            
            texto = '<p style="text-indent: 50px; font-family:Cambria; font-size: 15px;">El fenotipo para <b>'+x+'</b> es '+recomendaciones[i][x][0]+'.<br><span style="display:block; text-indent: 50px;">Recomendación clínica: '+recomendaciones[i][x][1]+'.</span><br><span style="display:block; text-indent: 50px;">Fuente de información: <a href="'+recomendaciones[i][x][3]+'" target= "_blank">'+recomendaciones[i][x][2]+'</a></span></p>'

            st.write(texto,unsafe_allow_html = True)
#--------------------------------------------------------------------------------------------------------------------------   
texto = '<i><p style="font-family:Cambria; font-size: 22px;"><u>Interacciones con otros fármacos</u></p></i>'
st.write(texto,unsafe_allow_html = True)

for i in relaciones:
    texto = '<p style="text-indent: 30px; font-family:Cambria; font-size: 15px;">Fármacos metabolizados por <b>'+i+'</b>: '+str(', '.join(relaciones[i]))+'.'+'</p>'
    st.write(texto,unsafe_allow_html = True)


st.markdown("***")
st.markdown("<center><h3>¡Gracias por usar Cardiogene!</h3></center>", unsafe_allow_html=True)
