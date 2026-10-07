"""
analisador_sintatico.py
Implementação do Analisador Sintático Descendente Recursivo para Mini-Lisp.
Recebe a lista de tokens do analisador léxico e gera a Árvore Sintática Abstrata (AST).
"""

from tokens import Token


class ErroSintatico(Exception):
    """Exceção levantada quando ocorre um erro de sintaxe no código-fonte."""
    pass


class NoAST:
    """
    Representa um nó na Árvore Sintática Abstrata (AST).
    Cada nó possui um tipo (ex: 'IF', 'WHILE', 'SET', 'NUMERO'),
    um valor opcional (ex: lexema ou valor numérico) e uma lista de nós filhos.
    """
    def __init__(self, tipo: str, valor=None, filhos=None, linha: int = 1):
        self.tipo = tipo
        self.valor = valor
        self.filhos = filhos if filhos is not None else []
        self.linha = linha

    def __repr__(self):
        if self.valor is not None:
            return f"NoAST({self.tipo}, valor={repr(self.valor)})"
        return f"NoAST({self.tipo})"

    def exibir(self, nivel: int = 0):
        """Imprime a árvore sintática de forma indentada e visual no terminal."""
        indent = "  " * nivel
        val_str = f" : {self.valor}" if self.valor is not None else ""
        print(f"{indent}- {self.tipo}{val_str} (linha {self.linha})")
        for f in self.filhos:
            if isinstance(f, NoAST):
                f.exibir(nivel + 1)
            else:
                print(f"{indent}  - {repr(f)}")


