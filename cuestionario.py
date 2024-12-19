import json
import os, sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox

import fitz


diccionario_elementos={}
comprobar_seleccion_pdf=False

def crear_formulario():
    # Configuración de la ventana principal
    global ventana,etiqueta_pdf,opcion, frame_general, frame_seleccion, lista, entrada_correctores
    entrada_correctores=None
    lista=None
    ventana = tk.Tk()
    ventana.title("Formulario de Corrección")
    ventana.geometry("400x300")  # Tamaño medio de la ventana
    ventana.protocol("WM_DELETE_WINDOW", on_closing)
    
    opcion = tk.StringVar()
    opcion.set("1")  # Valor inicial
    # Etiqueta y campo de entrada para "Nombre de la corrección"
    global entrada_nombre
    etiqueta_nombre = ttk.Label(ventana, text="Nombre de la tarea:")
    etiqueta_nombre.pack(pady=10)
    entrada_nombre = ttk.Entry(ventana, width=30)
    entrada_nombre.pack()

    # Crear un Frame para los radio buttons
    frame_radios = tk.Frame(ventana)
    frame_radios.pack(pady=10)  # Espaciado alrededor del contenedor

    # Crear Radio Buttons y colocarlos en línea
    radio1 = tk.Radiobutton(frame_radios, text="Seleccionar correctores", variable=opcion, value="1", command=seleccionar_opcion)
    radio1.grid(row=0, column=0, padx=10)

    radio2 = tk.Radiobutton(frame_radios, text="Corrección general", variable=opcion, value="2", command=seleccionar_opcion)
    radio2.grid(row=0, column=1, padx=10)
    
    # Crear un Frame para contener los Frames de las opciones
    main_frame = tk.Frame(ventana)
    main_frame.pack(pady=10)
    
    #Creamos el Frame para la opción de corrección general.
    frame_general = tk.Frame(main_frame)
    etiqueta_correctores = ttk.Label(frame_general, text="Número de correctores:")
    entrada_correctores = ttk.Entry(frame_general, width=30)
    etiqueta_correctores.pack(pady=10)
    entrada_correctores.pack()
    
    #Creamos Frame para la opción se seleccionar correctores
    frame_seleccion = tk.Frame(main_frame)
    # Scrollbar
    scrollbar = ttk.Scrollbar(frame_seleccion, orient="vertical")
    scrollbar.pack(side="right", fill="y")
    
    # Listbox con selección múltiple
    lista = tk.Listbox(frame_seleccion, selectmode="multiple", yscrollcommand=scrollbar.set, height=4)
    for nombre in nombres_tutores:
        lista.insert(tk.END, nombre)
    lista.pack(fill="both", expand=True)
    
    # Configurar scrollbar
    scrollbar.config(command=lista.yview)
    
    
    for frame in (frame_general, frame_seleccion):
        frame.grid(row=0, column=1, padx=10, sticky="nsew")
        
    # Botón para "Añadir PDF"
    boton_pdf = ttk.Button(ventana, text="Añadir PDF", command=seleccionarArchivos)
    boton_pdf.pack(pady=10)

    #Estiqueta para mostrar los pdf seleccionados
    etiqueta_pdf = ttk.Label(ventana, text="")
    # Botón para "Aceptar"
    boton_aceptar = ttk.Button(ventana, text="Aceptar", command=funcion_aceptar)
    boton_aceptar.pack(pady=10)
    
    ventana.mainloop()

def seleccionar_opcion():
    global opcion, frame_general,frame_seleccion
    if opcion.get() == "1":
        frame_seleccion.tkraise()
    elif opcion.get() == "2":
        frame_general.tkraise()
    
