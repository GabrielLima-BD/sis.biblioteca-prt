"""
Launcher Multi-Instância - Abre múltiplas interfaces gráficas simultaneamente
Permite rodar 2, 3, 4 ou mais janelas da aplicação em paralelo
"""

import customtkinter as ctk
from subprocess import Popen
import sys
import os
from threading import Thread
import json
from datetime import datetime


class LauncherMultiInstancia:
    """Launcher para abrir múltiplas instâncias da aplicação"""
    
    def __init__(self):
        self.janela_principal = ctk.CTk()
        self.janela_principal.title("🚀 Multi-Instância - Sistema de Biblioteca")
        self.janela_principal.geometry("900x650")
        self.janela_principal.minsize(800, 500)
        
        # Cores premium
        self.cores = {
            'bg_principal': '#0a0e27',
            'bg_secundario': '#0f1937',
            'accent': '#6366f1',
            'accent_hover': '#818cf8',
            'text': '#e0e7ff',
            'verde': '#10b981',
            'vermelho': '#ef4444',
        }
        
        self.janela_principal.configure(fg_color=self.cores['bg_principal'])
        
        # Controlar instâncias
        self.instancias_ativas = []
        self.numero_instancia = 0
        
        self.criar_interface()
    
    def criar_interface(self):
        """Criar interface do launcher"""
        
        # ==================== HEADER ====================
        header = ctk.CTkFrame(self.janela_principal, fg_color=self.cores['bg_secundario'], height=120)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        titulo = ctk.CTkLabel(
            header,
            text="🚀 SISTEMA MULTI-INSTÂNCIA",
            font=("Segoe UI", 32, "bold"),
            text_color=self.cores['accent']
        )
        titulo.pack(pady=(15, 5))
        
        subtitulo = ctk.CTkLabel(
            header,
            text="Abra múltiplas interfaces gráficas em paralelo",
            font=("Segoe UI", 12),
            text_color=self.cores['accent_hover']
        )
        subtitulo.pack(pady=(0, 15))
        
        # ==================== INFORMAÇÕES ====================
        frame_info = ctk.CTkFrame(self.janela_principal, fg_color=self.cores['bg_secundario'], corner_radius=10)
        frame_info.pack(fill="x", padx=30, pady=20)
        
        info_text = ctk.CTkLabel(
            frame_info,
            text="""
ℹ️  INFORMAÇÕES:
• Cada instância aberta é independente
• Todas conectam ao mesmo servidor (localhost:3000)
• Todos os dados são compartilhados em tempo real
• Perfeito para testar múltiplos usuários
• Máximo recomendado: 4-5 instâncias
            """,
            font=("Segoe UI", 11),
            text_color=self.cores['text'],
            justify="left"
        )
        info_text.pack(padx=20, pady=15)
        
        # ==================== CONTADOR ====================
        frame_contador = ctk.CTkFrame(self.janela_principal, fg_color="transparent")
        frame_contador.pack(fill="x", padx=30, pady=10)
        
        self.label_contador = ctk.CTkLabel(
            frame_contador,
            text=f"Instâncias Ativas: 0",
            font=("Segoe UI", 14, "bold"),
            text_color=self.cores['verde']
        )
        self.label_contador.pack(side="left")
        
        # ==================== BOTÕES ====================
        frame_botoes = ctk.CTkFrame(self.janela_principal, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=30, pady=20)
        
        # Botão: Abrir Nova Instância
        btn_nova = ctk.CTkButton(
            frame_botoes,
            text="+ Abrir Nova Instância",
            command=self.abrir_nova_instancia,
            font=("Segoe UI", 14, "bold"),
            fg_color=self.cores['accent'],
            hover_color=self.cores['accent_hover'],
            height=50,
            corner_radius=10,
            text_color="white"
        )
        btn_nova.pack(fill="x", pady=10)
        
        # ==================== ATALHOS ====================
        frame_atalhos = ctk.CTkFrame(self.janela_principal, fg_color="transparent")
        frame_atalhos.pack(fill="x", padx=30, pady=5)
        
        ctk.CTkLabel(
            frame_atalhos,
            text="🎯 Atalhos Rápidos:",
            font=("Segoe UI", 12, "bold"),
            text_color=self.cores['text']
        ).pack(anchor="w")
        
        # Grid de botões rápidos
        frame_grid = ctk.CTkFrame(frame_atalhos, fg_color="transparent")
        frame_grid.pack(fill="x", pady=10)
        
        for num in [2, 3, 4]:
            btn = ctk.CTkButton(
                frame_grid,
                text=f"Abrir {num}",
                command=lambda n=num: self.abrir_n_instancias(n),
                font=("Segoe UI", 11, "bold"),
                fg_color="#8b5cf6",
                hover_color="#a78bfa",
                height=40,
                width=100,
                corner_radius=8
            )
            btn.pack(side="left", padx=5)
        
        # ==================== LISTA DE INSTÂNCIAS ====================
        frame_lista = ctk.CTkFrame(self.janela_principal, fg_color=self.cores['bg_secundario'], corner_radius=10)
        frame_lista.pack(fill="both", expand=True, padx=30, pady=(10, 20))
        
        label_lista = ctk.CTkLabel(
            frame_lista,
            text="📋 Instâncias Abertas:",
            font=("Segoe UI", 12, "bold"),
            text_color=self.cores['text']
        )
        label_lista.pack(pady=(10, 5), padx=15, anchor="w")
        
        # Text widget para mostrar instâncias
        self.text_instancias = ctk.CTkTextbox(
            frame_lista,
            fg_color=self.cores['bg_principal'],
            text_color=self.cores['text'],
            border_color=self.cores['accent'],
            border_width=2,
            corner_radius=8,
            height=150,
            font=("Courier", 10)
        )
        self.text_instancias.pack(fill="both", expand=True, padx=10, pady=10)
        self.text_instancias.configure(state="disabled")
        
        # ==================== BOTÕES DE AÇÃO ====================
        frame_acao = ctk.CTkFrame(self.janela_principal, fg_color="transparent")
        frame_acao.pack(fill="x", padx=30, pady=15)
        
        btn_atualizar = ctk.CTkButton(
            frame_acao,
            text="🔄 Atualizar Lista",
            command=self.atualizar_lista,
            font=("Segoe UI", 11, "bold"),
            fg_color="#06b6d4",
            hover_color="#22d3ee",
            height=40,
            corner_radius=8
        )
        btn_atualizar.pack(side="left", padx=5)
        
        btn_fechar_todas = ctk.CTkButton(
            frame_acao,
            text="❌ Fechar Todas",
            command=self.fechar_todas_instancias,
            font=("Segoe UI", 11, "bold"),
            fg_color=self.cores['vermelho'],
            hover_color="#f87171",
            height=40,
            corner_radius=8
        )
        btn_fechar_todas.pack(side="right", padx=5)
        
        # ==================== STATUS ====================
        frame_status = ctk.CTkFrame(self.janela_principal, fg_color=self.cores['bg_secundario'], corner_radius=10)
        frame_status.pack(fill="x", padx=30, pady=(0, 20))
        
        self.label_status = ctk.CTkLabel(
            frame_status,
            text="✅ Sistema pronto | API: http://localhost:3000",
            font=("Segoe UI", 10),
            text_color=self.cores['verde']
        )
        self.label_status.pack(pady=10)
        
        # Atualizar lista inicial
        self.atualizar_lista()
    
    def abrir_nova_instancia(self):
        """Abrir uma nova instância da aplicação"""
        self.numero_instancia += 1
        
        thread = Thread(
            target=self._iniciar_instancia,
            args=(self.numero_instancia,),
            daemon=True
        )
        thread.start()
        
        self.atualizar_lista()
    
    def abrir_n_instancias(self, n):
        """Abrir n instâncias simultaneamente"""
        for _ in range(n):
            self.abrir_nova_instancia()
    
    def _iniciar_instancia(self, numero):
        """Iniciar uma instância em thread separada"""
        try:
            caminho_app = r"c:\Users\gabel\Documents\Programação\VsCode\Prj - Grandes\sis.biblioteca-prt\Biblioteca\Python\app_melhorado.py"
            
            # Abrir nova instância
            processo = Popen(
                [sys.executable, caminho_app],
                cwd=r"c:\Users\gabel\Documents\Programação\VsCode\Prj - Grandes\sis.biblioteca-prt\Biblioteca\Python"
            )
            
            # Registrar instância
            info_instancia = {
                'numero': numero,
                'pid': processo.pid,
                'inicio': datetime.now().strftime("%H:%M:%S"),
                'processo': processo
            }
            
            self.instancias_ativas.append(info_instancia)
            
            self.label_status.configure(
                text=f"✅ Instância #{numero} aberta (PID: {processo.pid})"
            )
            
            # Aguardar encerramento
            processo.wait()
            
            # Remover quando encerrar
            self.instancias_ativas = [
                inst for inst in self.instancias_ativas 
                if inst['pid'] != processo.pid
            ]
            
            self.atualizar_lista()
            
        except Exception as e:
            self.label_status.configure(
                text=f"❌ Erro ao abrir instância: {str(e)}",
                text_color=self.cores['vermelho']
            )
    
    def atualizar_lista(self):
        """Atualizar lista de instâncias ativas"""
        self.text_instancias.configure(state="normal")
        self.text_instancias.delete("1.0", "end")
        
        if not self.instancias_ativas:
            self.text_instancias.insert("end", "Nenhuma instância aberta\n")
        else:
            self.text_instancias.insert("end", "ID  │ PID      │ Inicializada\n")
            self.text_instancias.insert("end", "────┼──────────┼──────────────\n")
            
            for inst in self.instancias_ativas:
                linha = f" #{inst['numero']:2d} │ {inst['pid']:8d} │ {inst['inicio']}\n"
                self.text_instancias.insert("end", linha)
        
        self.text_instancias.configure(state="disabled")
        
        # Atualizar contador
        total = len(self.instancias_ativas)
        cor = self.cores['verde'] if total > 0 else self.cores['text']
        self.label_contador.configure(
            text=f"Instâncias Ativas: {total}",
            text_color=cor
        )
    
    def fechar_todas_instancias(self):
        """Fechar todas as instâncias abertas"""
        if not self.instancias_ativas:
            self.label_status.configure(
                text="ℹ️  Nenhuma instância para fechar",
                text_color=self.cores['accent_hover']
            )
            return
        
        # Confirmar
        confirmacao = ctk.CTkToplevel(self.janela_principal)
        confirmacao.title("Confirmar")
        confirmacao.geometry("400x150")
        confirmacao.configure(fg_color=self.cores['bg_principal'])
        confirmacao.transient(self.janela_principal)
        confirmacao.grab_set()
        
        label = ctk.CTkLabel(
            confirmacao,
            text=f"Deseja fechar todas as {len(self.instancias_ativas)} instâncias?",
            font=("Segoe UI", 12),
            text_color=self.cores['text']
        )
        label.pack(pady=30)
        
        frame_btns = ctk.CTkFrame(confirmacao, fg_color="transparent")
        frame_btns.pack(fill="x", padx=30, pady=20)
        
        def confirmar():
            for inst in self.instancias_ativas:
                try:
                    inst['processo'].terminate()
                except:
                    pass
            
            self.instancias_ativas.clear()
            self.atualizar_lista()
            confirmacao.destroy()
            self.label_status.configure(
                text="✅ Todas as instâncias foram fechadas"
            )
        
        btn_sim = ctk.CTkButton(
            frame_btns,
            text="✓ Sim",
            command=confirmar,
            fg_color=self.cores['verde'],
            hover_color="#34d399",
            height=40,
            width=100
        )
        btn_sim.pack(side="left", padx=5)
        
        btn_nao = ctk.CTkButton(
            frame_btns,
            text="✕ Não",
            command=confirmacao.destroy,
            fg_color=self.cores['accent'],
            hover_color=self.cores['accent_hover'],
            height=40,
            width=100
        )
        btn_nao.pack(side="right", padx=5)
    
    def executar(self):
        """Executar o launcher"""
        self.janela_principal.mainloop()


if __name__ == "__main__":
    launcher = LauncherMultiInstancia()
    launcher.executar()
