from collections import defaultdict
import pickle
import random,math,threading
import struct
import tempfile
from flask import Flask, render_template, request, redirect, url_for,g, make_response, flash, session
from models.models import EvPDF, Lista, Correccion
from models.Usuario import Usuario
from models.DatabaseManager import DatabaseManager
import subprocess, os, json, io
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from flask import send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from flask_session import Session
from flask_socketio import SocketIO, emit
import pandas as pd
from uuid import uuid4

app=Flask(__name__)
socketio = SocketIO(app) #Para actualizar todas las páginas de los clientes conectados
app.secret_key = 'EtsistUPM2024'
# Inicializar la base de datos al iniciar la aplicación
db_manager = DatabaseManager()
db_manager.create_tables()  # Crea las tablas si no existen
login_manager_app=LoginManager(app)
# Configurar Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'  # También puedes usar 'redis' o 'sqlalchemy'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_FILE_DIR'] = tempfile.gettempdir()  # Almacena sesiones temporalmente
Session(app)
i=0
lock = threading.Lock()

#Función para obtener los datos del usuario logeado
@login_manager_app.user_loader
def load(id):
    return db_manager.obtener_usuario_por_id(id)
# Contexto de conexión para cada solicitud
@app.before_request
def before_request():
    g.db_manager = DatabaseManager()  # Nueva conexión para cada solicitud

@app.teardown_request
def teardown_request(exception):
    db_manager = g.get('db_manager')
    if db_manager is not None:
        db_manager.close()  # Cierra la conexión al final de cada solicitud

@app.before_request
def verificar_session_token():
    if 'user_id' in session:
        usuario = db_manager.obtener_usuario_por_id(session['user_id'])
        if not usuario or usuario.session_token != session.get('session_token'):
            logout_user()  # Cierra la sesión si los tokens no coinciden
            session.clear()  # Limpia la sesión
            return redirect(url_for('login'))

@app.route('/')

def inicio():
    return redirect(url_for('login'))

@app.route('/principal')
@login_required
def principal():
    return render_template('principal.html')

@app.route('/correcciones')
@login_required
def mostrarCorrecciones():
    
    with lock:
        correcciones=g.db_manager.cargar_correcciones()
    
    return render_template('correcciones.html', correcciones=correcciones)

@app.route('/resultados')
@login_required
def mostrarResultados():
    correcciones=g.db_manager.cargar_correcciones()
    return render_template('resultados.html',correcciones=correcciones)

