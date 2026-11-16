import sys

from tokens import Token

sys.setrecursionlimit(max(sys.getrecursionlimit(), 10000))

NUMEROS = {"NUM_INT", "NUM_FLOAT"}
OPERADORES = {
    "OP_SOMA", "OP_SUB", "OP_MULT", "OP_DIV", "OP_MOD",
    "OP_MAI", "OP_MA", "OP_MEI", "OP_ME", "OP_II", "OP_DIFF", "OP_I",
}

PRIM_ATOM = NUMEROS | {"ID"} | OPERADORES
PRIM_EXPR = PRIM_ATOM | {"AP"}
SEGUE_EXPR_LIST = {"FP", "FIM"}


class ErroSintatico(Exception):
    pass


class NoAST:
    def __init__(self, tipo: str, valor=None, filhos=None, linha: int = 1):
        self.tipo = tipo
        self.valor = valor
        self.filhos = filhos if filhos is not None else []
        self.linha = linha

    # Mostra o tipo e o valor do nó para facilitar a depuração.
    def __repr__(self):
        if self.valor is not None:
            return f"NoAST({self.tipo}, valor={repr(self.valor)})"
        return f"NoAST({self.tipo})"

    # Imprime a árvore no terminal, com um recuo maior a cada nível.
    def exibir(self, nivel: int = 0):
        indent = "  " * nivel
        val_str = f" : {self.valor}" if self.valor is not None else ""
        print(f"{indent}- {self.tipo}{val_str} (linha {self.linha})")
        for f in self.filhos:
            if isinstance(f, NoAST):
                f.exibir(nivel + 1)
            else:
                print(f"{indent}  - {repr(f)}")


