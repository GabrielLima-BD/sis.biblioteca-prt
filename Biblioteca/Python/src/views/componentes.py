"""Componentes de interface (UI) reutilizáveis.

Este módulo concentra funções e classes de UI para a aplicação CustomTkinter,
como inputs, combobox, seletor de data, tabelas de resultados e helpers.
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
from src.utils.formatters import interpretar_data
from src.config.settings import OPERATOR_PASSWORD

# Paleta e fontes padronizadas
BACKGROUND_COLOR = "#0a0e27"
SURFACE_COLOR = "#0f1937"
CARD_COLOR = "#131829"
INPUT_COLOR = "#1e293b"
PRIMARY_COLOR = "#4f46e5"
PRIMARY_COLOR_HOVER = "#6366f1"
PRIMARY_COLOR_ALT = "#818cf8"
SUCCESS_COLOR = "#10b981"
SUCCESS_COLOR_HOVER = "#059669"
DANGER_COLOR = "#ef4444"
DANGER_COLOR_HOVER = "#dc2626"
WARNING_COLOR = "#f97316"
TEXT_PRIMARY = "#e0e7ff"
TEXT_SECONDARY = "#a5b4fc"
TEXT_MUTED = "#64748b"

FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 26, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 20, "bold")
FONT_LABEL = (FONT_FAMILY, 12, "bold")
FONT_BODY = (FONT_FAMILY, 11)
FONT_BODY_BOLD = (FONT_FAMILY, 11, "bold")


def solicitar_senha_operador(titulo: str = "Autorização necessária") -> bool:
    """Exibe diálogo centralizado pedindo a senha do operador (mascarada)."""

    resultado = {"autorizado": False}
    root = tk._default_root  # type: ignore[attr-defined]

    dialogo = ctk.CTkToplevel(root) if root else ctk.CTkToplevel()
    dialogo.title(titulo)
    dialogo.configure(fg_color=SURFACE_COLOR)
    dialogo.resizable(False, False)
    dialogo.grab_set()
    if root is not None:
        dialogo.transient(root)

    conteudo = ctk.CTkFrame(dialogo, fg_color=SURFACE_COLOR, corner_radius=12)
    conteudo.pack(fill="both", expand=True, padx=24, pady=24)

    ctk.CTkLabel(
        conteudo,
        text="Informe a senha do operador para continuar.",
        font=FONT_BODY,
        text_color=TEXT_SECONDARY,
        anchor="w"
    ).pack(fill="x", pady=(0, 16))

    entry_senha = ctk.CTkEntry(
        conteudo,
        show="*",
        font=FONT_BODY,
        fg_color=INPUT_COLOR,
        border_color=PRIMARY_COLOR,
        border_width=2,
        height=44,
        corner_radius=10,
        text_color=TEXT_PRIMARY,
        placeholder_text="Senha do operador"
    )
    entry_senha.pack(fill="x", pady=(0, 4))

    ajuda_label = ctk.CTkLabel(
        conteudo,
        text="Apenas usuários autorizados devem prosseguir.",
        font=(FONT_FAMILY, 10),
        text_color=TEXT_MUTED
    )
    ajuda_label.pack(fill="x", pady=(0, 16))

    botoes = ctk.CTkFrame(conteudo, fg_color="transparent")
    botoes.pack(fill="x")

    def confirmar():
        senha = (entry_senha.get() or "").strip()
        if senha == OPERATOR_PASSWORD:
            resultado["autorizado"] = True
            dialogo.destroy()
            return

        mostrar_mensagem_padrao("Acesso negado", "Senha incorreta", "erro")
        entry_senha.delete(0, "end")
        entry_senha.focus_set()

    def cancelar():
        dialogo.destroy()

    btn_cancelar = ctk.CTkButton(
        botoes,
        text="✕ Cancelar",
        command=cancelar,
        font=FONT_BODY_BOLD,
        fg_color=DANGER_COLOR,
        hover_color=DANGER_COLOR_HOVER,
        height=42,
        corner_radius=10
    )
    btn_cancelar.pack(side="left", expand=True, fill="x", padx=(0, 6))

    btn_confirmar = ctk.CTkButton(
        botoes,
        text="✓ Confirmar",
        command=confirmar,
        font=FONT_BODY_BOLD,
        fg_color=PRIMARY_COLOR,
        hover_color=PRIMARY_COLOR_HOVER,
        height=42,
        corner_radius=10
    )
    btn_confirmar.pack(side="right", expand=True, fill="x", padx=(6, 0))

    entry_senha.bind("<Return>", lambda _event: confirmar())
    dialogo.bind("<Escape>", lambda _event: cancelar())

    dialogo.after(50, entry_senha.focus_set)

    dialogo.update_idletasks()
    largura = dialogo.winfo_width() or 360
    altura = dialogo.winfo_height() or 200
    pos_x = (dialogo.winfo_screenwidth() // 2) - (largura // 2)
    pos_y = (dialogo.winfo_screenheight() // 2) - (altura // 2)
    dialogo.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

    dialogo.wait_window()
    return resultado["autorizado"]


def achatar_dados(dados: List[Dict]) -> List[Dict]:
    """Achata dados aninhados para exibição em tabela."""
    resultado = []
    for item in dados:
        item_flat = {}
        for chave, valor in item.items():
            if isinstance(valor, dict):
                for subchave, subvalor in valor.items():
                    item_flat[subchave] = subvalor
            else:
                item_flat[chave] = valor
        resultado.append(item_flat)
    return resultado


class TabelaResultados(ctk.CTkToplevel):
    """Tela de resultados com tabela responsiva e estilo premium."""

    def __init__(self, dados: List[Dict], colunas: List, titulo: str = "Resultados"):
        super().__init__()
        self.title(f"📊 {titulo}")
        self.geometry("1200x700")
        self.minsize(900, 500)
        
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))
        
        self.configure(fg_color=BACKGROUND_COLOR)
        
        dados_flat = achatar_dados(dados)

        # Normaliza definições de colunas para permitir rótulos e larguras customizadas
        self.colunas_config = []
        for coluna in colunas:
            if isinstance(coluna, dict):
                chave = coluna.get("key") or coluna.get("id")
                rotulo = coluna.get("label") or chave
                largura = coluna.get("width")
            elif isinstance(coluna, (list, tuple)):
                chave = coluna[0]
                rotulo = coluna[1] if len(coluna) > 1 else coluna[0]
                largura = coluna[2] if len(coluna) > 2 else None
            else:
                chave = coluna
                rotulo = coluna
                largura = None

            if not chave:
                continue

            self.colunas_config.append({
                "key": str(chave),
                "label": str(rotulo),
                "width": largura
            })

        colunas_keys = [cfg["key"] for cfg in self.colunas_config]
        
        # ==================== Header Premium ====================
        header = ctk.CTkFrame(self, fg_color=SURFACE_COLOR, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        
        inner_header = ctk.CTkFrame(header, fg_color=SURFACE_COLOR, corner_radius=0)
        inner_header.pack(fill="x", padx=20, pady=15)
        
        titulo_label = ctk.CTkLabel(
            inner_header,
            text=f"📊 {titulo}",
            font=(FONT_FAMILY, 28, "bold"),
            text_color=PRIMARY_COLOR_ALT
        )
        titulo_label.pack(anchor="w")
        
        info_label = ctk.CTkLabel(
            inner_header,
            text=f"✨ {len(dados_flat)} registros encontrados",
            font=FONT_BODY,
            text_color=TEXT_SECONDARY
        )
        info_label.pack(anchor="w", pady=(5, 0))
        
        # ==================== Frame Tabela ====================
        frame_tabela = ctk.CTkFrame(self, fg_color=BACKGROUND_COLOR)
        frame_tabela.pack(fill="both", expand=True, padx=20, pady=20)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Cores premium
        style.configure(
            "Treeview",
            background=CARD_COLOR,
            foreground=TEXT_PRIMARY,
            fieldbackground=CARD_COLOR,
            borderwidth=0,
            font=FONT_BODY,
            rowheight=48
        )
        style.configure(
            "Treeview.Heading",
            background=INPUT_COLOR,
            foreground=PRIMARY_COLOR_ALT,
            borderwidth=1,
            font=FONT_BODY_BOLD,
            padding=16
        )
        style.map(
            "Treeview",
            background=[("selected", PRIMARY_COLOR_HOVER), ("alternate", SURFACE_COLOR)],
            foreground=[("selected", "white")]
        )
        style.map(
            "Treeview.Heading",
            background=[("active", SUCCESS_COLOR)]
        )
        
        # Frame interno para scrollbars
        frame_scroll = ctk.CTkFrame(frame_tabela, fg_color="transparent")
        frame_scroll.pack(fill="both", expand=True)
        
        scroll_y = ttk.Scrollbar(frame_scroll, orient="vertical")
        scroll_y.pack(side="right", fill="y")
        
        scroll_x = ttk.Scrollbar(frame_scroll, orient="horizontal")
        scroll_x.pack(side="bottom", fill="x")
        
        self.tree = ttk.Treeview(
            frame_scroll,
            columns=colunas_keys,
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            height=20
        )
        self.tree.pack(fill="both", expand=True, side="left")
        
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        # Ajustar largura baseado na quantidade de colunas
        for cfg in self.colunas_config:
            rotulo = cfg["label"] or cfg["key"]
            largura_default = max(160, min(320, len(rotulo) * 12))
            largura = cfg["width"] or largura_default
            self.tree.heading(cfg["key"], text=rotulo)
            self.tree.column(cfg["key"], anchor="w", width=largura, minwidth=120)
        
        for idx, linha in enumerate(dados_flat):
            valores = []
            for cfg in self.colunas_config:
                valor = linha.get(cfg["key"])
                if valor is None:
                    valores.append("")
                else:
                    valores.append(str(valor)[:120])
            
            tag = "par" if idx % 2 == 0 else "impar"
            self.tree.insert("", "end", values=tuple(valores), tags=(tag,))
        
        self.tree.tag_configure("par", background=SURFACE_COLOR)
        self.tree.tag_configure("impar", background=CARD_COLOR)
        
        # ==================== Footer Premium ====================
        footer = ctk.CTkFrame(self, fg_color=SURFACE_COLOR, corner_radius=0, height=60)
        footer.pack(fill="x", padx=0, pady=0, side="bottom")
        footer.pack_propagate(False)
        
        inner_footer = ctk.CTkFrame(footer, fg_color=SURFACE_COLOR, corner_radius=0)
        inner_footer.pack(fill="both", expand=True, padx=20, pady=12)
        
        btn_fechar = ctk.CTkButton(
            inner_footer,
            text="✕ Fechar Janela",
            command=self.destroy,
            fg_color=DANGER_COLOR,
            hover_color=DANGER_COLOR_HOVER,
            font=FONT_BODY_BOLD,
            width=150,
            height=40,
            corner_radius=10
        )
        btn_fechar.pack(side="left")


def criar_frame_entrada(parent, label_texto: str, placeholder: str = "") -> ctk.CTkEntry:
    """Criar frame com label e entry estilizado com animações."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", pady=12)
    
    label = ctk.CTkLabel(
        frame,
        text=label_texto,
        font=FONT_LABEL,
        text_color=TEXT_PRIMARY
    )
    label.pack(anchor="w", padx=10, pady=(0, 6))
    
    entry = ctk.CTkEntry(
        frame,
        placeholder_text=placeholder,
        font=FONT_BODY,
        fg_color=INPUT_COLOR,
        border_color=PRIMARY_COLOR,
        border_width=2,
        height=42,
        corner_radius=10,
        text_color=TEXT_PRIMARY,
        placeholder_text_color=TEXT_MUTED
    )
    entry.pack(fill="x", padx=10, pady=5)
    
    # Animação de focus
    def on_focus_in(event):
        entry.configure(border_color=PRIMARY_COLOR_ALT)
    
    def on_focus_out(event):
        entry.configure(border_color=PRIMARY_COLOR)
    
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
    
    return entry