@app.route('/abrir_correcion')
@login_required
def abrir_correcion():
    lista_titulo = request.args.get('lista_titulo')
    if not lista_titulo.__contains__("Corrector"):
        if not lista_titulo.__contains__(current_user.usuario):
            flash(f'Solo lo puede corregir {lista_titulo}')
            return redirect(url_for('mostrarCorrecciones'))
    correccion_nombre = request.args.getlist('grupo_nombre')  # Esto asume que envías múltiples textos
    correccion_nombre=correccion_nombre[0]
    print("////////////////////////",correccion_nombre)
    lista_evpdf=[]
    with lock:
        correccion=g.db_manager.recuperar_correccion(correccion_nombre)
    listas = correccion.listas.copy()  # Crear una copia de la lista original para evitar modificarla mientras iteras
    lista_seleccionada=0
    for l in listas:
        if l.titulo == lista_titulo:
            # Evitar modificar 'listas' mientras iteras sobre ella, mejor hacerlo después
            l.evaluado = True  # Marca como evaluado sin alterar 'listas'
            l.corrector=current_user.usuario
            lista_seleccionada=l
            # Si necesitas hacer alguna modificación adicional en 'listas', hazlo aquí
            # Si se necesita eliminar este elemento de 'listas', mejor hazlo después del ciclo

            # Añadir los textos de 'l' a 'lista_evpdf'
            print(l.textos)  # Ver lo que se imprime para asegurarte de que no hay duplicados
            for e in l.textos:
                print(e.namePdf)
                lista_evpdf.append(e)
                
    correccion.listas = []  # Solo después de iterar, actualiza la lista completa
    correccion.listas=listas
    with lock:
        g.db_manager.actualizar_correccion(correccion)
        socketio.emit('actualizar_pagina') #mensaje que capturan todos los clientes y actualizan la página
    # Obtener el directorio base
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    
   # Crear una lista de diccionarios de EvPDF
    evpdf_data = []
    for ev_pdf in lista_evpdf:  # Supón que lista_evpdf es tu lista de objetos EvPDF
        evpdf_data.append({
            'namePdf': ev_pdf.namePdf,
            'texto': ev_pdf.texto,
            'nota': ev_pdf.nota
        })
    temp_file_path =os.path.join(basedir, 'app', 'tmp', f'temp_data_{current_user.usuario}.json')
    # Guardar estos datos en un archivo temporal
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        json.dump(evpdf_data, f)
    
    
    resutados_path=os.path.join(basedir,'tmp', f'resultados_{current_user.usuario}.json')
    # Construir la ruta al script
    script_path = os.path.join(basedir, 'comparaciones_profesor.py')

    # Comando para ejecutar el 
    command = ['python', script_path, temp_file_path, resutados_path]
    
    process=subprocess.Popen(command)

    process.wait()
    # Espera a que el archivo de resultados se cree y se llene
    # Puedes implementar un bucle de espera o una verificación de estado
    while not os.path.exists(resutados_path):
        pass  # Espera a que el archivo exista

    # Lee la lista ordenada desde el archivo
    with open(resutados_path, 'r') as f:
        resultados = json.load(f)
    
    os.remove(resutados_path)
    #Si la ventana de corrección se cierra sin terminar de corregir, se maneja. Se vuelve a poner la lista apta para corregir.
    if "Interrumpido" in resultados:
        with lock:
            correccion=g.db_manager.recuperar_correccion(correccion_nombre)
            listas = correccion.listas.copy()  # Crear una copia de la lista original para evitar modificarla mientras iteras
            for l in listas:
                if l.titulo == lista_titulo:
                    # Evitar modificar 'listas' mientras iteras sobre ella, mejor hacerlo después
                    l.evaluado = False  # Marca como evaluado sin alterar 'listas'
                    l.corrector=current_user.usuario
                    lista_seleccionada=l
                    # Si necesitas hacer alguna modificación adicional en 'listas', hazlo aquí
                    # Si se necesita eliminar este elemento de 'listas', mejor hazlo después del ciclo

                    # Añadir los textos de 'l' a 'lista_evpdf'
                    print(l.textos)  # Ver lo que se imprime para asegurarte de que no hay duplicados
                    for e in l.textos:
                        print(e.namePdf)
                        lista_evpdf.append(e)            
            correccion.listas = []  # Solo después de iterar, actualiza la lista completa
            correccion.listas=listas
            g.db_manager.actualizar_correccion(correccion)
        socketio.emit('actualizar_pagina') #mensaje que capturan todos los clientes y actualizan la página
        return redirect(url_for('mostrarCorrecciones'))  # Redirige de vuelta a la página principal
        
    ################################################    
    # Procesar los objetos EvPDF (los textos vienen como una lista de diccionarios)
    with lock:
        evpdf_objects = []

        for data in resultados:
            # Crear un objeto EvPDF por cada diccionario
            evpdf = EvPDF(namePdf=data['namePdf'], texto=data['texto'], nota=data['nota'])
            evpdf_objects.append(evpdf)
        
        correccion=g.db_manager.recuperar_correccion(correccion_nombre)
        listas = correccion.listas.copy()  # Crear una copia de la lista original para evitar modificarla mientras iteras
        for l in listas:
            if l.titulo == lista_titulo:
                l.textos=[]
                l.textos=evpdf_objects

        correccion.listas = []  # Solo después de iterar, actualiza la lista completa
        correccion.listas=listas
        print(correccion.evaluado())
        g.db_manager.actualizar_correccion(correccion)
        
        
        socketio.emit('actualizar_pagina') #mensaje que capturan todos los clientes y actualizan la página
        return redirect(url_for('mostrarCorrecciones'))  # Redirige de vuelta a la página principal