def funcion_aceptar():
    global entrada_nombre, entrada_correctores, ventana, lista, diccionario_elementos, resultados_path, comprobar_seleccion_pdf, opcion

    # Obtener el nombre de la corrección
    nombre_correccion = entrada_nombre.get().strip()
    if nombre_correccion != "":
        diccionario_elementos["NombreCorreccion"] = nombre_correccion
    else:
        messagebox.showwarning("Advertencia", "La corrección tiene que tener un nombre.")
        return
    
    #Comprobamos en que modo estamos (si corrección general o específica) y comprobamos que los valores de la opción seleccionada
    #se hayan seleccionado correctamente
    if opcion.get() =="2":
        # Validar número de correctores
        entrada_correctores_valor = entrada_correctores.get().strip()
        if entrada_correctores_valor != "":
            try:
                numero_correctores = int(entrada_correctores_valor)
                diccionario_elementos["NumeroCorrectores"] = numero_correctores
            except ValueError:
                messagebox.showwarning("Advertencia", "Por favor rellene correctamente el valor de Número de Correctores.")
                return
        else:
            messagebox.showwarning("Advertencia", "Por favor rellene correctamente el valor de Número de Correctores.")
            return
    elif opcion.get() == "1":
         # Validar correctores seleccionados si no se especificó el número
        seleccionados = lista.curselection()
        if len(seleccionados) >= 2:
            nombres_seleccionados = [lista.get(i) for i in seleccionados]
            diccionario_elementos["CorrectoresSeleccionados"] = nombres_seleccionados
        else:
            messagebox.showwarning("Advertencia", "Tienes que seleccionar al menos 2 correctores.")
            return

    #Comprobamos si se han seleccionado correctamente los trabajos PDF.
    if comprobar_seleccion_pdf == False:
        messagebox.showwarning("Advertencia", "Tienes que seleccionar los trabajos en formato PDF.")
        return
    
    # Guardar en archivo JSON
    if resultados_path:
        try:
            with open(resultados_path, 'w', encoding='utf-8') as f:
                json.dump(diccionario_elementos, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar los datos: {e}")
            return
    else:
        messagebox.showerror("Error", "No se especificó una ruta para guardar los resultados.")
        return

    ventana.destroy()

def seleccionarArchivos():
    global etiqueta_pdf, comprobar_seleccion_pdf
    # Seleccionar archivos PDF
    files_path = filedialog.askopenfilenames(
        title="Seleccionar archivos PDF",
        filetypes=[("Archivos PDF", "*.pdf"), ("Todos los archivos", "*.*")]
    )
    
    # Comprobar que se seleccionaron al menos dos archivos
    if len(files_path) >= 2:
        #Inicializar los PDF con mi clase MyPDF
        texto_etiqueta=""
        for path in files_path:
            nombre,texto=obtenerTexto(path)
            texto_etiqueta+=f' {nombre}'
            diccionario_elementos[nombre]=texto
        etiqueta_pdf.config(text=f'PDF seleccionados: {texto_etiqueta}')
        etiqueta_pdf.pack()
        comprobar_seleccion_pdf=True
        
        
        
    else:
        messagebox.showwarning("Advertencia", "Por favor, selecciona al menos dos archivos PDF.")

def obtenerTexto(file):
        pdf_document = fitz.open(file)
        nombre_archivo = os.path.basename(file)  # Extraer solo el nombre del archivo
        
        # Acumular el texto de todas las páginas
        texto_completo = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            texto_completo += page.get_text()  # Concatenar el texto de cada página

        return nombre_archivo, texto_completo

#Código que maneja si se pulsa la X para cerrar la ventana
def on_closing():
    global resultados_path
    if messagebox.askokcancel("Salir", "¿Seguro que quieres cerrar el formulario?"):
        diccionario_elementos["Interrumpido"] = True
         # Guardar en archivo JSON
        if resultados_path:
            try:
                with open(resultados_path, 'w', encoding='utf-8') as f:
                    json.dump(diccionario_elementos, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Error al guardar los datos: {e}")
                return
        else:
            messagebox.showerror("Error", "No se especificó una ruta para guardar los resultados.")
            return
        ventana.destroy()
        sys.exit()

# Llamada a la función para crear y mostrar el formulario
def main():
    global resultados_path,nombres_tutores
    nombres_tutores=[]
    if len(sys.argv) > 1:
        # Obtener la ruta del archivo temporal
        temp_file_path = sys.argv[1]
        resultados_path=sys.argv[2]
        # Leer el contenido del archivo temporal
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            nombres_tutores = json.load(f)  # 'textos' es ahora una lista de diccionarios de EvPDF
        
        
        # Después de usar el archivo, lo eliminamos para evitar dejar archivos temporales
        os.remove(temp_file_path)
    crear_formulario()
if __name__ == "__main__":
    
    main()