def criar_combobox(parent, label_texto: str, valores: List[str]) -> ctk.CTkComboBox:
    """Criar combobox com estilo premium e animações."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", pady=12)
    
    label = ctk.CTkLabel(
        frame,
        text=label_texto,
        font=FONT_LABEL,
        text_color=TEXT_PRIMARY
    )
    label.pack(anchor="w", padx=10, pady=(0, 6))
    
    combo = ctk.CTkComboBox(
        frame,
        values=valores,
        font=FONT_BODY,
        fg_color=INPUT_COLOR,
        border_color=PRIMARY_COLOR,
        button_color=PRIMARY_COLOR,
        button_hover_color=PRIMARY_COLOR_ALT,
        dropdown_fg_color=SURFACE_COLOR,
        dropdown_text_color=TEXT_PRIMARY,
        height=42,
        corner_radius=10,
        text_color=TEXT_PRIMARY,
        border_width=2
    )
    combo.pack(fill="x", padx=10, pady=5)
    
    return combo


def mostrar_mensagem_padrao(titulo: str, mensagem: str, tipo: str = "info"):
    """Mostrar mensagem estilizada com animações."""
    from tkinter import messagebox
    
    cores = {
        "sucesso": ("✅ " + titulo, mensagem, "info"),
        "erro": ("❌ " + titulo, mensagem, "error"),
        "aviso": ("⚠️ " + titulo, mensagem, "warning"),
        "info": ("ℹ️ " + titulo, mensagem, "info"),
    }
    
    if tipo in cores:
        titulo_real, msg_real, tipo_real = cores[tipo]
        if tipo_real == "error":
            messagebox.showerror(titulo_real, msg_real)
        elif tipo_real == "warning":
            messagebox.showwarning(titulo_real, msg_real)
        else:
            messagebox.showinfo(titulo_real, msg_real)


def criar_seletor_data(parent, label_texto: str) -> ctk.CTkEntry:
    """Criar seletor de data com calendário premium, animado e estilizado."""
    
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", pady=12)
    
    label = ctk.CTkLabel(
        frame,
        text=label_texto,
        font=FONT_LABEL,
        text_color=TEXT_PRIMARY
    )
    label.pack(anchor="w", padx=10, pady=(0, 6))
    
    frame_entrada = ctk.CTkFrame(frame, fg_color="transparent")
    frame_entrada.pack(fill="x", padx=10)
    
    entry = ctk.CTkEntry(
        frame_entrada,
        placeholder_text="DD/MM/AAAA",
        font=FONT_BODY,
        fg_color=INPUT_COLOR,
        border_color=PRIMARY_COLOR,
        border_width=2,
        height=42,
        corner_radius=10,
        text_color=TEXT_PRIMARY,
        placeholder_text_color=TEXT_MUTED
    )
    entry.pack(side="left", fill="x", expand=True, padx=(0, 12))
    
    def on_focus_in(event):
        entry.configure(border_color=PRIMARY_COLOR_ALT)
    
    def on_focus_out(event):
        entry.configure(border_color=PRIMARY_COLOR)
    
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
    
    def abrir_calendario():
        """Abrir janela com calendário customizado premium."""
        janela_cal = tk.Toplevel()
        janela_cal.title("📅 Selecionar Data")
        janela_cal.geometry("520x700")
        janela_cal.configure(bg=BACKGROUND_COLOR)
        janela_cal.resizable(False, False)
        
        # Animação de abertura
        janela_cal.attributes('-alpha', 0.0)
        
        def fade_in():
            alpha = janela_cal.attributes('-alpha')
            if alpha < 1.0:
                janela_cal.attributes('-alpha', alpha + 0.1)
                janela_cal.after(30, fade_in)
        
        try:
            janela_cal.iconbitmap(default='')
        except:
            pass
        
        data_atual = entry.get().strip()
        data_obj = interpretar_data(data_atual) if data_atual else None
        if data_obj:
            data_obj = data_obj.date()
        else:
            data_obj = date.today()
        
        mes_selecionado = [data_obj.year, data_obj.month]
        
        frame_main = tk.Frame(janela_cal, bg=BACKGROUND_COLOR)
        frame_main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header com gradiente visual
        frame_header = tk.Frame(frame_main, bg=SURFACE_COLOR, height=70)
        frame_header.pack(fill="x", pady=(0, 20), padx=10)
        frame_header.pack_propagate(False)
        
        def abrir_seletor_mes():
            jan_window = tk.Toplevel(janela_cal)
            jan_window.title("Selecionar Mês")
            jan_window.geometry("350x380")
            jan_window.configure(bg=BACKGROUND_COLOR)
            jan_window.resizable(False, False)
            jan_window.attributes('-alpha', 0.0)
            
            def fade_in_mes():
                alpha = jan_window.attributes('-alpha')
                if alpha < 1.0:
                    jan_window.attributes('-alpha', alpha + 0.15)
                    jan_window.after(30, fade_in_mes)
            
            meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            
            canvas_mes = tk.Canvas(jan_window, bg=BACKGROUND_COLOR, highlightthickness=0)
            scrollbar_mes = tk.Scrollbar(jan_window, orient="vertical", command=canvas_mes.yview)
            scrollable_mes = tk.Frame(canvas_mes, bg=BACKGROUND_COLOR)
            
            scrollable_mes.bind(
                "<Configure>",
                lambda e: canvas_mes.configure(scrollregion=canvas_mes.bbox("all"))
            )
            
            canvas_mes.create_window((0, 0), window=scrollable_mes, anchor="nw")
            canvas_mes.configure(yscrollcommand=scrollbar_mes.set)
            
            def _on_mousewheel_mes(event):
                canvas_mes.yview_scroll(int(-1*(event.delta/120)), "units")
            jan_window.bind("<MouseWheel>", _on_mousewheel_mes)
            
            for idx, mes_nome in enumerate(meses):
                def select_mes(m=idx+1):
                    mes_selecionado[1] = m
                    atualizar_calendario()
                    jan_window.destroy()
                
                bg_cor = SUCCESS_COLOR if mes_selecionado[1] == idx + 1 else PRIMARY_COLOR
                btn = tk.Button(
                    scrollable_mes,
                    text=mes_nome,
                    command=select_mes,
                    bg=bg_cor,
                    fg="white",
                    font=FONT_BODY_BOLD,
                    relief="flat",
                    padx=15,
                    pady=14,
                    cursor="hand2",
                    activebackground=PRIMARY_COLOR_ALT,
                    activeforeground="white",
                    width=28,
                    bd=0,
                    highlightthickness=0
                )
                btn.pack(pady=4, fill="x")
                
                def on_enter(e, b=btn):
                    b.configure(bg=PRIMARY_COLOR_ALT)
                
                def on_leave(e, b=btn, original_color=bg_cor):
                    b.configure(bg=original_color)
                
                btn.bind("<Enter>", on_enter)
                btn.bind("<Leave>", on_leave)
            
            canvas_mes.pack(side="left", fill="both", expand=True)
            scrollbar_mes.pack(side="right", fill="y")
            
            janela_cal.after(100, fade_in_mes)
        
        def abrir_seletor_ano():
            ano_window = tk.Toplevel(janela_cal)
            ano_window.title("Selecionar Ano")
            ano_window.geometry("350x450")
            ano_window.configure(bg=BACKGROUND_COLOR)
            ano_window.resizable(False, False)
            ano_window.attributes('-alpha', 0.0)
            
            def fade_in_ano():
                alpha = ano_window.attributes('-alpha')
                if alpha < 1.0:
                    ano_window.attributes('-alpha', alpha + 0.15)
                    ano_window.after(30, fade_in_ano)
            
            canvas_ano = tk.Canvas(ano_window, bg=BACKGROUND_COLOR, highlightthickness=0)
            scrollbar_ano = tk.Scrollbar(ano_window, orient="vertical", command=canvas_ano.yview)
            scrollable_ano = tk.Frame(canvas_ano, bg=BACKGROUND_COLOR)
            
            scrollable_ano.bind(
                "<Configure>",
                lambda e: canvas_ano.configure(scrollregion=canvas_ano.bbox("all"))
            )
            
            canvas_ano.create_window((0, 0), window=scrollable_ano, anchor="nw")
            canvas_ano.configure(yscrollcommand=scrollbar_ano.set)
            
            def _on_mousewheel_ano(event):
                canvas_ano.yview_scroll(int(-1*(event.delta/120)), "units")
            ano_window.bind("<MouseWheel>", _on_mousewheel_ano)
            
            anos_range = range(1950, 2051)
            for ano in anos_range:
                def select_ano(a=ano):
                    mes_selecionado[0] = a
                    atualizar_calendario()
                    ano_window.destroy()
                
                bg_cor = SUCCESS_COLOR if mes_selecionado[0] == ano else PRIMARY_COLOR
                btn = tk.Button(
                    scrollable_ano,
                    text=str(ano),
                    command=select_ano,
                    bg=bg_cor,
                    fg="white",
                    font=FONT_BODY_BOLD,
                    relief="flat",
                    padx=10,
                    pady=10,
                    cursor="hand2",
                    activebackground=PRIMARY_COLOR_ALT,
                    activeforeground="white",
                    width=20,
                    bd=0,
                    highlightthickness=0
                )
                btn.pack(pady=2, fill="x")
                
                def on_enter_ano(e, b=btn):
                    b.configure(bg=PRIMARY_COLOR_ALT)
                
                def on_leave_ano(e, b=btn, original_color=bg_cor):
                    b.configure(bg=original_color)
                
                btn.bind("<Enter>", on_enter_ano)
                btn.bind("<Leave>", on_leave_ano)
            
            canvas_ano.pack(side="left", fill="both", expand=True)
            scrollbar_ano.pack(side="right", fill="y")
            
            janela_cal.after(100, fade_in_ano)
        
        btn_mes = tk.Button(
            frame_header,
            text="",
            command=abrir_seletor_mes,
            bg=SURFACE_COLOR,
            fg=PRIMARY_COLOR_ALT,
            font=(FONT_FAMILY, 15, "bold"),
            relief="flat",
            padx=20,
            pady=12,
            cursor="hand2",
            activebackground=INPUT_COLOR,
            activeforeground=PRIMARY_COLOR_ALT,
            bd=0,
            highlightthickness=0,
            width=15
        )
        btn_mes.pack(side="left", padx=8, fill="both", expand=True)
        
        btn_ano = tk.Button(
            frame_header,
            text="",
            command=abrir_seletor_ano,
            bg=SURFACE_COLOR,
            fg=PRIMARY_COLOR_ALT,
            font=(FONT_FAMILY, 15, "bold"),
            relief="flat",
            padx=20,
            pady=12,
            cursor="hand2",
            activebackground=INPUT_COLOR,
            activeforeground=PRIMARY_COLOR_ALT,
            bd=0,
            highlightthickness=0,
            width=8
        )
        btn_ano.pack(side="right", padx=8, fill="both", expand=True)
        
        frame_nav = tk.Frame(frame_main, bg=BACKGROUND_COLOR)
        frame_nav.pack(fill="x", pady=(0, 20))
        
        def mudar_mes(direcao):
            mes_selecionado[1] += direcao
            if mes_selecionado[1] > 12:
                mes_selecionado[1] = 1
                mes_selecionado[0] += 1
            elif mes_selecionado[1] < 1:
                mes_selecionado[1] = 12
                mes_selecionado[0] -= 1
            
            atualizar_calendario()
        
        btn_prev = tk.Button(
            frame_nav,
            text="◀  Anterior",
            command=lambda: mudar_mes(-1),
            bg=PRIMARY_COLOR,
            fg="white",
            font=FONT_BODY_BOLD,
            relief="flat",
            padx=14,
            pady=10,
            cursor="hand2",
            activebackground=PRIMARY_COLOR_ALT,
            activeforeground="white",
            bd=0,
            highlightthickness=0
        )
        btn_prev.pack(side="left", padx=6)
        
        btn_next = tk.Button(
            frame_nav,
            text="Próximo  ▶",
            command=lambda: mudar_mes(1),
            bg=PRIMARY_COLOR,
            fg="white",
            font=FONT_BODY_BOLD,
            relief="flat",
            padx=14,
            pady=10,
            cursor="hand2",
            activebackground=PRIMARY_COLOR_ALT,
            activeforeground="white",
            bd=0,
            highlightthickness=0
        )
        btn_next.pack(side="right", padx=6)
        
        frame_cal = tk.Frame(frame_main, bg=BACKGROUND_COLOR)
        frame_cal.pack(fill="both", expand=True, padx=10)
        
        dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sab", "Dom"]
        for col, dia in enumerate(dias_semana):
            lbl = tk.Label(
                frame_cal,
                text=dia,
                font=FONT_BODY_BOLD,
                bg=SURFACE_COLOR,
                fg=PRIMARY_COLOR_ALT,
                width=7,
                height=2,
                relief="flat",
                pady=8
            )
            lbl.grid(row=0, column=col, padx=3, pady=4, sticky="nsew")
        
        botoes_dias = {}
        
        def atualizar_calendario():
            meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            btn_mes.config(text=f"{meses[mes_selecionado[1]-1]}")
            btn_ano.config(text=str(mes_selecionado[0]))
            
            for btn in botoes_dias.values():
                btn.destroy()
            botoes_dias.clear()
            
            primeiro_dia = date(mes_selecionado[0], mes_selecionado[1], 1)
            dia_semana_primeiro = primeiro_dia.weekday()
            
            if mes_selecionado[1] == 12:
                ultimo_dia = date(mes_selecionado[0] + 1, 1, 1) - timedelta(days=1)
            else:
                ultimo_dia = date(mes_selecionado[0], mes_selecionado[1] + 1, 1) - timedelta(days=1)
            
            num_dias = ultimo_dia.day
            
            linha = 1
            coluna = dia_semana_primeiro
            
            for dia in range(1, num_dias + 1):
                if coluna >= 7:
                    coluna = 0
                    linha += 1
                
                data_btn = date(mes_selecionado[0], mes_selecionado[1], dia)
                if data_btn == data_obj:
                    bg_cor = SUCCESS_COLOR
                    fg_cor = "white"
                elif data_btn == date.today():
                    bg_cor = PRIMARY_COLOR
                    fg_cor = "white"
                else:
                    bg_cor = INPUT_COLOR
                    fg_cor = TEXT_PRIMARY
                
                def selecionar(d=dia):
                    data_selecionada = date(mes_selecionado[0], mes_selecionado[1], d)
                    entry.delete(0, "end")
                    entry.insert(0, data_selecionada.strftime("%d/%m/%Y"))
                    janela_cal.destroy()
                
                btn = tk.Button(
                    frame_cal,
                    text=str(dia),
                    command=selecionar,
                    bg=bg_cor,
                    fg=fg_cor,
                    font=FONT_BODY_BOLD,
                    width=7,
                    height=2,
                    relief="flat",
                    cursor="hand2",
                    activebackground=PRIMARY_COLOR_ALT,
                    activeforeground="white",
                    bd=0,
                    highlightthickness=0
                )
                btn.grid(row=linha, column=coluna, padx=3, pady=3, sticky="nsew")
                botoes_dias[dia] = btn
                
                def on_enter_dia(e, b=btn):
                    if b.cget("bg") != SUCCESS_COLOR:
                        b.configure(bg=PRIMARY_COLOR_ALT)
                
                def on_leave_dia(e, b=btn, original_color=bg_cor):
                    if original_color != SUCCESS_COLOR:
                        b.configure(bg=original_color)
                
                btn.bind("<Enter>", on_enter_dia)
                btn.bind("<Leave>", on_leave_dia)
                
                coluna += 1
            
            for i in range(7):
                frame_cal.grid_columnconfigure(i, weight=1)
        
        atualizar_calendario()
        
        frame_buttons = tk.Frame(frame_main, bg=BACKGROUND_COLOR)
        frame_buttons.pack(fill="x", pady=(15, 0))
        
        btn_hoje = tk.Button(
            frame_buttons,
            text="📅 Hoje",
            command=lambda: (entry.delete(0, "end"), entry.insert(0, date.today().strftime("%d/%m/%Y")), janela_cal.destroy()),
            bg=SUCCESS_COLOR,
            fg="white",
            font=FONT_BODY_BOLD,
            relief="flat",
            padx=18,
            pady=11,
            cursor="hand2",
            activebackground=SUCCESS_COLOR_HOVER,
            activeforeground="white",
            bd=0,
            highlightthickness=0
        )
        btn_hoje.pack(fill="x", pady=6)
        
        btn_cancelar = tk.Button(
            frame_buttons,
            text="✕ Cancelar",
            command=janela_cal.destroy,
            bg=DANGER_COLOR,
            fg="white",
            font=FONT_BODY_BOLD,
            relief="flat",
            padx=18,
            pady=11,
            cursor="hand2",
            activebackground=DANGER_COLOR_HOVER,
            activeforeground="white",
            bd=0,
            highlightthickness=0
        )
        btn_cancelar.pack(fill="x", pady=6)
        
        janela_cal.after(100, fade_in)
    
    btn_calendario = ctk.CTkButton(
        frame_entrada,
        text="📅",
        command=abrir_calendario,
        fg_color=PRIMARY_COLOR,
        hover_color=PRIMARY_COLOR_ALT,
        font=(FONT_FAMILY, 16, "bold"),
        width=55,
        height=42,
        corner_radius=10
    )
    btn_calendario.pack(side="right")
    
    return entry


# ==================== Componentes Reutilizáveis de Layout ====================

def criar_header_padrao(parent, titulo: str, icone: str, callback_voltar, altura: int = 90):
    """Cria header padronizado com botão voltar e título."""
    header = ctk.CTkFrame(parent, fg_color=SURFACE_COLOR, height=altura)
    header.pack(fill="x", padx=0, pady=0)
    header.pack_propagate(False)
    
    top_frame = ctk.CTkFrame(header, fg_color=SURFACE_COLOR)
    top_frame.pack(fill="x", padx=20, pady=10)
    
    btn_voltar = ctk.CTkButton(
        top_frame,
        text="⬅️ Voltar",
        command=callback_voltar,
        font=FONT_BODY,
        fg_color="transparent",
        hover_color=INPUT_COLOR,
        text_color=PRIMARY_COLOR_ALT,
        width=100,
        height=35
    )
    btn_voltar.pack(side="left")
    
    titulo_label = ctk.CTkLabel(
        header,
        text=f"{icone} {titulo}",
        font=FONT_TITLE,
        text_color=PRIMARY_COLOR_ALT
    )
    titulo_label.pack(pady=(0, 10))
    
    return header


def criar_container_scroll(parent, padx: int = 30, pady: int = 20):
    """Cria container com scroll padronizado."""
    container = ctk.CTkScrollableFrame(
        parent,
        fg_color=BACKGROUND_COLOR,
        scrollbar_button_color=PRIMARY_COLOR,
        scrollbar_button_hover_color=PRIMARY_COLOR_ALT
    )
    container.pack(fill="both", expand=True, padx=padx, pady=pady)
    return container


def criar_container_simples(parent, padx: int = 30, pady: int = 20):
    """Cria container simples padronizado (sem scroll)."""
    container = ctk.CTkFrame(parent, fg_color=BACKGROUND_COLOR)
    container.pack(fill="both", expand=True, padx=padx, pady=pady)
    return container


def criar_busca_entidade(parent, label_inicial: str, cor_nao_encontrado: str = TEXT_MUTED, cor_encontrado: str = SUCCESS_COLOR, cor_erro: str = DANGER_COLOR):
    """Cria frame de status para busca de entidade (cliente, livro, etc)."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", pady=10)
    
    label = ctk.CTkLabel(
        frame,
        text=label_inicial,
        font=FONT_BODY,
        text_color=cor_nao_encontrado
    )
    label.pack(side="left", padx=10)
    
    def atualizar_label(texto: str, status: str = "nao_encontrado"):
        cores = {
            "nao_encontrado": cor_nao_encontrado,
            "encontrado": cor_encontrado,
            "erro": cor_erro
        }
        label.configure(text=texto, text_color=cores.get(status, cor_nao_encontrado))
    
    return label, atualizar_label, frame