@app.route('/abrir_cuestionario')
@login_required
def abrir_cuestionario():
    print("He entrado al cuestionario")
    lista_tuplas_usuarios=[]
    nombres_tutores=[]
    with lock:
        lista_tuplas_usuarios=db_manager.obtener_nombres_todos_tutores()
        nombres_tutores = [resultado[0] for resultado in lista_tuplas_usuarios]

    
    basedir = os.path.abspath(os.path.dirname(__file__))
    temp_file_path = os.path.join(basedir,'tmp','temp_data_cuestionario_{current_user.usuario}.json')
    
    # Guardar estos datos en un archivo temporal
    with open(temp_file_path, 'w', encoding='utf-8') as f:
        json.dump(nombres_tutores, f)
    
    # Obtener el directorio base
    
    
    # Construir la ruta al script
    script_path = os.path.join(basedir, 'cuestionario.py')
    # Comando para ejecutar el script
    resultados_path = os.path.join(basedir,'tmp', f'resultados_cuestionario_{current_user.usuario}.json')
    command = ['python', script_path, temp_file_path, resultados_path]  # Cambia esto a la ruta de tu script
    
    process=subprocess.Popen(command)

    process.wait()
    
    # Espera a que el archivo de resultados se cree y se llene
    # Puedes implementar un bucle de espera o una verificación de estado
    while not os.path.exists(resultados_path):
        pass  # Espera a que el archivo exista

    with open(resultados_path, "r", encoding="utf-8") as f:
        diccionario_formulario = json.load(f)

    # Elimina el archivo para evitar confusiones en futuras llamadas
    os.remove(resultados_path)

    #Primero vemos si se ha cerrado la ventana sin darle a aceptar. De esta forma no se rompe el programa:
    if "Interrumpido" in diccionario_formulario:
        flash("Se ha cerrado el formulario y no se añadirá ninguna corrección")
        return redirect(url_for('mostrarCorrecciones'))
    #Tratamos los datos recibidos en el formulario
    num_corr=0
    lista_correctores=[]
    nombre_correccion=diccionario_formulario["NombreCorreccion"]
    del diccionario_formulario["NombreCorreccion"]
    
    if "NumeroCorrectores" in diccionario_formulario:
        num_corr=diccionario_formulario["NumeroCorrectores"]
        del diccionario_formulario["NumeroCorrectores"]
    if "CorrectoresSeleccionados" in diccionario_formulario:
        lista_correctores=diccionario_formulario["CorrectoresSeleccionados"]
        del diccionario_formulario["CorrectoresSeleccionados"]
    
    print(lista_correctores)
    elementos=[]
    for nombre_evpdf, texto in diccionario_formulario.items():
        elementos.append(EvPDF(nombre_evpdf,texto))
    
    if num_corr>0:
        for i in range(0,num_corr):
            lista_correctores.append(f'Corrector {i+1}')
    
    dic_listas=distribute_reviews_uniform(elementos,lista_correctores)
    lista_listas=[]
    for nombre_lista,listaPdf in dic_listas.items():
        l=Lista(nombre_lista,listaPdf)
        lista_listas.append(l)
    
    print(lista_listas)
    correccion=Correccion(nombre_correccion)
    correccion.agregar_lista(lista_listas)
    
    with lock:
        g.db_manager.guardar_correccion(correccion)
        socketio.emit('actualizar_pagina') #Mensaje que capturan los clientes y actualizan sus respectivas páginas
    
    return redirect(url_for('mostrarCorrecciones'))

