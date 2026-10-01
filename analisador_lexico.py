import re
from tokens import Token

class ErroLexico(Exception):
	pass

class AnalisadorLexico:
	REGEXS = [
		("ESPACO",  r"\s+"),
		("AP",      r"\("),
		("FP",      r"\)"),
		("OP_SOMA", r"\+"),
		("OP_SUB",  r"-"),
		("OP_MULT", r"\*"),
		("OP_DIV",  r"/"),
		("OP_MOD",  r"%"),
		("OP_MAI",  r">="),
		("OP_MA",   r">"),
		("OP_MEI",  r"<="),
		("OP_ME",   r"<"),
		("OP_II",   r"=="),
		("OP_DIFF", r"!="),
		("OP_I",    r"="),
		("NUM_INT", r"[0-9]+(?![a-zA-Z_])"),
		("ID",      r"[a-zA-Z_][a-zA-Z0-9_]*"),
	]
		
	PALAVRAS_RESERVADAS = {
		"defun": 	"PR_DEFUN",
		"if":	 	"PR_IF",
		"while": 	"PR_WHILE",
		"begin": 	"PR_BEGIN",
		"set":		"PR_SET",
		"print": 	"PR_PRINT",
		"let":   	"PR_LET",
	}
		
	DESCARTAR = {"ESPACO"}

	def __init__(self, codigo: str):
		self.codigo = codigo
		self.pos = 0 
		self.linha = 1
		
		self.regras = []
		for item in self.REGEXS: 	# item[0] -> ("NUM_INT", r"[0-9]+"),
			tok = item[0]
			regra_tex = item[1]
			self.regras.append((tok, re.compile(regra_tex)))
			
	def __prox_token(self):
		while self.pos < len(self.codigo): # loop no texto
			for item in self.regras:
				tok = item[0]
				regra_tex = item[1]
				casamento = regra_tex.match(self.codigo, self.pos) # casamento de regra na pos atual do texto
				if not casamento:
					continue
					
				lex = casamento.group() # lexema obtido
				linha_tok = self.linha
					
				self.linha += lex.count("\n")
				self.pos += len(lex)
					
				if tok in self.DESCARTAR:
					break
						
				if tok == "ID": # checar lexema em PR, se existe entao sai em formato PR_
					tok = self.PALAVRAS_RESERVADAS.get(lex, "ID")
						
				return Token(tok, lex, linha_tok)
			else:
				ch = self.codigo[self.pos]
				raise ErroLexico(f"Erro Lexico: Caractere invalido '{ch}' na linha {self.linha}.")
					
		return Token("FIM", "", self.linha)
			
	def tokenizar(self):
		toks = []
		while 1:
			t = self.__prox_token()
			toks.append(t)
			if t.tipo == "FIM":
				return toks
		

		
	
	