def criar_botoes_acao(parent, texto_confirmar: str, callback_confirmar, callback_cancelar, icone_confirmar: str = "✓", icone_cancelar: str = "✕"):
    """Cria frame com botões de confirmar e cancelar padronizados."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", pady=30)
    
    btn_confirmar = ctk.CTkButton(
        frame,
        text=f"{icone_confirmar} {texto_confirmar}",
        command=callback_confirmar,
        font=(FONT_FAMILY, 13, "bold"),
        fg_color=SUCCESS_COLOR,
        hover_color=SUCCESS_COLOR_HOVER,
        height=45,
        corner_radius=10,
        text_color=TEXT_PRIMARY
    )
    btn_confirmar.pack(side="left", expand=True, fill="x", padx=(0, 10))
    
    btn_cancelar = ctk.CTkButton(
        frame,
        text=f"{icone_cancelar} Cancelar",
        command=callback_cancelar,
        font=(FONT_FAMILY, 13, "bold"),
        fg_color=DANGER_COLOR,
        hover_color=DANGER_COLOR_HOVER,
        height=45,
        corner_radius=10,
        text_color=TEXT_PRIMARY
    )
    btn_cancelar.pack(side="right", expand=True, fill="x", padx=(10, 0))
    
    return frame


def limpar_frame(frame):
    """Remove todos os widgets de um frame."""
    for widget in frame.winfo_children():
        widget.destroy()


def criar_frame_info(parent, texto_inicial: str, icone: str = "ℹ️"):
    """Cria frame de informação com estilo padronizado."""
    frame = ctk.CTkFrame(parent, fg_color=SURFACE_COLOR, corner_radius=10)
    frame.pack(fill="x", pady=20, padx=10)
    
    label = ctk.CTkLabel(
        frame,
        text=f"{icone} {texto_inicial}",
        font=FONT_BODY,
        text_color=TEXT_MUTED,
        wraplength=600
    )
    label.pack(pady=20, padx=20)
    
    return frame, label