def distribute_reviews_uniform(elements, lista_correctores):
    num_correctors = len(lista_correctores)
    # Calculamos cuántas veces como mínimo tiene que corregirse cada elemento
    num_min_correcciones = (num_correctors // 2) + 1 if num_correctors % 2 == 0 else math.ceil(num_correctors / 2)

    # Creamos una lista auxiliar donde los elementos se repiten `num_min_correcciones` veces
    elementos_repetidos = []
    for _ in range(num_min_correcciones):
        elementos_repetidos += elements

    # Creamos un diccionario para cada corrector
    diccionario = {lista_correctores[i]: [] for i in range(num_correctors)}

    lista_keys = list(diccionario.keys())
    i = 0

    # Distribuir los elementos de manera uniforme entre los correctores
    while len(elementos_repetidos) > 0:
        if i > len(lista_keys) - 1:
            i = 0  # Volver al primer corrector si llegamos al último
        
        corrector = lista_keys[i]
        lista = diccionario[corrector]
        contains = False
        intentos = 0  # Contador de intentos para evitar bucles infinitos

        while not contains:
            if intentos > len(elementos_repetidos):  # Si todos los elementos ya están en la lista, salir
                print(f"No se pueden asignar más elementos únicos al {corrector}.")
                break
            
            # Generar un índice aleatorio
            numero_aleatorio = random.randint(0, len(elementos_repetidos) - 1)
            elemento = elementos_repetidos[numero_aleatorio]
            
            if elemento not in lista:
                lista.append(elemento)  # Añadir el elemento a la lista del corrector
                elementos_repetidos.pop(numero_aleatorio)  # Eliminar el elemento de la lista repetida
                diccionario[corrector] = lista  # Actualizar el diccionario
                contains = True  # Salir del bucle
            else:
                intentos += 1  # Incrementar intentos si el elemento ya estaba en la lista
        
        i += 1  # Pasar al siguiente corrector

    # Encontrar la longitud máxima de las listas
    max_len = max(len(v) for v in diccionario.values())

    # Añadir elementos aleatorios hasta que todas las listas tengan la misma longitud
    all_elements = set(elements)  # Usamos un set para eliminar duplicados de los elementos
    for corrector, lista in diccionario.items():
        while len(lista) < max_len:
            # Seleccionar un elemento aleatorio que no esté ya en la lista
            available_elements = list(all_elements - set(lista))  # Elementos no asignados aún
            if available_elements:
                elemento_aleatorio = random.choice(available_elements)
                lista.append(elemento_aleatorio)  # Añadir el elemento aleatorio
            else:
                break  # Si no hay más elementos disponibles, salir

    return diccionario


@app.route('/descargar_informe')
@login_required
def descargar_informe():
    correccion_nombre = request.args.get('grupo_nombre')  # Obtén el nombre de la corrección
    tipo = request.args.get('tipo')
    if not correccion_nombre:
        return redirect(url_for('mostrarResultados'))  # Si no se especifica, redirige

    correccion = g.db_manager.recuperar_correccion(correccion_nombre)
    listas = correccion.listas.copy()
    lista_todos_evpdf = []
    for lista in listas:
        lista_todos_evpdf += lista.textos

    nota_max =len(listas[0].textos)
    diccionario_ordenado = combinar_evaluaciones(lista_todos_evpdf, nota_max)
    print(tipo)
    if tipo == 'pdf':
        # Crear un buffer de memoria para el PDF
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        
        width, height = letter  # Obtén las dimensiones de la página
        # Configuración de la página
        pdf.setFont("Helvetica-Bold", 20)  # Establece la fuente en negrita y un tamaño de 14

        # Título centrado y en negrita
        titulo = f"Informe de la corrección: {correccion.nombre}"
        pdf.drawCentredString(width / 2, 730, titulo)  # Texto centrado en la posición x = ancho/2
        # Agregar contenido al PDF
        pdf.setFont("Helvetica-Bold", 13)  
        pdf.drawString(50, 700, f"Ranking final tras la combinación de los rankings de cada corrector:")

        pdf.setFont("Helvetica", 12) 
        i = 0
        y = 680  # Coordenada vertical para el texto

        for nombre_pdf, (porcentaje, contador) in diccionario_ordenado:
             # Verificar si queda espacio en la página
            if y < 50:
                pdf.showPage()  # Añade una nueva página si no hay espacio suficiente
                y = 750  # Reinicia la coordenada vertical
                
            texto = f"{i + 1}-{nombre_pdf}: {porcentaje:.2f}% Ha sido corregido por {contador} correctores"
            
            # Calcular el ancho del texto
            texto_ancho = pdfmetrics.stringWidth(texto, "Helvetica", 12)  # Usa la fuente y tamaño actuales
            x_centrado = (width - texto_ancho) / 2  # Centra el texto basado en el ancho de la página

            # Dibujar el texto centrado
            pdf.drawString(x_centrado, y, texto)
            y -= 20  # Espacio entre entradas
            i += 1

            # Verificar si queda espacio en la página
            if y < 50:
                pdf.showPage()  # Añade una nueva página si no hay espacio suficiente
                y = 750  # Reinicia la coordenada vertical

        # Añadir contenido adicional
        pdf.setFont("Helvetica-Bold", 13)
        y-=20
        pdf.drawString(50, y, "Ranking de cada corrector:")
        pdf.setFont("Helvetica", 12) 
        y -= 20
        i=0
        for lista in correccion.listas:
            pdf.drawString(70, y, f"El ranking de {lista.corrector} es: ")
            y -= 20
            for evpdf in lista.textos:
                # Verificar si queda espacio
                if y < 100:
                    pdf.showPage()
                    y = 750
                pdf.drawString(140, y, f"{i+1}- {evpdf.namePdf}")
                i+=1
                y -= 20
            y -= 10  # Espacio entre listas
            i=0
            # Verificar si queda espacio
            if y < 100:
                pdf.showPage()
                y = 750

        # Resumen adicional
        total_pdfs = len(diccionario_ordenado)
        pdf.drawString(120, y, f"Total de PDFs evaluados: {total_pdfs}")
        y -= 20

        # Finalizar y guardar el PDF
        pdf.save()

        # Configurar la respuesta como un archivo descargable
        buffer.seek(0)
        response = send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{correccion_nombre}_informe.pdf"
        )
        response.call_on_close(lambda: redirect(url_for('mostrarResultados')))  # Llamar la redirección después de que se haya enviado el archivo
        return response
    else:
        #Clasificamos los datos que queremos añadir al excel para la hoja principal
        lista_keys=[]
        porcentajes=[]
        num_correctores=[]
        for diccionario in diccionario_ordenado:
            key=diccionario[0]
            tupla=diccionario[1]
            porcentaje=tupla[0]
            correctores=tupla[1]
            lista_keys.append(key)
            porcentajes.append(porcentaje)
            num_correctores.append(correctores)       
        #Datos de la hoja principal
        data = {
            'Nombre Archivo': lista_keys,
            'Porcentaje de conformidad': porcentajes,
            'Número de veces corrgido': num_correctores
        }
        
        #Sacamos la información para la segunda hoja. Se dividirá en dos partes. Columna 1:  Nombre del corrector. Resto de columnas Ranking
        nombres_correctores=[]
        #Como el numero de columnas será variable, sacamos cuantas columnas tendrá la parte de 
        tamano_max_listas=0
        for lista in listas:
            nombres_correctores.append(lista.corrector)
            if len(lista.textos) > tamano_max_listas:
                tamano_max_listas = len(lista.textos)
        #Inicializamos el diccionario y le vamos añadiendo los trabajos a cada posición
        diccionario_rankings={}
        for i in range(1,tamano_max_listas+1):
            diccionario_rankings[i]=[]
        for lista in listas:
            for i in range(1,tamano_max_listas+1):
                if i <= len(lista.textos):
                    texto_posicion=lista.textos[i-1].namePdf
                    l=diccionario_rankings[i]
                    l.append(texto_posicion)
                    diccionario_rankings[i]=l
                else:
                    l=diccionario_rankings[i]
                    l.append("-")
                    diccionario_rankings[i]=l
        diccionario_por_corrector={
            "Corrector": nombres_correctores
        }
        diccionario_por_corrector.update(diccionario_rankings)
        
            

        # Crear un archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame(data).to_excel(writer, index=False, sheet_name='Informe General')
            pd.DataFrame(diccionario_por_corrector).to_excel(writer, index=False, sheet_name='Informe por corrector')
                
        output.seek(0)
        response = send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'{correccion_nombre}_informe.xlsx'
        )
        response.call_on_close(lambda: redirect(url_for('mostrarResultados')))  # Llamar la redirección después de que se haya enviado el archivo
        return response