class AnalisadorSintatico:
    """
    Analisador Sintático Descendente Recursivo para a linguagem Mini-Lisp.
    """
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # --- MÉTODOS AUXILIARES DE NAVEGAÇÃO ---

    def atual(self) -> Token:
        """Retorna o token atual sem consumir."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def avancar(self) -> Token:
        """Consome o token atual e avança o cursor."""
        tok = self.atual()
        if self.pos < len(self.tokens):
            self.pos += 1
        return tok

    def combinar(self, *tipos: str) -> bool:
        """Verifica se o tipo do token atual coincide com algum dos tipos fornecidos."""
        return self.atual().tipo in tipos

    def consumir(self, tipo_esperado: str, mensagem_custom: str = None) -> Token:
        """
        Consome obrigatoriamente um token do tipo esperado.
        Se não coincidir, dispara um ErroSintatico formatado.
        """
        tok = self.atual()
        if tok.tipo == tipo_esperado:
            return self.avancar()

        if mensagem_custom:
            raise ErroSintatico(mensagem_custom)

        if tok.tipo == "FIM":
            raise ErroSintatico(f"Erro Sintático na linha {tok.linha}: Fim de arquivo inesperado. Esperava-se '{tipo_esperado}'.")
        
        raise ErroSintatico(f"Erro Sintático na linha {tok.linha}: Esperava-se '{tipo_esperado}', mas obteve '{tok.lexema}' ({tok.tipo}).")

    def eh_operador(self, tipo: str) -> bool:
        """Verifica se o token é um operador (+, -, *, /, >, <, etc.)."""
        return tipo.startswith("OP_")

    # --- REGRAS DA GRAMÁTICA (BNF) ---

    def parse(self) -> NoAST:
        """Ponto de entrada do compilador sintático."""
        ast = self.programa()
        if not self.combinar("FIM"):
            tok = self.atual()
            raise ErroSintatico(f"Erro Sintático na linha {tok.linha}: Conteúdo inesperado após o término do programa: '{tok.lexema}'.")
        return ast

    def programa(self) -> NoAST:
        """
        <program> ::= <expr_list>
        """
        linha_inicio = self.atual().linha
        expressoes = []
        while not self.combinar("FIM"):
            expressoes.append(self.expr())
        return NoAST("PROGRAMA", filhos=expressoes, linha=linha_inicio)

    def expr(self) -> NoAST:
        """
        <expr> ::= <atom> | <generic_list> | <defun_expr> | <let_expr>
        """
        if self.combinar("AP"):
            return self.lista()
        elif self.combinar("NUM_INT", "NUM_FLOAT"):
            tok = self.avancar()
            valor = int(tok.lexema) if tok.tipo == "NUM_INT" else float(tok.lexema)
            return NoAST("NUMERO", valor=valor, linha=tok.linha)
        elif self.combinar("ID"):
            tok = self.avancar()
            return NoAST("ID", valor=tok.lexema, linha=tok.linha)
        elif self.eh_operador(self.atual().tipo):
            tok = self.avancar()
            return NoAST("OPERADOR", valor=tok.lexema, linha=tok.linha)
        else:
            tok = self.atual()
            if tok.tipo == "FIM":
                raise ErroSintatico(f"Erro Sintático na linha {tok.linha}: Fim de arquivo inesperado ao aguardar expressão.")
            raise ErroSintatico(f"Erro Sintático na linha {tok.linha}: Expressão inválida iniciando com '{tok.lexema}'.")

    def lista(self) -> NoAST:
        """
        Processa qualquer estrutura iniciada por '(':
        Pode ser defun, let, if, while, set, print, begin, operação ou chamada de função.
        """
        tok_ap = self.consumir("AP")

        # Lista vazia: ()
        if self.combinar("FP"):
            self.consumir("FP")
            return NoAST("LISTA_VAZIA", linha=tok_ap.linha)

        primeiro = self.atual()

        if primeiro.tipo == "PR_DEFUN":
            return self.defun_expr(tok_ap)
        elif primeiro.tipo == "PR_LET":
            return self.let_expr(tok_ap)
        elif primeiro.tipo == "PR_IF":
            return self.if_expr(tok_ap)
        elif primeiro.tipo == "PR_WHILE":
            return self.while_expr(tok_ap)
        elif primeiro.tipo == "PR_SET":
            return self.set_expr(tok_ap)
        elif primeiro.tipo == "PR_PRINT":
            return self.print_expr(tok_ap)
        elif primeiro.tipo == "PR_BEGIN":
            return self.begin_expr(tok_ap)
        elif self.eh_operador(primeiro.tipo):
            return self.operacao_expr(tok_ap)
        else:
            return self.chamada_ou_lista_generica(tok_ap)

    def defun_expr(self, tok_ap: Token) -> NoAST:
        """
        <defun_expr> ::= "(" "defun" <id> "(" <param_list> ")" <expr_list> ")"
        """
        self.consumir("PR_DEFUN")
        tok_nome = self.consumir("ID", f"Erro Sintático na linha {self.atual().linha}: Nome de função esperado após 'defun'.")

        self.consumir("AP", f"Erro Sintático na linha {self.atual().linha}: Esperava-se '(' para lista de parâmetros da função '{tok_nome.lexema}'.")
        params = []
        while self.combinar("ID"):
            tok_p = self.avancar()
            params.append(NoAST("PARAMETRO", valor=tok_p.lexema, linha=tok_p.linha))

        if self.combinar("FIM"):
            raise ErroSintatico(f"Erro Sintático na linha {tok_ap.linha}: Fim de arquivo inesperado. Esperava-se ')' para fechar parâmetros.")
        self.consumir("FP", f"Erro Sintático na linha {self.atual().linha}: Esperava-se ')' para fechar parâmetros da função '{tok_nome.lexema}'.")

        corpo = []
        while not self.combinar("FP", "FIM"):
            corpo.append(self.expr())

        if self.combinar("FIM"):
            raise ErroSintatico(f"Erro Sintático na linha {tok_ap.linha}: Fim de arquivo inesperado. Esperava-se ')' ao fechar 'defun'.")
        self.consumir("FP")

        no_params = NoAST("PARAMETROS", filhos=params, linha=tok_nome.linha)
        no_corpo = NoAST("CORPO", filhos=corpo, linha=tok_nome.linha)
        return NoAST("DEFUN", valor=tok_nome.lexema, filhos=[no_params, no_corpo], linha=tok_ap.linha)

    def let_expr(self, tok_ap: Token) -> NoAST:
        """
        <let_expr> ::= "(" "let" "(" <binding_list> ")" <expr_list> ")"
        """
        self.consumir("PR_LET")
        self.consumir("AP", f"Erro Sintático na linha {self.atual().linha}: Esperava-se '(' para iniciar as declarações do 'let'.")

        declaracoes = []
        while self.combinar("AP"):
            tok_b_ap = self.avancar()
            tok_var = self.consumir("ID", f"Erro Sintático na linha {self.atual().linha}: Esperava-se nome de variável na declaração do 'let'.")
            expr_val = self.expr()
            if self.combinar("FIM"):
                raise ErroSintatico(f"Erro Sintático na linha {tok_b_ap.linha}: Fim de arquivo inesperado. Esperava-se ')' na declaração.")
            self.consumir("FP", f"Erro Sintático na linha {self.atual().linha}: Esperava-se ')' após o valor de '{tok_var.lexema}' no 'let'.")
            declaracoes.append(NoAST("DECLARACAO", valor=tok_var.lexema, filhos=[expr_val], linha=tok_b_ap.linha))

        if self.combinar("FIM"):
            raise ErroSintatico(f"Erro Sintático na linha {tok_ap.linha}: Fim de arquivo inesperado. Esperava-se ')' para fechar as declarações do 'let'.")
        self.consumir("FP", f"Erro Sintático na linha {self.atual().linha}: Esperava-se ')' para fechar a lista de declarações do 'let'.")

        corpo = []
        while not self.combinar("FP", "FIM"):
            corpo.append(self.expr())

        if self.combinar("FIM"):
            raise ErroSintatico(f"Erro Sintático na linha {tok_ap.linha}: Fim de arquivo inesperado. Esperava-se ')' ao fechar 'let'.")
        self.consumir("FP")

        no_decls = NoAST("DECLARACOES", filhos=declaracoes, linha=tok_ap.linha)
        no_corpo = NoAST("CORPO", filhos=corpo, linha=tok_ap.linha)
        return NoAST("LET", filhos=[no_decls, no_corpo], linha=tok_ap.linha)

    def if_expr(self, tok_ap: Token) -> NoAST:
        """
        Condicional: (if <condicao> <ramo_then> <ramo_else>)
        Valida a omissão do ramo 'else' conforme o exemplo negativo do PDF!
        """
        self.consumir("PR_IF")
        condicao = self.expr()

        if self.combinar("FP", "FIM"):
            raise ErroSintatico(f"Erro Sintático na linha {tok_ap.linha}: Estrutura 'if' malformada. Omitido argumento de ramo 'then'.")
        ramo_then = self.expr()

        # Validação exigida especificamente no PDF
        if self.combinar("FP", "FIM"):
            raise ErroSintatico("Erro Sintático: Estrutura 'if' malformada. Omitido argumento de 'else'.")
        ramo_else = self.expr()

        if self.combinar("FIM"):
            raise ErroSintatico(f"Erro Sintático na linha {tok_ap.linha}: Fim de arquivo inesperado. Esperava-se ')' ao fechar 'if'.")
        self.consumir("FP", f"Erro Sintático na linha {self.atual().linha}: Esperava-se ')' após argumentos do 'if'.")

        return NoAST("IF", filhos=[condicao, ramo_then, ramo_else], linha=tok_ap.linha)

    def while_expr(self, tok_ap: Token) -> NoAST:
        """
        Repetição: (while <condicao> <expr_list>)
        """
        self.consumir("PR_WHILE")
        condicao = self.expr()
        corpo = []
        while not self.combinar("FP", "FIM"):
            corpo.append(self.expr())

        if self.combinar("FIM"):
            raise ErroSintatico(f"Erro Sintático na linha {tok_ap.linha}: Fim de arquivo inesperado. Esperava-se ')' ao fechar 'while'.")
        self.consumir("FP")
        return NoAST("WHILE", filhos=[condicao, NoAST("CORPO", filhos=corpo, linha=tok_ap.linha)], linha=tok_ap.linha)

    def set_expr(self, tok_ap: Token) -> NoAST:
        """
        Atribuição: (set <id> <expr>)
        """
        self.consumir("PR_SET")
        tok_id = self.consumir("ID", f"Erro Sintático na linha {self.atual().linha}: Esperava-se identificador após 'set'.")
        valor = self.expr()

        if self.combinar("FIM"):
            raise ErroSintatico(f"Erro Sintático na linha {tok_ap.linha}: Fim de arquivo inesperado. Esperava-se ')' ao fechar 'set'.")
        self.consumir("FP", f"Erro Sintático na linha {self.atual().linha}: Esperava-se ')' após atribuição de '{tok_id.lexema}'.")
        return NoAST("SET", valor=tok_id.lexema, filhos=[valor], linha=tok_ap.linha)

    def print_expr(self, tok_ap: Token) -> NoAST:
        """
        Impressão: (print <expr>)
        """
        linha_expr = self.atual().linha
        self.consumir("PR_PRINT")
        argumento = self.expr()

        if self.combinar("FIM"):
            raise ErroSintatico(f"Erro Sintático na linha {linha_expr}: Fim de arquivo inesperado. Esperava-se ')'.")
        self.consumir("FP", f"Erro Sintático na linha {self.atual().linha}: Esperava-se ')' após argumento do 'print'.")
        return NoAST("PRINT", filhos=[argumento], linha=tok_ap.linha)

    def begin_expr(self, tok_ap: Token) -> NoAST:
        """
        Bloco sequencial: (begin <expr_list>)
        """
        self.consumir("PR_BEGIN")
        expressoes = []
        while not self.combinar("FP", "FIM"):
            expressoes.append(self.expr())

        if self.combinar("FIM"):
            raise ErroSintatico(f"Erro Sintático na linha {tok_ap.linha}: Fim de arquivo inesperado. Esperava-se ')'.")
        self.consumir("FP")
        return NoAST("BEGIN", filhos=expressoes, linha=tok_ap.linha)

    def operacao_expr(self, tok_ap: Token) -> NoAST:
        """
        Operação prefixada: (<operador> <arg1> <arg2> ...)
        """
        tok_op = self.avancar()
        argumentos = []
        while not self.combinar("FP", "FIM"):
            argumentos.append(self.expr())

        if self.combinar("FIM"):
            raise ErroSintatico(f"Erro Sintático na linha {tok_ap.linha}: Fim de arquivo inesperado. Esperava-se ')'.")
        self.consumir("FP")
        return NoAST("OPERACAO", valor=tok_op.lexema, filhos=argumentos, linha=tok_ap.linha)

    def chamada_ou_lista_generica(self, tok_ap: Token) -> NoAST:
        """
        Chamadas de função como (square 5) ou listas genéricas.
        """
        primeiro = self.expr()
        argumentos = []
        while not self.combinar("FP", "FIM"):
            argumentos.append(self.expr())

        if self.combinar("FIM"):
            raise ErroSintatico(f"Erro Sintático na linha {tok_ap.linha}: Fim de arquivo inesperado. Esperava-se ')'.")
        self.consumir("FP")

        if primeiro.tipo == "ID":
            return NoAST("CHAMADA_FUNCAO", valor=primeiro.valor, filhos=argumentos, linha=tok_ap.linha)
        return NoAST("LISTA_GENERICA", filhos=[primeiro] + argumentos, linha=tok_ap.linha)
