import sys
from tokens import Token
from pathlib import Path

caminho_arquivo = sys.argv[1]


try:
    arquivo_path = Path(caminho_arquivo)

    if not arquivo_path.is_file():
        print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado.")
        sys.exit(1)

    conteudo = arquivo_path.read_text(encoding="utf-8")
    print(f"Conteúdo do arquivo '{caminho_arquivo}': \n")
    print(conteudo)

except Exception as e:
    print(f"Ocorreu um erro ao abrir o arquivo: {e}")