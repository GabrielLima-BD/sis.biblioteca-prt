"""Executar o sistema (compatibilidade).

Este arquivo existe apenas para manter o comando antigo:

    python run_all.py

O script principal e didático agora é: executar_tudo.py
"""

from executar_tudo import GerenciadorServicos


if __name__ == "__main__":
    GerenciadorServicos().executar()