def combinar_evaluaciones(evaluaciones,nota_max):
    evaluaciones_unicas = {}

    for evaluacion in evaluaciones:
        if evaluacion.namePdf in evaluaciones_unicas:
            # Suma la nota
            evaluaciones_unicas[evaluacion.namePdf]['nota'] += evaluacion.nota
            # Incrementa el contador de veces que ha sido evaluado
            evaluaciones_unicas[evaluacion.namePdf]['contador'] += 1
        else:
            # Inicializa el elemento en el diccionario con su nota y contador en 1
            evaluaciones_unicas[evaluacion.namePdf] = {'nota': evaluacion.nota, 'contador': 1}

    # Llama a la función para calcular porcentajes
    return calcular_porcentajes(evaluaciones_unicas,nota_max)

def calcular_porcentajes(resultados,nota_max):
    
    porcentajes = {}

    # Itera sobre cada resultado y calcula el porcentaje
    for nombre_pdf, datos in resultados.items():
        suma_notas = datos['nota']           # Obtiene la suma de notas
        numero_correctores = datos['contador'] # Obtiene el contador de evaluadores
        if numero_correctores > 0:
            # Calcula el porcentaje
            porcentaje = (suma_notas / (nota_max * numero_correctores)) * 100
            porcentajes[nombre_pdf] = (porcentaje, numero_correctores)  # Guarda porcentaje y contador

    # Ordena los porcentajes de mayor a menor, y en caso de empate, por contador
    porcentajes_ordenados = sorted(porcentajes.items(), key=lambda x: (x[1][0], x[1][1]), reverse=True)

    return porcentajes_ordenados


