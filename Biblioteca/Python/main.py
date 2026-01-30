#!/usr/bin/env python3
"""
Sistema de Biblioteca - Ponto de entrada principal
Versão: 2.0 com arquitetura modularizada
"""

import os
import sys
import logging
from pathlib import Path

# Configurar paths
PROJETO_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJETO_ROOT))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('biblioteca.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def iniciar_aplicacao():
    """Inicia a aplicação de biblioteca"""
    try:
        logger.info("Iniciando aplicação de biblioteca...")

        # Importar após setup de paths
        from app import main as iniciar_gui

        logger.info("Iniciando GUI (app)...")
        iniciar_gui()
        
        logger.info("Aplicação finalizada com sucesso")
        
    except ImportError as e:
        logger.error(f"Erro ao importar módulos: {e}")
        print(f"❌ Erro ao carregar módulos: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Erro durante execução: {e}", exc_info=True)
        print(f"❌ Erro na aplicação: {e}")
        sys.exit(1)


if __name__ == "__main__":
    iniciar_aplicacao()
