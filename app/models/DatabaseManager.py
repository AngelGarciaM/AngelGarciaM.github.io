import sqlite3
import os
from models.models import Correccion,Lista,EvPDF
from models.Usuario import Usuario

#D:\Universidad\Practicas\WebApp\app\DataBase
class DatabaseManager:
    def __init__(self, db_name="app\\DataBase\\correcciones.db"):
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.connection.cursor()
        
        # Crear tabla para Usuarios
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            contraseña TEXT NOT NULL,
            rol TEXT NOT NULL,
            session_token TEXT NOT NULL
        )
        ''')
        
        # Crear tabla para Correccion
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Correccion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL
        )
        ''')
        
        # Crear tabla para Lista, con referencia a Correccion
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Lista (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            evaluado BOOLEAN NOT NULL,
            corrector TEXT NOT NULL,
            correccion_id INTEGER,
            FOREIGN KEY (correccion_id) REFERENCES Correccion(id)
        )
        ''')
        
        # Crear tabla para EvPDF, con referencia a Lista
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS EvPDF (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_archivo TEXT NOT NULL,
            texto TEXT,
            nota INTEGER,
            lista_id INTEGER,
            FOREIGN KEY (lista_id) REFERENCES Lista(id)
        )
        ''')
                
        self.connection.commit()

    def close(self):
        self.connection.close()

    def guardar_correccion(self, correccion):
        cursor = self.connection.cursor()
        
        # Insertar Correccion
        cursor.execute("INSERT INTO Correccion (nombre) VALUES (?)", (correccion.nombre,))
        correccion_id = cursor.lastrowid  # Obtener el ID de la corrección recién insertada
        
        # Insertar Listas asociadas a la Corrección
        for lista in correccion.listas:
            cursor.execute("INSERT INTO Lista (titulo, evaluado, corrector, correccion_id) VALUES (?, ?, ?, ?)", 
                           (lista.titulo, lista.evaluado, lista.corrector, correccion_id))
            lista_id = cursor.lastrowid  # Obtener el ID de la lista recién insertada
            
            # Insertar PDFs asociados a la Lista
            for ev_pdf in lista.textos:
                cursor.execute("INSERT INTO EvPDF (nombre_archivo, texto, nota, lista_id) VALUES (?, ?, ?, ?)",
                               (ev_pdf.namePdf, ev_pdf.texto, ev_pdf.nota, lista_id))
        
        self.connection.commit()
    
    def eliminar_correccion(self, nombre_correccion):
        cursor = self.connection.cursor()
        
        # Obtener el ID de la corrección basada en su nombre
        cursor.execute("SELECT id FROM Correccion WHERE nombre = ?", (nombre_correccion,))
        correccion = cursor.fetchone()
        
        # Verificar si la corrección existe
        if correccion is None:
            print(f"No se encontró una corrección con el nombre: {nombre_correccion}")
            return
        
        correccion_id = correccion[0]
        
        # Primero eliminamos los PDFs asociados a las listas de la corrección
        cursor.execute("SELECT id FROM Lista WHERE correccion_id = ?", (correccion_id,))
        listas = cursor.fetchall()
        
        # Eliminar los PDFs de cada lista
        for lista in listas:
            lista_id = lista[0]
            cursor.execute("DELETE FROM EvPDF WHERE lista_id = ?", (lista_id,))
        
        # Eliminar las listas asociadas a la corrección
        cursor.execute("DELETE FROM Lista WHERE correccion_id = ?", (correccion_id,))
        
        # Finalmente, eliminamos la corrección
        cursor.execute("DELETE FROM Correccion WHERE id = ?", (correccion_id,))
        
        # Confirmar los cambios en la base de datos
        self.connection.commit()
        

    def cargar_correcciones(self):
        cursor = self.connection.cursor()
        correcciones = []
        
        # Cargar todas las correcciones
        cursor.execute("SELECT id, nombre FROM Correccion")
        correccion_rows = cursor.fetchall()
        
        for correccion_row in correccion_rows:
            correccion_id, nombre = correccion_row
            correccion = Correccion(nombre)
            
            # Cargar listas asociadas a esta corrección
            cursor.execute("SELECT id, titulo, evaluado, corrector FROM Lista WHERE correccion_id = ?", (correccion_id,))
            lista_rows = cursor.fetchall()
            
            for lista_row in lista_rows:
                lista_id, titulo, evaluado, corrector = lista_row
                lista = Lista(titulo, [])
                lista.evaluado = bool(evaluado)
                lista.corrector=corrector
                
                # Cargar PDFs asociados a esta lista
                cursor.execute("SELECT nombre_archivo, texto, nota FROM EvPDF WHERE lista_id = ?", (lista_id,))
                evpdf_rows = cursor.fetchall()
                
                for evpdf_row in evpdf_rows:
                    nombre_archivo, texto, nota = evpdf_row
                    evpdf = EvPDF("","")
                    evpdf.namePdf = nombre_archivo
                    evpdf.texto = texto
                    evpdf.nota = nota
                    lista.textos.append(evpdf)
                
                correccion.agregar_lista(lista)
            
            correcciones.append(correccion)
        
        return correcciones

    def recuperar_correccion(self, nombre_correccion):
        """
        Recupera una corrección específica por su nombre, incluyendo sus listas y PDFs asociados.
        """
        cursor = self.connection.cursor()

        # Cargar la corrección por su nombre
        cursor.execute("SELECT id FROM Correccion WHERE nombre = ?", (nombre_correccion,))
        correccion_row = cursor.fetchone()
        if correccion_row is None:
            return None  # Si no se encuentra la corrección, devuelve None

        correccion_id = correccion_row[0]
        correccion = Correccion(nombre_correccion)
        
        # Cargar listas asociadas a esta corrección
        cursor.execute("SELECT id, titulo, evaluado, corrector FROM Lista WHERE correccion_id = ?", (correccion_id,))
        lista_rows = cursor.fetchall()
        
        for lista_row in lista_rows:
            lista_id, titulo, evaluado, corrector = lista_row
            lista = Lista(titulo, [])
            lista.evaluado = bool(evaluado)
            lista.corrector=corrector
            
            # Cargar PDFs asociados a esta lista
            cursor.execute("SELECT nombre_archivo, texto, nota FROM EvPDF WHERE lista_id = ?", (lista_id,))
            evpdf_rows = cursor.fetchall()
            
            for evpdf_row in evpdf_rows:
                nombre_archivo, texto, nota = evpdf_row
                evpdf = EvPDF("","")  # Instanciar con un nombre temporal
                evpdf.namePdf = nombre_archivo
                evpdf.texto = texto
                evpdf.nota = nota
                lista.textos.append(evpdf)
            
            correccion.agregar_lista(lista)
        
        return correccion

    def actualizar_correccion(self, correccion):
        """
        Actualiza una corrección existente en la base de datos usando un objeto Correccion completo.
        Reemplaza el nombre de la corrección, las listas y los PDFs asociados.
        """
        cursor = self.connection.cursor()

        # Primero obtener el ID de la corrección usando su nombre
        cursor.execute("SELECT id FROM Correccion WHERE nombre = ?", (correccion.nombre,))
        correccion_row = cursor.fetchone()
        
        if correccion_row is None:
            raise ValueError("Corrección no encontrada en la base de datos")
        
        correccion_id = correccion_row[0]

        # Actualizar el nombre de la corrección
        cursor.execute("UPDATE Correccion SET nombre = ? WHERE id = ?", (correccion.nombre, correccion_id))
        
        # Eliminar las listas y los EvPDF asociados a la corrección
        cursor.execute("DELETE FROM EvPDF WHERE lista_id IN (SELECT id FROM Lista WHERE correccion_id = ?)", (correccion_id,))
        cursor.execute("DELETE FROM Lista WHERE correccion_id = ?", (correccion_id,))
        
        # Insertar las nuevas listas
        for lista in correccion.listas:
            cursor.execute("INSERT INTO Lista (titulo, evaluado, corrector, correccion_id) VALUES (?, ?, ?, ?)", 
                        (lista.titulo, lista.evaluado, lista.corrector, correccion_id))
            lista_id = cursor.lastrowid  # Obtener el nuevo ID de la lista
            
            # Insertar los EvPDF asociados a la lista
            for ev_pdf in lista.textos:
                cursor.execute("INSERT INTO EvPDF (nombre_archivo, texto, nota, lista_id) VALUES (?, ?, ?, ?)",
                            (ev_pdf.namePdf, ev_pdf.texto, ev_pdf.nota, lista_id))

        self.connection.commit()
    
    # Métodos para gestionar usuarios
    def agregar_usuario(self,user):
        cursor = self.connection.cursor()
        try:
            cursor.execute("INSERT INTO Usuario (usuario, contraseña, rol, session_token) VALUES (?, ?, ?, ?)", 
                           (user.usuario, user.contraseña, user.rol, user.session_token))
            self.connection.commit()
        except sqlite3.IntegrityError:
            raise ValueError("El usuario ya existe en la base de datos")
    
    def obtener_usuario_(self, usuario):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, usuario, contraseña, rol FROM Usuario WHERE usuario = ?", (usuario,))
        return cursor.fetchone()

    def obtener_nombres_todos_tutores(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT usuario FROM Usuario WHERE rol = 'tutor'") 
        return cursor.fetchall()  # Devuelve una lista de tuplas
        
    def actualizar_usuario(self, usuario, nueva_contraseña=None, nuevo_rol=None, nuevo_session=None):
        cursor = self.connection.cursor()
        if nueva_contraseña:
            cursor.execute("UPDATE Usuario SET contraseña = ? WHERE usuario = ?", (nueva_contraseña, usuario))
        if nuevo_rol:
            cursor.execute("UPDATE Usuario SET rol = ? WHERE usuario = ?", (nuevo_rol, usuario))
        if nuevo_session:
            cursor.execute("UPDATE Usuario SET session_token = ? WHERE usuario = ?", (nuevo_session, usuario))
        self.connection.commit()

    def eliminar_usuario(self, usuario):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM Usuario WHERE usuario = ?", (usuario,))
        self.connection.commit()
    
    def obtener_usuario(self, nombre_usuario):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, usuario, contraseña, rol, session_token FROM Usuario WHERE usuario = ?", (nombre_usuario,))
        row = cursor.fetchone()
        if row:
            return Usuario(id=row[0], usuario=row[1], contraseña=row[2], rol=row[3], session_token=row[4])
        return None
    
    def obtener_usuario_por_id(self, id):
        """
        Comprueba si un usuario existe en la base de datos y devuelve un objeto Usuario si existe.
        :param nombre_usuario: El nombre de usuario a buscar.
        :return: Objeto Usuario si existe, None en caso contrario.
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, usuario, contraseña, rol, session_token FROM Usuario WHERE id = ?", (id,))
        row = cursor.fetchone()
        if row:
            # Crear y devolver un objeto Usuario
            return Usuario(id=row[0], usuario=row[1], contraseña=row[2], rol=row[3])
        return None
    
    def obtener_usuario_por_session_token(self, session_token):
        """
        Comprueba si un usuario existe en la base de datos usando su session_token y devuelve un objeto Usuario si existe.
        :param session_token: El token de sesión del usuario a buscar.
        :return: Objeto Usuario si existe, None en caso contrario.
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, usuario, contraseña, rol, session_token FROM Usuario WHERE session_token = ?", (session_token,))
        row = cursor.fetchone()
        if row:
            # Crear y devolver un objeto Usuario
            return Usuario(id=row[0], usuario=row[1], contraseña=row[2], rol=row[3], session_token=row[4])
        return None