def eliminar_correcciones():
    correcciones = request.args.get('correcciones')
    correcciones=correcciones.split(",")
    with lock:
        for correccion in correcciones:
            print(correccion)
            db_manager.eliminar_correccion(correccion)
    
    socketio.emit('actualizar_pagina') #Mensaje que capturan los clientes y actualizan sus respectivas páginas

@app.route('/eliminar_correcciones_resultados')
def eliminar_correcciones_resultados():
    eliminar_correcciones()
    return redirect(url_for('mostrarResultados'))

@app.route('/eliminar_correcciones_activas')
def eliminar_correcciones_activas():
    eliminar_correcciones()
    return redirect(url_for('mostrarCorrecciones'))
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':  # Si el método es POST, significa que se han introducido el username y la contraseña.
        user = Usuario(0, request.form['username'], request.form['password'])
        user_bd = db_manager.obtener_usuario(user.usuario)
        if user_bd:
            if user_bd.check_password(user.contraseña):
                # Generar un nuevo session_id único para esta pestaña
                session_id = str(uuid4())  # Usar uuid4 para generar un token único
                user_bd.session_token = session_id  # Asignar el nuevo session_token al usuario

                # Guardar el session_id en la base de datos
                db_manager.actualizar_usuario(user_bd.usuario, nuevo_session=session_id)

                # Guardar el session_id en la sesión de Flask para esta pestaña
                session['session_id'] = session_id  # Establecer el session_token en la cookie de sesión de Flask

                login_user(user_bd)  # Iniciar sesión del usuario
                return redirect(url_for('principal'))
            else:
                flash("Contraseña incorrecta...")
                return render_template('login.html')
        else:
            flash("Usuario no encontrado...")
        return render_template('login.html')
    else:  # Si el método es GET, simplemente se muestra el formulario de login
        return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    user = current_user  # Obtén al usuario actual desde Flask-Login
    db_manager.actualizar_usuario(user.usuario, '')  # Borra el session_token de la base de datos
    logout_user()  # Cierra la sesión del usuario
    session.clear()  # Limpia todas las variables de la sesión
    return redirect(url_for('login'))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method=='POST': #Si el método es Post, significa que se han introduciod el username y la contraseña.
        #print(request.form['username'])#Obtener el username introducido
        #print(request.form['password'])#Obtener el password introducido
        
        user=Usuario(0,request.form['username'],generate_password_hash(request.form['password']))
        user_bd=db_manager.obtener_usuario(user.usuario)
        if user_bd == None:
            if user.usuario.__contains__("@alumnos.upm.es"):
                user.rol="alumno"
            elif user.usuario.__contains__("@upm.es"):
                user.rol="tutor"
            else:
                flash("Hay que añadir el @")
                return render_template('signin.html')
            
            db_manager.agregar_usuario(user)
            return redirect(url_for('login'))
        else:
            flash("Este usuario ya existe")
        return render_template('login.html')
    else: #En el caso que el método sea GET, simplemente está entrando por primera vez y se le quiere mostrar el formulario
        
        return render_template('signin.html')

# if __name__=='__main__':
#     app.run(debug=True)