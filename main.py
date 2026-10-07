import sys
from pathlib import Path
from analisador_lexico import AnalisadorLexico, ErroLexico
from analisador_sintatico import AnalisadorSintatico, ErroSintatico


def main(argc, argv):
    if len(sys.argv) < 2:
        print("Uso: python main.py <arquivo.lsp>")
        sys.exit(1)

    caminho_arquivo = sys.argv[1]
    arquivo_path = Path(caminho_arquivo)

    try:
        if not arquivo_path.is_file():
            print(f"Erro: O arquivo '{caminho_arquivo}' nao foi encontrado.")
            sys.exit(1)

        codigo = arquivo_path.read_text(encoding="utf-8")
        # print(f"Conteudo do arquivo '{caminho_arquivo}':) \n"
        # print(codigo)
    except Exception as e:
        print(f"Ocorreu um erro ao abrir o arquivo: {e}")

    try:
        #Analizador Léxico
        lexico = AnalisadorLexico(codigo)
        tokens = lexico.tokenizar()
        
        for tok in tokens:
            print(tok)

        sintatico = AnalisadorSintatico(tokens)
        ast = sintatico.parse()
        ast.exibir()
        print("\nAnálise Sintática realizada com sucesso!")


    except ErroLexico as e:
        print(e)
        sys.exit(1)
    except ErroSintatico as e:
        print(e)
        sys.exit()


if __name__ == "__main__":
    main(len(sys.argv), sys.argv)