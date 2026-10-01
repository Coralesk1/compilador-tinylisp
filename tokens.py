import re

class Token:
    def __init__(self, tipo, lexema, linha):
        self.tipo = tipo
        self.lexema = lexema
        self.linha = linha

    def __repr__(self):
        return f"Token: {self.tipo} {repr(self.lexema)} (linha {self.linha})"