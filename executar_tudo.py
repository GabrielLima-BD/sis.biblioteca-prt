"""Executar o Sistema de Biblioteca (API + App).

Este script inicia, em paralelo:
- A API Node/Express (Biblioteca/API/server.js)
- A interface gráfica Python (Biblioteca/Python/app.py)

Uso:
    python executar_tudo.py
"""

import subprocess
import sys
import time
from pathlib import Path
from threading import Thread

import requests


class GerenciadorServicos:
    """Gerencia múltiplos processos (API + App) em paralelo."""
    
    def __init__(self):
        self.processos = []
        self.ativo = True
    
    def verificar_api(self, max_tentativas=30, intervalo=1):
        """Verifica se a API está respondendo"""
        for tentativa in range(max_tentativas):
            try:
                resposta = requests.get('http://localhost:3000/health', timeout=2)
                if resposta.status_code == 200:
                    print("✅ API está respondendo!")
                    return True
            except:
                pass
            
            print(f"⏳ Aguardando API... ({tentativa + 1}/{max_tentativas})")
            time.sleep(intervalo)
        
        print("❌ API não respondeu no tempo esperado")
        return False
    
    def iniciar_api(self):
        """Inicia o servidor Node.js da API"""
        print("\n🚀 Iniciando API (Node.js)...")
        try:
            projeto_root = Path(__file__).resolve().parent
            caminho_api = str(projeto_root / "Biblioteca" / "API")
            
            # Rodar direto com node
            processo = subprocess.Popen(
                ["node", "server.js"],
                cwd=caminho_api,
                shell=False
            )
            
            self.processos.append(('API', processo))
            print("✅ Processo da API iniciado")
            
        except Exception as e:
            print(f"❌ Erro ao iniciar API: {e}")
    
    def iniciar_app(self):
        """Inicia a aplicação Python"""
        print("\n🎨 Iniciando App Python...")
        
        try:
            projeto_root = Path(__file__).resolve().parent
            caminho_app = str(projeto_root / "Biblioteca" / "Python")
            
            processo = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=caminho_app,
                shell=False
            )
            
            self.processos.append(('App', processo))
            print("✅ App iniciado!")
            
        except Exception as e:
            print(f"❌ Erro ao iniciar App: {e}")
    
    def executar(self):
        """Executar ambos os serviços"""
        print("=" * 70)
        print("🚀 INICIANDO SISTEMA DE BIBLIOTECA")
        print("=" * 70)
        
        # Iniciar API primeiro
        thread_api = Thread(target=self.iniciar_api, daemon=False)
        thread_api.start()
        thread_api.join()  # Aguardar que o processo foi criado
        
        # Verificar se API está pronta
        print("\n📡 Verificando conexão com API...")
        if not self.verificar_api():
            print("\n⚠️  API não respondeu! Verifique se Node.js está instalado.")
            return
        
        # Iniciar App
        self.iniciar_app()
        
        print("\n" + "=" * 70)
        print("✅ AMBOS OS SERVIÇOS ESTÃO RODANDO!")
        print("=" * 70)
        print("\n📌 INFORMAÇÕES:")
        print("   🔗 API: http://localhost:3000")
        print("   🎨 App: Interface gráfica principal")
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Aguarde a janela principal abrir")
        print("   2. Use o menu para navegar entre as funcionalidades")
        print("\n⚠️  Pressione Ctrl+C para encerrar tudo")
        print("=" * 70 + "\n")
        
        try:
            while self.ativo:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⛔ Encerrando todos os serviços...")
            self.ativo = False
            for nome, processo in self.processos:
                try:
                    processo.terminate()
                    print(f"   ✓ {nome} encerrado")
                except:
                    pass
            print("\n✅ Todos os serviços foram encerrados!")


if __name__ == "__main__":
    gerenciador = GerenciadorServicos()
    gerenciador.executar()