class AnalisadorSintatico:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.token = tokens[0]

    # Consome o token atual, avança para o próximo e devolve o token consumido.
    def prox(self) -> Token:
        consumido = self.token
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        self.token = self.tokens[self.pos]
        return consumido

    # Interrompe a análise levantando um erro sintático com a mensagem recebida.
    def erro(self, msg: str):
        raise ErroSintatico(msg)

    # Consome o token se for o esperado; senão gera o erro, tratando também o fim de arquivo.
    def accept(self, esperado: str, msg: str = None, linha_abertura: int = None, contexto: str = "") -> Token:
        tok = self.token
        if tok.tipo == esperado:
            return self.prox()

        simbolo = {"FP": "')'", "AP": "'('"}.get(esperado, f"'{esperado}'")

        if tok.tipo == "FIM" and linha_abertura is not None:
            complemento = f" {contexto}" if contexto else ""
            self.erro(f"Erro Sintático na linha {linha_abertura}: Fim de arquivo inesperado. Esperava-se {simbolo}{complemento}.")
        if msg:
            self.erro(msg)
        if tok.tipo == "FIM":
            self.erro(f"Erro Sintático na linha {tok.linha}: Fim de arquivo inesperado. Esperava-se {simbolo}.")
        self.erro(f"Erro Sintático na linha {tok.linha}: Esperava-se {simbolo}, mas obteve '{tok.lexema}' ({tok.tipo}).")

    # Ponto de entrada: analisa o programa inteiro e exige que termine no fim de arquivo.
    def parse(self) -> NoAST:
        self.pos = 0
        self.token = self.tokens[0]
        ast = self.program()
        if self.token.tipo != "FIM":
            self.erro(f"Erro Sintático na linha {self.token.linha}: Conteúdo inesperado após o término do programa: '{self.token.lexema}'.")
        return ast

    # Lê todas as expressões do programa e monta o nó raiz PROGRAMA.
    def program(self) -> NoAST:
        linha_inicio = self.token.linha
        expressoes = self.expr_list()
        return NoAST("PROGRAMA", filhos=expressoes, linha=linha_inicio)

    # Lê zero ou mais expressões em sequência e devolve a lista de nós.
    def expr_list(self) -> list:
        if self.token.tipo in PRIM_EXPR:
            primeiro = self.expr()
            return [primeiro] + self.expr_list()
        if self.token.tipo in SEGUE_EXPR_LIST:
            return []
        self.erro_expressao_invalida()

    # Lê uma expressão, que pode ser um átomo ou uma lista entre parênteses.
    def expr(self, msg_omitido: str = None) -> NoAST:
        if self.token.tipo in PRIM_ATOM:
            return self.atom()
        if self.token.tipo == "AP":
            tok_ap = self.prox()
            return self.lista(tok_ap)
        if msg_omitido and self.token.tipo in SEGUE_EXPR_LIST:
            self.erro(msg_omitido)
        self.erro_expressao_invalida()

    # Gera o erro de expressão inesperada ou de fim de arquivo quando faltou uma expressão.
    def erro_expressao_invalida(self):
        tok = self.token
        if tok.tipo == "FIM":
            self.erro(f"Erro Sintático na linha {tok.linha}: Fim de arquivo inesperado ao aguardar expressão.")
        self.erro(f"Erro Sintático na linha {tok.linha}: Expressão inválida iniciando com '{tok.lexema}'.")

    # Lê um número, identificador ou operador e cria o nó correspondente.
    def atom(self) -> NoAST:
        if self.token.tipo in NUMEROS:
            tok = self.prox()
            valor = int(tok.lexema) if tok.tipo == "NUM_INT" else float(tok.lexema)
            return NoAST("NUMERO", valor=valor, linha=tok.linha)
        if self.token.tipo == "ID":
            tok = self.prox()
            return NoAST("ID", valor=tok.lexema, linha=tok.linha)
        if self.token.tipo in OPERADORES:
            tok = self.prox()
            return NoAST("OPERADOR", valor=tok.lexema, linha=tok.linha)
        self.erro_expressao_invalida()

    # Depois do "(", escolhe qual estrutura analisar olhando o token seguinte.
    def lista(self, tok_ap: Token) -> NoAST:
        tipo = self.token.tipo
        if tipo == "PR_DEFUN":
            return self.defun_expr(tok_ap)
        if tipo == "PR_LET":
            return self.let_expr(tok_ap)
        if tipo == "PR_IF":
            return self.if_expr(tok_ap)
        if tipo == "PR_WHILE":
            return self.while_expr(tok_ap)
        if tipo == "PR_SET":
            return self.set_expr(tok_ap)
        if tipo == "PR_PRINT":
            return self.print_expr(tok_ap)
        if tipo == "PR_BEGIN":
            return self.begin_expr(tok_ap)
        return self.lista_generica(tok_ap)

    # Analisa a definição de função: (defun nome (parametros) corpo).
    def defun_expr(self, tok_ap: Token) -> NoAST:
        self.accept("PR_DEFUN")
        tok_nome = self.accept("ID", f"Erro Sintático na linha {self.token.linha}: Nome de função esperado após 'defun'.")

        self.accept("AP", f"Erro Sintático na linha {self.token.linha}: Esperava-se '(' para lista de parâmetros da função '{tok_nome.lexema}'.")
        params = self.param_list()
        self.accept("FP",
                    f"Erro Sintático na linha {self.token.linha}: Esperava-se ')' para fechar parâmetros da função '{tok_nome.lexema}'.",
                    linha_abertura=tok_ap.linha, contexto="para fechar parâmetros")

        corpo = self.expr_list()
        self.accept("FP", linha_abertura=tok_ap.linha, contexto="ao fechar 'defun'")

        no_params = NoAST("PARAMETROS", filhos=params, linha=tok_nome.linha)
        no_corpo = NoAST("CORPO", filhos=corpo, linha=tok_nome.linha)
        return NoAST("DEFUN", valor=tok_nome.lexema, filhos=[no_params, no_corpo], linha=tok_ap.linha)

    # Lê os nomes dos parâmetros de uma função até encontrar o ")".
    def param_list(self) -> list:
        if self.token.tipo == "ID":
            tok_p = self.prox()
            return [NoAST("PARAMETRO", valor=tok_p.lexema, linha=tok_p.linha)] + self.param_list()
        return []

    # Analisa o escopo local: (let ((var valor) ...) corpo).
    def let_expr(self, tok_ap: Token) -> NoAST:
        self.accept("PR_LET")
        self.accept("AP", f"Erro Sintático na linha {self.token.linha}: Esperava-se '(' para iniciar as declarações do 'let'.")

        declaracoes = self.binding_list()
        self.accept("FP",
                    f"Erro Sintático na linha {self.token.linha}: Esperava-se ')' para fechar a lista de declarações do 'let'.",
                    linha_abertura=tok_ap.linha, contexto="para fechar as declarações do 'let'")

        corpo = self.expr_list()
        self.accept("FP", linha_abertura=tok_ap.linha, contexto="ao fechar 'let'")

        no_decls = NoAST("DECLARACOES", filhos=declaracoes, linha=tok_ap.linha)
        no_corpo = NoAST("CORPO", filhos=corpo, linha=tok_ap.linha)
        return NoAST("LET", filhos=[no_decls, no_corpo], linha=tok_ap.linha)

    # Lê todas as declarações (var valor) do let até encontrar o ")".
    def binding_list(self) -> list:
        if self.token.tipo == "AP":
            decl = self.binding()
            return [decl] + self.binding_list()
        return []

    # Lê uma declaração do let no formato (variavel expressao).
    def binding(self) -> NoAST:
        tok_b_ap = self.accept("AP")
        tok_var = self.accept("ID", f"Erro Sintático na linha {self.token.linha}: Esperava-se nome de variável na declaração do 'let'.")
        expr_val = self.expr()
        self.accept("FP",
                    f"Erro Sintático na linha {self.token.linha}: Esperava-se ')' após o valor de '{tok_var.lexema}' no 'let'.",
                    linha_abertura=tok_b_ap.linha, contexto="na declaração")
        return NoAST("DECLARACAO", valor=tok_var.lexema, filhos=[expr_val], linha=tok_b_ap.linha)

    # Analisa o condicional (if condicao then else) e exige o ramo else.
    def if_expr(self, tok_ap: Token) -> NoAST:
        self.accept("PR_IF")
        condicao = self.expr()
        ramo_then = self.expr(msg_omitido=f"Erro Sintático na linha {tok_ap.linha}: Estrutura 'if' malformada. Omitido argumento de ramo 'then'.")
        ramo_else = self.expr(msg_omitido="Erro Sintático: Estrutura 'if' malformada. Omitido argumento de 'else'.")
        self.accept("FP",
                    f"Erro Sintático na linha {self.token.linha}: Esperava-se ')' após argumentos do 'if'.",
                    linha_abertura=tok_ap.linha, contexto="ao fechar 'if'")
        return NoAST("IF", filhos=[condicao, ramo_then, ramo_else], linha=tok_ap.linha)

    # Analisa o laço (while condicao corpo).
    def while_expr(self, tok_ap: Token) -> NoAST:
        self.accept("PR_WHILE")
        condicao = self.expr()
        corpo = self.expr_list()
        self.accept("FP", linha_abertura=tok_ap.linha, contexto="ao fechar 'while'")
        return NoAST("WHILE", filhos=[condicao, NoAST("CORPO", filhos=corpo, linha=tok_ap.linha)], linha=tok_ap.linha)

    # Analisa a atribuição (set variavel expressao).
    def set_expr(self, tok_ap: Token) -> NoAST:
        self.accept("PR_SET")
        tok_id = self.accept("ID", f"Erro Sintático na linha {self.token.linha}: Esperava-se identificador após 'set'.")
        valor = self.expr()
        self.accept("FP",
                    f"Erro Sintático na linha {self.token.linha}: Esperava-se ')' após atribuição de '{tok_id.lexema}'.",
                    linha_abertura=tok_ap.linha, contexto="ao fechar 'set'")
        return NoAST("SET", valor=tok_id.lexema, filhos=[valor], linha=tok_ap.linha)

    # Analisa a impressão (print expressao).
    def print_expr(self, tok_ap: Token) -> NoAST:
        linha_expr = self.token.linha
        self.accept("PR_PRINT")
        argumento = self.expr()
        self.accept("FP",
                    f"Erro Sintático na linha {self.token.linha}: Esperava-se ')' após argumento do 'print'.",
                    linha_abertura=linha_expr)
        return NoAST("PRINT", filhos=[argumento], linha=tok_ap.linha)

    # Analisa o bloco sequencial (begin expressoes).
    def begin_expr(self, tok_ap: Token) -> NoAST:
        self.accept("PR_BEGIN")
        expressoes = self.expr_list()
        self.accept("FP", linha_abertura=tok_ap.linha)
        return NoAST("BEGIN", filhos=expressoes, linha=tok_ap.linha)

    # Analisa uma lista comum e a classifica como lista vazia, operação, chamada de função ou lista genérica.
    def lista_generica(self, tok_ap: Token) -> NoAST:
 tok_ap: Token) -> NoAST:
        """
        (17) lista -> expr_list ")"        (generic_list do enunciado)
        O tipo do nó é decidido pelo primeiro elemento:
          nenhum elemento    -> LISTA_VAZIA      ()
          operador           -> OPERACAO         (+ 1 2)
          identificador      -> CHAMADA_FUNCAO   (square 5)
          qualquer outro     -> LISTA_GENERICA   (1 2 3)
        """
 tok_ap: Token) -> NoAST:
        """
        (17) lista -> expr_list ")"        (generic_list do enunciado)
        O tipo do nó é decidido pelo primeiro elemento:
          nenhum elemento    -> LISTA_VAZIA      ()
          operador           -> OPERACAO         (+ 1 2)
          identificador      -> CHAMADA_FUNCAO   (square 5)
          qualquer outro     -> LISTA_GENERICA   (1 2 3)
        """
        elementos = self.expr_list()
        self.accept("FP", linha_abertura=tok_ap.linha)

        if not elementos:
            return NoAST("LISTA_VAZIA", linha=tok_ap.linha)

        primeiro, argumentos = elementos[0], elementos[1:]
        if primeiro.tipo == "OPERADOR":
            return NoAST("OPERACAO", valor=primeiro.valor, filhos=argumentos, linha=tok_ap.linha)
        if primeiro.tipo == "ID":
            return NoAST("CHAMADA_FUNCAO", valor=primeiro.valor, filhos=argumentos, linha=tok_ap.linha)
        return NoAST("LISTA_GENERICA", filhos=elementos, linha=tok_ap.linha)
