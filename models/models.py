import fitz,os

class EvPDF:
    def obtenerTexto(self, namePdf):
        pdf_document = fitz.open(namePdf)
        nombre_archivo = os.path.basename(namePdf)  # Extraer solo el nombre del archivo
        
        # Acumular el texto de todas las páginas
        texto_completo = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            texto_completo += page.get_text()  # Concatenar el texto de cada página

        return nombre_archivo, texto_completo
    
    #def __init__(self,path):
        
     #   self.namePdf,self.texto=self.obtenerTexto(path)
      #  self.nota=0
    def __init__(self, namePdf,texto, nota=0):
        self.namePdf=namePdf
        self.texto=texto
        self.nota=nota

class Lista:
    def __init__(self, titulo,textos):
        """
        Inicializa la lista con un título y opcionalmente una lista de objetos EvPDF.
        Si no se proporcionan textos, la lista de textos queda vacía.
        """
        self.titulo = titulo  # Título de la lista
        self.textos = textos
        self.corrector="Holahola" #Usuario que ha corregido esta lista
        self.evaluado = False  # Estado de evaluación de la lista

class Correccion:
    def __init__(self, nombre):
        self.nombre = nombre
        self.listas = []

    def agregar_lista(self, listas):
        """
        Agrega una lista de objetos Lista a la corrección.
        """
        # Si 'listas' es un solo objeto Lista, lo agrega
        if isinstance(listas, Lista):
            self.listas.append(listas)
        # Si 'listas' es una lista de objetos Lista, agrega todos
        elif isinstance(listas, list):
            for lista in listas:
                if isinstance(lista, Lista):  # Verifica que cada item sea un objeto Lista
                    self.listas.append(lista)
                else:
                    raise ValueError("Todos los elementos deben ser instancias de la clase Lista.")
        else:
            raise ValueError("El argumento debe ser una instancia de Lista o una lista de instancias de Lista.")
        
    def evaluado(self):
        listas_evaluadas=0
        for lista in self.listas:
            if lista.evaluado:
                listas_evaluadas+=1
        if listas_evaluadas==len(self.listas):
            return True
        return False

