from werkzeug.security import check_password_hash
from flask_login import UserMixin
import secrets

class Usuario(UserMixin):
    def __init__(self, id, usuario, contraseña,rol="", session_token=""):
        self.id=id
        self.usuario=usuario
        self.contraseña=contraseña
        self.rol=rol
        self.session_token=session_token
    
    def generar_session_token(self):
        self.session_token = secrets.token_hex(16)
        
    def setRol(self,rol):
        self.rol=rol
        
    def check_password(self, plain_password):
        """
        Comprueba si la contraseña en texto plano coincide con el hash almacenado.
        :param plain_password: Contraseña ingresada por el usuario (texto plano).
        :return: True si coincide, False de lo contrario.
        """
        return check_password_hash(self.contraseña, plain_password)

#Hola123= scrypt:32768:8:1$yroW3JiBpZ396wZf$bc94e8b7285946e39cbbcbcc805dbcb2dce9062442dbed7b5d2906587bdb0adbfc9f3825b803376ba276f8e812b0edc56586dd1d8889b47ae062dea301b6a8ce

            
            