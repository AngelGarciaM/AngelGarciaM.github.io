import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # Importar PyMuPDF
import os
import sys
import json, glob
from models.models import EvPDF

pdf_seleccionados = []
seleccionado = 0
seleccion_texto = ""
cierre = 0
icancelar = 0
indice = 0
def quicksort(arr):
    global seleccionado, seleccion_texto, indice, cierre, icancelar, boton_buscar

    if len(arr) <= 1:
        return arr

    pivot = arr[0]
    peores = []
    mejores = []

    for item in range(1, len(arr)):
        mostrarArchivos(pivot, arr[item])

        while seleccionado == 0 and (cierre == 0 and icancelar == 0):
            ventana.update()

        if icancelar == 1:
            limpiar_frames()
            arr = []
            peores = []
            mejores = []
            icancelar = 0
            return []

        if cierre == 1:
            sys.exit()

        if seleccion_texto == pivot:
            peores.append(arr[item])
        elif seleccion_texto == arr[item]:
            mejores.append(arr[item])

        seleccionado = 0
        seleccion_texto = ""

    indice += 1
    return quicksort(mejores) + [pivot] + quicksort(peores)

def mostrarArchivos(file1, file2):
    limpiar_frames()
    cargar_y_mostrar_pdf(file1, frame_interno1, canvas_pdf1)
    cargar_y_mostrar_pdf(file2, frame_interno2, canvas_pdf2)

def cargar_y_mostrar_pdf(file, frame_interno, canvas_pdf):
    try:
        canvas_pdf.create_window((0, 0), window=frame_interno, anchor="nw")
        label_file_name = tk.Label(frame_interno, text=f"Document: {file.namePdf}", font=("Arial", 10, "bold"))
        label_file_name.pack(pady=10)  # Añadir un pequeño espacio debajo del label
        
        label = tk.Label(frame_interno, text=file.texto, justify=tk.LEFT, wraplength=800)
        label.pack()
        label.bind("<Button-1>", lambda event: label_click(file))
        frame_interno.update_idletasks()
        canvas_pdf.config(scrollregion=canvas_pdf.bbox("all"))

    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el archivo {file}: {e}")

def label_click(file):
    global seleccionado, seleccion_texto
    seleccionado = 1
    seleccion_texto = file

def cancelar():
    global icancelar
    icancelar = 1

def inicializar_interfaz():
    global ventana, boton_buscar, frame_pdf1, frame_pdf2, canvas_pdf1, canvas_pdf2, frame_interno1, frame_interno2  

    ventana = tk.Tk()
    ventana.title("Programa corrección de pares")
    #ventana.iconbitmap("D:\\Universidad\\4to\\PYTHON\\CorreccionPares\\logo.ico")
    ventana.protocol("WM_DELETE_WINDOW", on_closing)

    ventana.state("zoomed")
    
    boton_salir = tk.Button(ventana, text="Salir", command=on_closing)
    boton_salir.place(relx=0.2, y=10, anchor="n")
    
    boton_guardar = tk.Button(ventana, text="Guardar")
    boton_guardar.place(relx=0.4, y=10, anchor="n")
    
    frame_pdf1 = tk.Frame(ventana, bd=2, relief=tk.RAISED, bg="RoyalBlue1")
    frame_pdf1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    frame_pdf2 = tk.Frame(ventana, bd=2, relief=tk.RAISED, bg="red2")
    frame_pdf2.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    canvas_pdf1 = tk.Canvas(frame_pdf1)
    canvas_pdf1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    scrollbar_pdf1 = tk.Scrollbar(frame_pdf1, orient="vertical", command=canvas_pdf1.yview)
    scrollbar_pdf1.pack(side=tk.RIGHT, fill="y")
    canvas_pdf1.config(yscrollcommand=scrollbar_pdf1.set)

    frame_interno1 = tk.Frame(canvas_pdf1)

    canvas_pdf2 = tk.Canvas(frame_pdf2)
    canvas_pdf2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

    scrollbar_pdf2 = tk.Scrollbar(frame_pdf2, orient="vertical", command=canvas_pdf2.yview)
    scrollbar_pdf2.pack(side=tk.RIGHT, fill="y")
    canvas_pdf2.config(yscrollcommand=scrollbar_pdf2.set)

    frame_interno2 = tk.Frame(canvas_pdf2)



def limpiar_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()

def limpiar_frames():
    limpiar_frame(frame_interno1)
    limpiar_frame(frame_interno2)

def on_closing():
    global cierre
    if messagebox.askokcancel("Salir", "¿Seguro que quieres cerrar la aplicación?"):
        cierre = 1
        ventana.destroy()
        sys.exit()


def main(textos):
    global resultados_path
    # Inicializa la interfaz de Tkinter
    inicializar_interfaz()
    
    # Procesar los objetos EvPDF (los textos vienen como una lista de diccionarios)
    evpdf_objects = []

    for data in textos:
        # Crear un objeto EvPDF por cada diccionario
        evpdf = EvPDF(namePdf=data['namePdf'], texto=data['texto'])
        evpdf_objects.append(evpdf)

    # Ordena los textos
    sorted_texts = quicksort(evpdf_objects)
    
    for i in range(0,len(sorted_texts)):
        sorted_texts[i].nota=len(sorted_texts)-i
        
    evpdf_data = []
    for ev_pdf in sorted_texts:  # Supón que lista_evpdf es tu lista de objetos EvPDF
        evpdf_data.append({
            'namePdf': ev_pdf.namePdf,
            'texto': ev_pdf.texto,
            'nota': ev_pdf.nota
        })

    # Guarda la lista ordenada en un archivo
    with open(resultados_path, 'w') as f:
        json.dump(evpdf_data, f)  # Guarda la lista ordenada en formato JSON

    # Al finalizar, puedes cerrar la ventana si es necesario
    ventana.destroy()

if __name__ == "__main__":
    # Verificamos si hay al menos un argumento (el archivo temporal)
    if len(sys.argv) > 1:
        # Obtener la ruta del archivo temporal
        temp_file_path = sys.argv[1]
        resultados_path=sys.argv[2]
        # Leer el contenido del archivo temporal
        with open(temp_file_path, 'r', encoding='utf-8') as f:
            textos = json.load(f)  # 'textos' es ahora una lista de diccionarios de EvPDF
        
        # Llamar a la función principal con los textos leídos
        main(textos)

        # Después de usar el archivo, lo eliminamos para evitar dejar archivos temporales
        os.remove(temp_file_path)