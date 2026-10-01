import re

class Token:
    def __init__(self, indentificador, valor):
        self.indentificador = indentificador
        self.valor = valor

    def __repr__(self):
        return f"Token: {self.indentificador} - {repr(self.valor)}"