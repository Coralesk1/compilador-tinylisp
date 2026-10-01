import sys
from pathlib import Path
from analisador_lexico import AnalisadorLexico, ErroLexico

caminho_arquivo = sys.argv[1]
arquivo_path = Path(caminho_arquivo)

try:
    if not arquivo_path.is_file():
        print(f"Erro: O arquivo '{caminho_arquivo}' nao foi encontrado.")
        sys.exit(1)

    codigo = arquivo_path.read_text(encoding="utf-8")
    #print(f"Conteudo do arquivo '{caminho_arquivo}': \n")
    #print(codigo)
except Exception as e:
    print(f"Ocorreu um erro ao abrir o arquivo: {e}")
    
try:
	lexico = AnalisadorLexico(codigo)
	for tok in lexico.tokenizar():
		print(tok)
except ErroLexico as e:
	print(e)
	sys.exit(1)