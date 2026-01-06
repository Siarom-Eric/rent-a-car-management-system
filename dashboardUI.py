import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, Toplevel, Checkbutton, BooleanVar, Frame
import sqlite3
from tkcalendar import DateEntry
import datetime
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class DashboardUI:
    def __init__(self, root, data_manager):
        self.root = root
        self.data_manager = data_manager

        # Configurar a janela para maximizar
        self.root.state('zoomed')

        # Variável para opções de busca
        self.opcao_busca = tk.StringVar()
        self.valor_busca_entry = tk.Entry(self.root, textvariable=self.opcao_busca)
        self.opcao_busca.set("")

        self.data_manager.atualizar_disponibilidade_todos()

        self.create_dashboard()

        # Variáveis de controle para a interface
        self.novo_cliente_var = tk.BooleanVar(value=True)
        self.lista_veiculo_selecionado = tk.StringVar()
        self.categoria_var = tk.StringVar()
        self.novo_cliente_frame = None
        self.existente_cliente_frame = None

    """Criação do Dashboard"""
    def create_main_layout(self):
        """ Cria o layout principal com canvas e scrollbars. """
        self.canvas = tk.Canvas(self.root)
        self.scroll_y = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scroll_x = tk.Scrollbar(self.root, orient="horizontal", command=self.canvas.xview)
        self.frame = tk.Frame(self.canvas)

        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        self.scroll_y.pack(side="right", fill="y")
        self.scroll_x.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Para redimensionar o canvas conforme a janela for ajustada
        self.root.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        """ Ajusta o tamanho do canvas ao redimensionar a janela. """
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def create_dashboard(self):
        """ Configura o layout principal e cria botões de gestão. """
        self.create_main_layout()

        # Frame principal do dashboard
        self.frame_dashboard = tk.Frame(self.frame)
        self.frame_dashboard.pack(padx=10, pady=10, fill="both", expand=True)

        self.frame_dashboard.grid_columnconfigure(0, weight=1)
        self.frame_dashboard.grid_rowconfigure(0, weight=1)
        self.frame_dashboard.grid_rowconfigure(1, weight=0)
        self.frame_dashboard.grid_rowconfigure(2, weight=1)

        # Frame para exibir informações no dashboard
        self.frame_info = tk.Frame(self.frame_dashboard, height=100, bg="lightgray")
        self.frame_info.grid(row=0, column=0, sticky="ew", pady=10)
        self.frame_info.grid_columnconfigure(0, weight=1)

        # Frame para botões de gerenciamento
        self.frame_buttons = tk.Frame(self.frame_dashboard)
        self.frame_buttons.grid(row=1, column=0, sticky="ew", pady=10)
        self.frame_buttons.grid_columnconfigure(0, weight=1)

        # Preenche Dashboard com informações
        self.preencher_informacoes_dashboard()
        # Cria os botões de gerenciamento
        self.expanded_frames = {}
        self.create_buttons()

    def preencher_informacoes_dashboard(self):
        """ Preenche a área do dashboard com informações atualizadas. """
        for widget in self.frame_info.winfo_children():
            widget.destroy()

        # Configurar a expansão do frame principal
        self.frame_info.grid_columnconfigure(0, weight=1)
        self.frame_info.grid_rowconfigure(0, weight=1)

        # Criação das seções do dashboard
        left_frame = tk.Frame(self.frame_info)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        mid_frame = tk.Frame(self.frame_info)
        mid_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        right_frame = tk.Frame(self.frame_info)
        right_frame.grid(row=0, column=3, padx=10, pady=10, sticky="nsew")

        self.frame_info.grid_columnconfigure(0, weight=1)
        self.frame_info.grid_columnconfigure(1, weight=1)
        self.frame_info.grid_rowconfigure(0, weight=1)

        hoje = datetime.today().date()

        # Consultas ao banco de dados via DataManager
        veiculos_alugados = self.data_manager.get_veiculos_alugados(hoje)
        ultimos_clientes = self.data_manager.get_ultimos_clientes()
        veiculos_revisao = self.data_manager.get_veiculos_revisao(hoje)
        veiculos_inspecao = self.data_manager.get_veiculos_inspecao(hoje)

        # Dados para gráficos
        veiculos_disponiveis_categoria = self.data_manager.get_veiculos_disponiveis_categoria()
        veiculos_disponiveis_tipo = self.data_manager.get_veiculos_disponiveis_tipo()

        # Gráficos à esquerda
        self.criar_graficos(left_frame, veiculos_disponiveis_categoria, veiculos_disponiveis_tipo, mid_frame)

        # Exibir seções à direita
        self.display_section("Veículos Alugados:", [f"{marca} {modelo} - {dias_restantes:.0f} dias restantes" for
                                                    marca, modelo, dias_restantes in veiculos_alugados],
                             right_frame)
        self.display_section("Últimos Clientes Registrados:", [f"{nome} - {email}" for nome, email in ultimos_clientes],
                             right_frame)
        self.display_section("Veículos com Revisão Hoje:",
                             [f"{marca} {modelo} - {proxima_revisao}" for marca, modelo, proxima_revisao in
                              veiculos_revisao],
                             right_frame)
        self.display_section("Veículos com Inspeção Hoje:",
                             [f"{marca} {modelo} - {proxima_inspecao}" for marca, modelo, proxima_inspecao in
                              veiculos_inspecao],
                             right_frame)

        # Mostrar alertas
        self.show_alertas_revisao(veiculos_revisao)
        self.show_alertas_inspecao(veiculos_inspecao)

        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def criar_graficos(self, frame, veiculos_disponiveis_categoria, veiculos_disponiveis_tipo, mid_frame):
        """ Cria gráficos de pizza e gráfico de barras. """

        # Gráfico de Pizza por Tipo de Veículos
        tipos_veiculos, quantidades_tipos = zip(*veiculos_disponiveis_tipo)  # Desempacotar dados

        fig1 = Figure(figsize=(5, 3), dpi=100)
        ax1 = fig1.add_subplot(111)
        ax1.pie(quantidades_tipos, labels=tipos_veiculos, autopct='%1.1f%%')
        ax1.set_title('Número de veículos disponíveis por Tipo')

        canvas1 = FigureCanvasTkAgg(fig1, master=frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Gráfico de Pizza por Categoria de Veículos
        categorias_veiculos, quantidades_categorias = zip(*veiculos_disponiveis_categoria)  # Desempacotar dados

        fig2 = Figure(figsize=(5, 3), dpi=100)
        ax2 = fig2.add_subplot(111)
        ax2.pie(quantidades_categorias, labels=categorias_veiculos, autopct='%1.1f%%')
        ax2.set_title('Número de veículos disponíveis por Categoria')

        canvas2 = FigureCanvasTkAgg(fig2, master=frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Gráfico de Barras para Lucro Total dos Últimos 6 Meses
        lucros = self.data_manager.get_lucro_ultimos_seis_meses()

        # Listas separadas para meses e valores de lucro
        meses = list(lucros.keys())  # Obtemos os meses diretamente do dicionário
        valores_lucro = list(lucros.values())  # Obtemos os valores de lucro diretamente do dicionário

        fig3 = Figure(figsize=(7, 5), dpi=100)
        ax3 = fig3.add_subplot(111)
        ax3.bar(meses, valores_lucro, color='blue')
        ax3.set_title('Lucro Total nos Últimos 6 Meses')
        ax3.set_ylabel('Lucro (€)')

        canvas3 = FigureCanvasTkAgg(fig3, master=mid_frame)
        canvas3.draw()
        canvas3.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def show_alertas_revisao(self, revisoes):
        if revisoes:
            msg = "\n".join(revisoes)
            messagebox.showwarning("Alertas de Revisão Próxima", f"Os seguintes veículos precisam de revisão:\n\n{msg}")

    def show_alertas_inspecao(self, inspecoes):
        if inspecoes:
            msg = "\n".join(inspecoes)
            messagebox.showwarning("Alertas de Inspeção Próxima",
                                   f"Os seguintes veículos precisam de inspeção:\n\n{msg}")

    def display_section(self, title, items, frame):
        """ Exibe uma seção no dashboard com um título e uma lista de itens. """
        tk.Label(frame, text=title, font=('Arial', 12, 'bold')).pack(anchor='w', pady=5)
        for item in items:
            tk.Label(frame, text=item).pack(anchor='w')

    def create_buttons(self):
        """ Cria os botões de gestão e adiciona ao layout. """
        categories = [
            ("Gerir Veículos", "veiculos"),
            ("Gerir Clientes", "clientes"),
            ("Gerir Reservas", "reservas"),
            ("Gerir Formas de Pagamento", "formas de pagamento"),
            ("Exportar Dados", self.exportar_dados),
            ("Atualizar", self.preencher_informacoes_dashboard)
        ]

        # Configurar as colunas da grid para ajustar corretamente
        for i in range(len(categories)):
            self.frame_buttons.grid_columnconfigure(i, weight=1)

        # Criar e posicionar os botões
        for i, (text, command) in enumerate(categories):
            if callable(command):  # Se for exportar_dados
                btn = tk.Button(self.frame_buttons, text=text, command=command)
            else:  # Se for uma categoria, definir ação para exibir as opções
                btn = tk.Button(self.frame_buttons, text=text,
                                command=lambda c=command: self.toggle_opcoes(c))
            btn.grid(row=0, column=i, sticky="ew", padx=10, pady=5)

    def toggle_opcoes(self, categoria):
        """ Exibe ou oculta as opções de gerir para a categoria especificada. """
        # Fechar todos os outros frames de opções
        for cat in list(self.expanded_frames.keys()):
            if cat != categoria:
                self.expanded_frames[cat].grid_forget()
                del self.expanded_frames[cat]

        # Verificar se o frame já está mostrado; caso contrário, removê-lo
        if categoria in self.expanded_frames:
            self.expanded_frames[categoria].grid_forget()
            del self.expanded_frames[categoria]
        else:
            # Criar e exibir o frame de opções
            frame_opcoes_categoria = self.create_opcoes_frame(categoria)
            # Posicionar o frame diretamente abaixo dos botões
            frame_opcoes_categoria.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))
            self.expanded_frames[categoria] = frame_opcoes_categoria

    def create_opcoes_frame(self, categoria):
        """ Cria o frame com botões de opções para a categoria especificada. """
        frame_opcoes_categoria = tk.Frame(self.frame_dashboard)

        if categoria == "veiculos":
            options = [
                ("Adicionar Veículo", self.open_adicionar_veiculo),
                ("Listar Veículos", self.listar_veiculos_interface),
                ("Buscar Veículo", self.open_busca_veiculo)
            ]
        elif categoria == "clientes":
            options = [
                ("Adicionar Cliente", self.open_adicionar_cliente),
                ("Listar Clientes", self.listar_clientes_interface),
                ("Buscar Cliente", self.open_busca_cliente)
            ]
        elif categoria == "reservas":
            options = [
                ("Adicionar Reservas", self.open_adicionar_reserva),
                ("Listar Reservas", self.listar_reservas_interface),
                ("Buscar Reservas", self.open_busca_reserva)
            ]
        elif categoria == "formas de pagamento":
            options = [
                ("Adicionar Formas de Pagamento", self.open_adicionar_forma_pagamento),
                ("Listar Formas de Pagamento", self.listar_formas_pagamento_interface),
                ("Buscar Formas de Pagamento", self.open_buscar_forma_pagamento)
            ]

        for i, (option_text, command) in enumerate(options):
            btn = tk.Button(frame_opcoes_categoria, text=option_text, command=command)
            btn.grid(row=i, column=0, sticky="ew", padx=20, pady=2)

        return frame_opcoes_categoria

# region Exportar Dados
    def exportar_dados(self):
        """ Secção de exportar dados em Excel ou CSV"""
        def escolher_seccoes():
            escolha = Toplevel(self.root)
            escolha.title("Escolher Seções para Exportar")

            seccoes_disponiveis = {
                'Veículos': BooleanVar(),
                'Clientes': BooleanVar(),
                'Reservas': BooleanVar(),
                'Formas de Pagamento': BooleanVar()
            }

            for i, (seccao, var) in enumerate(seccoes_disponiveis.items()):
                Checkbutton(escolha, text=seccao, variable=var).grid(row=i, sticky="w")

            def confirmar():
                seccoes_escolhidas = [seccao for seccao, var in seccoes_disponiveis.items() if var.get()]
                if seccoes_escolhidas:
                    escolha.destroy()
                    escolher_formato(seccoes_escolhidas)
                else:
                    messagebox.showwarning("Nenhuma Seção Selecionada",
                                           "Por favor, selecione pelo menos uma seção para exportar.")

            tk.Button(escolha, text="Confirmar", command=confirmar).grid(row=len(seccoes_disponiveis), pady=10)

        def escolher_formato(seccoes_escolhidas):
            formato = simpledialog.askstring("Escolher Formato",
                                             "Digite 'Excel' ou 'CSV' para escolher o formato de exportação:")
            if formato is None:  # Usuário cancelou
                return
            formato = formato.lower()
            if formato in ['excel', 'csv']:
                processar_exportacao(seccoes_escolhidas, formato)
            else:
                messagebox.showerror("Erro", "Formato de exportação inválido. Escolha 'Excel' ou 'CSV'.")

        def processar_exportacao(seccoes_escolhidas, formato):
            try:
                if formato == 'excel':
                    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                             filetypes=[("Excel files", "*.xlsx")])
                    if file_path:
                        self.data_manager.exportar_para_excel(seccoes_escolhidas, file_path)
                elif formato == 'csv':
                    dir_path = filedialog.askdirectory()
                    if dir_path:
                        self.data_manager.exportar_para_csv(seccoes_escolhidas, dir_path)
                messagebox.showinfo("Exportar Dados", "Dados exportados com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar dados: {e}")

        escolher_seccoes()
# endregion

# region Funções para operações de Gerir Veículos
    def open_adicionar_veiculo(self):
        top_add_veiculo = tk.Toplevel(self.root)
        top_add_veiculo.title("Adicionar Veículo")

        fields = {
            "Marca": tk.Entry(top_add_veiculo),
            "Modelo": tk.Entry(top_add_veiculo),
            "Categoria": ttk.Combobox(top_add_veiculo,
                                      values=["Econômico", "Compacto", "Standard", "SUV", "Premium/Luxo", "Minivan",
                                              "Van", "Conversível", "Esportivo", "Pick-up"]),
            "Tipo": ttk.Combobox(top_add_veiculo,
                                 values=["Automotor Gasolina", "Automotor Diesel", "Elétrico", "Híbrido", "GNV", "Flex",
                                         "Híbrido Plug-in"]),
            "Transmissão": ttk.Combobox(top_add_veiculo, values=["Manual", "Semi-automática", "Automática"]),
            "Capacidade": tk.Entry(top_add_veiculo),
            "Diária": tk.Entry(top_add_veiculo),
            "Última Revisão": DateEntry(top_add_veiculo, date_pattern='dd-mm-yyyy'),
            "Próxima Revisão": DateEntry(top_add_veiculo, date_pattern='dd-mm-yyyy'),
            "Última Inspeção": DateEntry(top_add_veiculo, date_pattern='dd-mm-yyyy'),
            "Próxima Inspeção": DateEntry(top_add_veiculo, date_pattern='dd-mm-yyyy'),
            "Cor": tk.Entry(top_add_veiculo),
            "Chassis": tk.Entry(top_add_veiculo),
            "Ano de Fabricação": tk.Entry(top_add_veiculo),
            "Quilometragem": tk.Entry(top_add_veiculo),
            "Matrícula": tk.Entry(top_add_veiculo),
            "Imagem": tk.Entry(top_add_veiculo)
        }

        for i, (label, widget) in enumerate(fields.items()):
            tk.Label(top_add_veiculo, text=label + ":").grid(row=i, column=0, padx=10, pady=5)
            widget.grid(row=i, column=1, padx=10, pady=5)

        btn_confirmar = tk.Button(top_add_veiculo, text="Adicionar",
                                  command=lambda: self.data_manager.adicionar_veiculo(fields, top_add_veiculo))
        btn_confirmar.grid(row=len(fields), columnspan=2, pady=10)

    def listar_veiculos_interface(self):
        try:
            veiculos = self.data_manager.listar_veiculos()
            refresh_list = True

            top = tk.Toplevel(self.root)
            top.title("Lista de Veículos")
            top.state("zoomed")

            columns = [
                "ID", "Marca", "Modelo", "Categoria", "Tipo", "Transmissão", "Capacidade", "Diária",
                "Última Revisão", "Próxima Revisão", "Última Inspeção", "Próxima Inspeção",
                "Cor", "Chassis", "Ano de Fabricação", "Quilometragem", "Matrícula", "Imagem",
                "Disponibilidade", "Editar", "Apagar", "Manutenção", "Disponibilizar"
            ]

            tree = ttk.Treeview(top, columns=columns, show="headings")
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, anchor=tk.W, width=100)

            for veiculo in veiculos:
                tree.insert("", tk.END, values=veiculo + ("Editar", "Apagar", "Manutenção", "Disponibilizar"))

            tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
            tree.bind("<ButtonRelease-1>", lambda event: self.tree_click_veiculos(event, tree, top, refresh_list))

        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao listar veículos: {e}")

    def tree_click_veiculos(self, event, tree, top, refresh_list):
        item_id = tree.identify_row(event.y)
        column_id = tree.identify_column(event.x)
        if not item_id:
            return
        actions = {
            '#20': self.janela_edicao_veiculo,
            '#21': self.confirmar_remover_veiculo,
            '#22': self.reportar_avaria,
            '#23': self.marcar_como_disponivel
        }
        action = actions.get(column_id)
        if action:
            veiculo_id = tree.item(item_id)["values"][0]
            top.destroy()
            action(veiculo_id, refresh_list)

    def janela_edicao_veiculo(self, veiculo_id, refresh_list):
        veiculo = self.data_manager.buscar_editar_veiculo(veiculo_id)
        if veiculo:
            top_editar_veiculo = tk.Toplevel(self.root)
            top_editar_veiculo.title(f"Editar Veículo ID {veiculo[0]}")

        # Definir os campos, tipos de widget e suas opções
        fields = [
            ("Marca", tk.Entry, veiculo[1]),
            ("Modelo", tk.Entry, veiculo[2]),
            ("Categoria", ttk.Combobox, veiculo[3],
             ["Econômico", "Compacto", "Standard", "SUV", "Premium/Luxo", "Minivan", "Van", "Conversível", "Esportivo",
              "Camionete"]),
            ("Tipo", ttk.Combobox, veiculo[4],
             ["Automotor Gasolina", "Automotor Diesel", "Elétrico", "Híbrido", "GNV", "Flex", "Híbrido Plug-in"]),
            ("Transmissão", ttk.Combobox, veiculo[5], ["Manual", "Semi-automática", "Automática"]),
            ("Capacidade", tk.Entry, veiculo[6]),
            ("Diária", tk.Entry, veiculo[7]),
            ("Última Revisão", DateEntry, veiculo[8]),
            ("Próxima Revisão", DateEntry, veiculo[9]),
            ("Última Inspeção", DateEntry, veiculo[10]),
            ("Próxima Inspeção", DateEntry, veiculo[11]),
            ("Cor", tk.Entry, veiculo[12]),
            ("Chassis", tk.Entry, veiculo[13]),
            ("Ano de Fabricação", tk.Entry, veiculo[14]),
            ("Quilometragem", tk.Entry, veiculo[15]),
            ("Matrícula", tk.Entry, veiculo[16]),
            ("Imagem", tk.Entry, veiculo[17] if veiculo[17] else "")
        ]

        entries = []
        for i, (label, widget_type, value, *options) in enumerate(fields):
            tk.Label(top_editar_veiculo, text=f"{label}:").grid(row=i, column=0, padx=10, pady=5)

            if widget_type == ttk.Combobox:
                entry = widget_type(top_editar_veiculo, values=options[0])
                entry.set(value)
            elif widget_type == DateEntry:
                entry = widget_type(top_editar_veiculo, date_pattern='dd-mm-yyyy')
                entry.set_date(value)
            else:
                entry = widget_type(top_editar_veiculo)
                entry.insert(0, value)

            entry.grid(row=i, column=1, padx=10, pady=5)
            entries.append(entry)

            # Adicionar os botões "Confirmar" e "Cancelar" na parte inferior
            frame_botoes = tk.Frame(top_editar_veiculo)
            frame_botoes.grid(row=len(fields), column=0, columnspan=2, pady=10)

            # Botão de Confirmar Edição
            tk.Button(
                frame_botoes, text="Confirmar Edição",
                command=lambda: self.data_manager.editar_veiculo(
                    veiculo[0],
                    [entry.get() if not isinstance(entry, DateEntry) else entry.get_date().strftime('%d-%m-%Y') for
                     entry in entries],
                    top_editar_veiculo
                )
                                or (self.listar_veiculos_interface() if refresh_list
                                    else self.exibir_veiculo(veiculo_id=veiculo_id))
                    ).pack(side=tk.LEFT, padx=5)

            # Botão de Cancelar Edição
            tk.Button(
                frame_botoes, text="Cancelar", command=lambda: (self.listar_veiculos_interface() if refresh_list else self.exibir_veiculo(veiculo_id=veiculo[0]),
                                                                top_editar_veiculo.destroy())
            ).pack(side=tk.LEFT, padx=5)

        return top_editar_veiculo

    def confirmar_remover_veiculo(self, veiculo_id, refresh_list):
        if messagebox.askyesno("Confirmar Remoção", f"Tem certeza que deseja remover o veículo com ID {veiculo_id}?"):
            self.data_manager.remover_veiculo(veiculo_id, refresh_list)
        if refresh_list:
            self.listar_veiculos_interface()
        else:
            self.exibir_veiculo(veiculo_id=veiculo_id)

    def reportar_avaria(self, veiculo_id, refresh_list):
        self.data_manager.reportar_avaria(veiculo_id)
        if refresh_list:
            self.listar_veiculos_interface()
        else:
            self.exibir_veiculo(veiculo_id=veiculo_id)

    def marcar_como_disponivel(self, id_veiculo, refresh_list):
        self.data_manager.marcar_como_disponivel(id_veiculo)
        if refresh_list:
            self.listar_veiculos_interface()
        else:
            self.exibir_veiculo(veiculo_id=id_veiculo)

    def open_busca_veiculo(self):
        # Criar uma nova janela para buscar o veículo por ID ou matrícula
        self.busca_window = tk.Toplevel(self.root)
        self.busca_window.title("Buscar Veículo")
        self.busca_window.geometry("300x150")

        # Layout simplificado para escolher o método de busca (ID ou matrícula)
        tk.Label(self.busca_window, text="Escolha o método de busca:").pack()

        self.opcao_busca = tk.StringVar(value="ID")
        for opcao in [("ID", "ID"), ("Matrícula", "Matricula")]:
            tk.Radiobutton(self.busca_window, text=opcao[0], variable=self.opcao_busca, value=opcao[1]).pack()

        tk.Label(self.busca_window, text="Valor da busca:").pack()
        self.valor_busca_entry = tk.Entry(self.busca_window)
        self.valor_busca_entry.pack()

        # Botão de busca
        tk.Button(self.busca_window, text="Buscar", command=self.definir_busca_veiculo).pack()

    def definir_busca_veiculo(self):
        metodo_busca = self.opcao_busca.get()
        valor_busca = self.valor_busca_entry.get().strip()

        if metodo_busca == "ID":
            try:
                veiculo_id = int(valor_busca)
                self.exibir_veiculo(veiculo_id=veiculo_id)

            except ValueError:
                messagebox.showerror("Erro", "ID deve ser um número inteiro.")
        elif metodo_busca == "Matricula":
            self.exibir_veiculo(matricula=valor_busca)
        else:
            messagebox.showerror("Erro", "Método de busca não reconhecido.")

    def exibir_veiculo(self, veiculo_id=None, matricula=None):
        veiculo = self.data_manager.buscar_veiculo(veiculo_id, matricula)
        if not veiculo:
            messagebox.showerror("Erro", "Veículo não encontrado.")
            return

        try:
            refresh_list = False

            top = tk.Toplevel(self.root)
            top.title(f"Detalhes do Veículo")


            labels = [
                "ID", "Marca", "Modelo", "Categoria", "Tipo", "Transmissão", "Capacidade", "Diária",
                "Última Revisão", "Próxima Revisão", "Última Inspeção", "Próxima Inspeção",
                "Cor", "Chassis", "Ano de Fabricação", "Quilometragem", "Matrícula", "Imagem", "Disponibilidade"
            ]

            for i, (label, valor) in enumerate(zip(labels, veiculo)):
                tk.Label(top, text=label + ":", anchor="w").grid(row=i, column=0, sticky="w", padx=10, pady=2)
                tk.Label(top, text=valor, anchor="w").grid(row=i, column=1, sticky="w", padx=10, pady=2)

            # Botões de ação
            frame_botoes = tk.Frame(top)
            frame_botoes.grid(row=len(labels), column=0, columnspan=2, pady=10)

            botoes_acao = [
                ("Editar Veículo", lambda: [top.destroy(), self.janela_edicao_veiculo(veiculo[0], refresh_list)]),
                ("Apagar Veículo", lambda: [top.destroy(), self.confirmar_remover_veiculo(veiculo[0], refresh_list)]),
                ("Manutenção", lambda: [top.destroy(), self.reportar_avaria(veiculo[0], refresh_list)]),
                ("Disponibilizar", lambda: [top.destroy(), self.marcar_como_disponivel(veiculo[0], refresh_list)])
            ]

            for texto, comando in botoes_acao:
                tk.Button(frame_botoes, text=texto, command=comando).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exibir Veículo: {e}")
# endregion

# region Funções para operações de Gerir Clientes
    def open_adicionar_cliente(self):
        # Função para abrir janela de adicionar cliente
        top_add_cliente = tk.Toplevel(self.root)
        top_add_cliente.title("Adicionar Cliente")

        # Campos para adicionar cliente
        fields = {
            "Nome": tk.Entry(top_add_cliente),
            "Email": tk.Entry(top_add_cliente),
            "Telefone": tk.Entry(top_add_cliente),
            "Endereço": tk.Entry(top_add_cliente),
            "Documento de Identificação": tk.Entry(top_add_cliente)
        }

        # Criação dinâmica das labels e widgets
        for i, (label, widget) in enumerate(fields.items()):
            tk.Label(top_add_cliente, text=label + ":").grid(row=i, column=0, padx=10, pady=5)
            widget.grid(row=i, column=1, padx=10, pady=5)

        # Botão de confirmar
        btn_confirmar = tk.Button(
            top_add_cliente, text="Adicionar",
            command=lambda: self.data_manager.adicionar_cliente(fields, top_add_cliente)
        )
        btn_confirmar.grid(row=len(fields), columnspan=2, pady=10)

    def listar_clientes_interface(self):
        try:
            # Chama a função para obter a lista de clientes do banco de dados
            clientes = self.data_manager.listar_clientes()
            refresh_list = True

            # Cria uma nova janela Toplevel para exibir os clientes
            top = tk.Toplevel(self.root)
            top.title("Lista de Clientes")

            columns = ["ID", "Nome", "Email", "Telefone", "Endereço",
                       "Documento de Identificação", "Editar", "Apagar"]

            # Cria uma treeview para exibir os clientes em forma de tabela
            tree = ttk.Treeview(top, columns=columns, show="headings")
            for col in columns:
                tree.column(col, anchor=tk.W, width=100)
                tree.heading(col, text=col, anchor=tk.W)

            # Inserir clientes na Treeview com tags para identificar botões de ação
            for cliente in clientes:
                tree.insert("", tk.END, values=cliente + ("Editar", "Apagar"))

            tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
            tree.bind("<ButtonRelease-1>", lambda event: self.tree_click_clientes(event, tree, top, refresh_list))

        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao listar clientes: {e}")

    def tree_click_clientes(self, event, tree, top, refresh_list):
        item_id = tree.identify_row(event.y)
        column_id = tree.identify_column(event.x)

        if not item_id:
            return

        actions = {
            '#7': self.janela_edicao_cliente,
            '#8': self.confirmar_remover_cliente
        }

        action = actions.get(column_id)
        if action:
            client_id = tree.item(item_id)["values"][0]
            top.destroy()
            action(client_id, refresh_list)

    def janela_edicao_cliente(self, cliente_id, refresh_list):
        cliente = self.data_manager.buscar_editar_cliente(cliente_id)

        if cliente:
            top_editar_cliente = tk.Toplevel(self.root)
            top_editar_cliente.title(f"Editar Clinte ID {cliente[0]}")

        # Defenir campos
        fields = [
            ("Nome", tk.Entry, cliente[1]),
            ("Email", tk.Entry, cliente[2]),
            ("Telefone", tk.Entry, cliente[3]),
            ("Endereço", tk.Entry, cliente[4]),
            ("Documento de Identificação", tk.Entry, cliente[5])
        ]

        entries = []

        for i, (label, widget, value) in enumerate(fields):
            tk.Label(top_editar_cliente, text=label + ":").grid(row=i, column=0, padx=10, pady=5)
            entry = widget(top_editar_cliente)
            entry.insert(0, value)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries.append(entry)

        # Adicionar os botões "Confirmar" e "Cancelar" na parte inferior
        frame_botoes = tk.Frame(top_editar_cliente)
        frame_botoes.grid(row=len(fields), column=0, columnspan=2, pady=10)

        # Botão de Confirmar Edição
        tk.Button(
            frame_botoes, text="Confirmar Edição",
            command=lambda: self.data_manager.editar_cliente(
                cliente[0],
                [entry.get() for entry in entries],
                top_editar_cliente
            )
                            or (self.listar_clientes_interface() if refresh_list
                                else self.exibir_cliente(cliente_id=cliente_id))
        ).pack(side=tk.LEFT, padx=5)

        # Botão de Cancelar Edição
        tk.Button(
            frame_botoes, text="Cancelar", command=lambda: (
                self.listar_clientes_interface() if refresh_list else self.exibir_cliente(cliente_id=cliente[0]),
                top_editar_cliente.destroy())
        ).pack(side=tk.LEFT, padx=5)

        return top_editar_cliente

    def confirmar_remover_cliente(self, cliente_id, refresh_list):
        if messagebox.askyesno("Confirmar Remoção",
                               f"Tem certeza que deseja remover o cliente com ID {cliente_id}?"):
            self.data_manager.remover_cliente(cliente_id, refresh_list)
        if refresh_list:
            self.listar_clientes_interface()
        else:
            self.exibir_cliente(cliente_id=cliente_id)

    def open_busca_cliente(self):
        # Criar uma nova janela para buscar o cliente por ID ou email ou documento de identificação
        self.busca_window = tk.Toplevel(self.root)
        self.busca_window.title("Buscar Cliente")

        # Label e campo de entrada para escolher o método de busca (ID ou email ou documento de identificação)
        tk.Label(self.busca_window, text="Escolha o método de busca:").pack()

        self.opcao_busca = tk.StringVar(value="ID")
        opcoes = [
            ("ID", "ID"),
            ("Email", "Email"),
            ("Documento de Identificação", "Documento de Identificação")
        ]
        for texto, valor in opcoes:
            tk.Radiobutton(self.busca_window, text=texto, variable=self.opcao_busca, value=valor).pack()

        tk.Label(self.busca_window, text="Valor da busca:").pack()
        self.valor_busca_entry = tk.Entry(self.busca_window)
        self.valor_busca_entry.pack()

        # Botão de busca
        tk.Button(self.busca_window, text="Buscar", command=self.definir_busca_cliente).pack()

    def definir_busca_cliente(self):
        metodo_busca = self.opcao_busca.get()
        valor_busca = self.valor_busca_entry.get().strip()

        if not valor_busca:
            messagebox.showerror("Erro", "Por favor, insira um valor de busca.")
            return

        if metodo_busca == "ID":
            try:
                cliente_id = int(valor_busca)
                self.exibir_cliente(cliente_id=cliente_id)
            except ValueError:
                messagebox.showerror("Erro", "ID deve ser um número inteiro.")
        elif metodo_busca == "Email":
            self.exibir_cliente(email=valor_busca)
        elif metodo_busca == "Documento de Identificação":
            self.exibir_cliente(documento_id=valor_busca)
        else:
            messagebox.showerror("Erro", "Método de busca não reconhecido.")

    def exibir_cliente(self, cliente_id=None, email=None, documento_id=None):
        cliente = self.data_manager.buscar_cliente(cliente_id, email, documento_id)
        if not cliente:
            messagebox.showerror("Erro", "Cliente não encontrado.")
            return

        try:
            refresh_list = False
            # Criar uma nova janela Toplevel para exibir o cliente
            top = tk.Toplevel(self.root)
            top.title(f"Detalhes do Cliente ID {cliente[0]}")

            # Definir rótulos e valores correspondentes
            labels = [
                "ID", "Nome", "Email", "Telefone", "Endereço", "Documento de Identificação"
            ]

            for i, (label, valor) in enumerate(zip(labels, cliente)):
                tk.Label(top, text=label + ":", anchor="w").grid(row=i, column=0, sticky="w", padx=10, pady=2)
                tk.Label(top, text=valor, anchor="w").grid(row=i, column=1, sticky="w", padx=10, pady=2)

            # Botões para editar e apagar cliente
            frame_botoes = tk.Frame(top)
            frame_botoes.grid(row=len(labels), column=0, columnspan=2, pady=10)

            tk.Button(
                frame_botoes, text="Editar Cliente",
                command=lambda: [top.destroy(), self.janela_edicao_cliente(cliente[0], refresh_list)]
            ).pack(side=tk.LEFT, padx=5)

            tk.Button(
                frame_botoes, text="Apagar Cliente",
                command=lambda: [top.destroy(), self.confirmar_remover_cliente(cliente[0], refresh_list)]
            ).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exibir Cliente: {e}")

# endregion

# region Funções para operações de Gerir Formas de pagamento
    def open_adicionar_forma_pagamento(self):
        top_add_forma_pagamento = tk.Toplevel(self.root)
        top_add_forma_pagamento.title("Adicionar Forma de Pagamento")

        # Campos para adicionar Forma de Pagamento
        fields = {
            "Tipo": tk.Entry(top_add_forma_pagamento),
            "Descrição": tk.Entry(top_add_forma_pagamento)
        }

        # Criação dinâmica das labels e widgets
        for i, (label, widget) in enumerate(fields.items()):
            tk.Label(top_add_forma_pagamento, text=label + ":").grid(row=i, column=0, padx=10, pady=5)
            widget.grid(row=i, column=1, padx=10, pady=5)

        # Botão de confirmar
        btn_confirmar = tk.Button(top_add_forma_pagamento, text="Adicionar",
                                  command=lambda: self.data_manager.adicionar_forma_pagamento(fields, top_add_forma_pagamento)
                                  )
        btn_confirmar.grid(row=len(fields), columnspan=2, pady=10)

    def listar_formas_pagamento_interface(self):
        try:
            # Chama a função para obter a lista de veículos do banco de dados
            formas_pagamento = self.data_manager.listar_formas_pagamento()
            refresh_list = True

            # Cria uma nova janela Toplevel para exibir os veículos
            top = tk.Toplevel(self.root)
            top.title("Lista de Formas de Pagamento")

            # Definir as colunas da Treeview
            columns = ["ID", "Tipo", "Descrição", "Estado", "Editar", "Apagar", "Activar/Desactivar"]

            #Cria a Treeview para exibir as formas de pagamento em forma de tabela
            tree = ttk.Treeview(top, columns=columns, show="headings")
            for col in columns:
                tree.column(col, anchor=tk.W, width=100)
                tree.heading(col, text=col, anchor=tk.W)

            # Inserir formas de pagamento na Treeview
            for forma_pagamento in formas_pagamento:
                estado = "Activo" if forma_pagamento[3] == 1 else "Inactivo"
                botao_estado = "Activar" if estado == "Inactivo" else "Desactivar"
                tree.insert("", tk.END, values=(forma_pagamento[0], forma_pagamento[1], forma_pagamento[2], estado,"Editar", "Apagar", botao_estado))

            # Empacotar a Treeview
            tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

            # Definir evento de clique na Treeview
            tree.bind("<ButtonRelease-1>", lambda event: self.tree_click_forma_pagamento(event, tree, top, refresh_list))

        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao listar formas de pagamento: {e}")

    def tree_click_forma_pagamento(self, event, tree, top, refresh_list):
        item_id = tree.identify_row(event.y)
        column_id = tree.identify_column(event.x)

        if not item_id:
            return

        actions = {
            '#5': self.janela_edicao_forma_pagamento,
            '#6': self.confirmar_remover_forma_pagamento,
            '#7': self.alterar_estado_forma_pagamento
        }

        action = actions.get(column_id)
        if action:
            forma_pagamento_id = tree.item(item_id)["values"][0]
            top.destroy()
            action(forma_pagamento_id, refresh_list)

    def janela_edicao_forma_pagamento(self, forma_pagamento_id, refresh_list):
        forma_pagamento = self.data_manager.buscar_forma_pagamento(forma_pagamento_id)

        if forma_pagamento:
            top_editar_forma_pagamento = tk.Toplevel(self.root)
            top_editar_forma_pagamento.title(f"Editar Forma de pagamento ID {forma_pagamento[0]}")

        # Definir campos
        fields = {
            ("Tipo", tk.Entry, forma_pagamento[1]),
            ("Descrição", tk.Entry, forma_pagamento[2])
        }

        entries = []

        # Criar dinamicamente os campos de entrada
        for i, (label, widget, value) in enumerate(fields):
            tk.Label(top_editar_forma_pagamento, text=label + ":").grid(row=i, column=0, padx=10, pady=5)
            entry = widget(top_editar_forma_pagamento)
            entry.insert(0, value)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries.append(entry)

        # Mostrar estado atual
        estado = "Ativo" if forma_pagamento[3] == 1 else "Inativo"
        estado_label = tk.Label(top_editar_forma_pagamento, text=f"Estado: {estado}")
        estado_label.grid(row=len(fields), column=0, padx=10, pady=5)

        # Botão para alterar estado
        btn_alterar_estado = tk.Button(
            top_editar_forma_pagamento, text="Alterar Estado",
            command=lambda: self.alterar_estado_forma_pagamento(forma_pagamento[0])
        )
        btn_alterar_estado.grid(row=len(fields), column=1, padx=10, pady=5)

        # Adicionar os botões "Confirmar Edição" e "Cancelar" na parte inferior
        frame_botoes = tk.Frame(top_editar_forma_pagamento)
        frame_botoes.grid(row=len(fields) + 1, column=0, columnspan=2, pady=10)

        # Botão de Confirmar Edição
        tk.Button(
            frame_botoes, text="Confirmar Edição",
            command=lambda: self.data_manager.editar_forma_pagamento(
                forma_pagamento[0], [entry.get() for entry in entries],
                top_editar_forma_pagamento
            )
                            or (self.listar_formas_pagamento_interface() if refresh_list
                                else self.exibir_forma_pagamento(forma_pagamento_id))
        ).pack(side=tk.LEFT, padx=5)

        # Botão de Cancelar Edição
        tk.Button(
            frame_botoes, text="Cancelar",
            command=lambda: (
                self.listar_formas_pagamento_interface() if refresh_list else self.exibir_forma_pagamento(
                    forma_pagamento[0]),
                top_editar_forma_pagamento.destroy()
            )
        ).pack(side=tk.LEFT, padx=5)

        return top_editar_forma_pagamento

    def alterar_estado_forma_pagamento(self, forma_pagamento_id, refresh_list):
        self.data_manager.alterar_estado_forma_pagamento(forma_pagamento_id)
        if refresh_list:
            self.listar_formas_pagamento_interface()
        else:
            self.exibir_forma_pagamento(forma_pagamento_id)

    def confirmar_remover_forma_pagamento(self, forma_pagamento_id, refresh_list):
        if messagebox.askyesno("Confirmar Remoção", f"Tem certeza que deseja remover a forma de pagamento com ID {forma_pagamento_id}?"):
            self.data_manager.remover_forma_pagamento(forma_pagamento_id, refresh_list)
        if refresh_list:
            self.listar_formas_pagamento_interface()
        else:
            self.exibir_forma_pagamento(forma_pagamento_id)

    def open_buscar_forma_pagamento(self):
        # Criar uma nova janela para buscar a forma de pagamento por ID
        top_buscar = tk.Toplevel(self.root)
        top_buscar.title("Buscar forma de pagamento")

        tk.Label(top_buscar, text="ID:").grid(row=0, column=0, padx=10, pady=5)
        id_entry = tk.Entry(top_buscar)
        id_entry.grid(row=0, column=1, padx=10, pady=5)

        # Botão para confirmar a busca
        tk.Button(top_buscar, text="Buscar",
                  command=lambda: self.exibir_forma_pagamento(id_entry.get())).grid(row=1, columnspan=2, pady=10)

    def exibir_forma_pagamento(self, forma_pagamento_id):
        forma_pagamento = self.data_manager.buscar_forma_pagamento(forma_pagamento_id)
        if not forma_pagamento:
            messagebox.showerror("Erro", "Forma de pagamento não encontrada.")
            return

        try:
            refresh_list = False

            top = tk.Toplevel(self.root)
            top.title(f"Detalhes da Forma de Pagamento ID {forma_pagamento[0]}")

            #Definir rótulos e valores correspondentes
            labels = ["ID", "Tipo", "Descrição"]
            values = forma_pagamento[:3]

            for i, (label, valor) in enumerate(zip(labels, values)):
                tk.Label(top, text=label + ":", anchor="w").grid(row=i, column=0, sticky="w", padx=10, pady=2)
                tk.Label(top, text=valor, anchor="w").grid(row=i, column=1, sticky="w", padx=10, pady=2)

            estado = "Ativo" if forma_pagamento[3] == 1 else "Inativo"
            botao_estado = "Activar" if estado == "Inactivo" else "Desactivar"
            tk.Label(top, text="Estado:").grid(row=len(labels), column=0, sticky="w", padx=10, pady=5)
            tk.Label(top, text=estado).grid(row=len(labels), column=1, sticky="w", padx=10, pady=5)

            # Adicionar os botões de ação
            frame_botoes = tk.Frame(top)
            frame_botoes.grid(row=len(labels) + 1, column=0, columnspan=2, pady=10)

            tk.Button(
                frame_botoes, text="Editar Forma de Pagamento",
                command=lambda: [top.destroy(), self.janela_edicao_forma_pagamento(forma_pagamento[0], refresh_list)]
            ).pack(side=tk.LEFT, padx=5)

            tk.Button(
                frame_botoes, text="Apagar Forma de Pagamento",
                command=lambda: [top.destroy(),
                                 self.confirmar_remover_forma_pagamento(forma_pagamento[0], refresh_list)]
            ).pack(side=tk.LEFT, padx=5)

            tk.Button(
                frame_botoes, text=f"{botao_estado} Forma de Pagamento",
                command=lambda: [top.destroy(), self.alterar_estado_forma_pagamento(forma_pagamento[0], refresh_list)]
            ).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exibir Forma de Pagamento: {e}")

# endregion

# region Funções para operações de Gerir Reservas
    def open_adicionar_reserva(self):
        top_adicionar_reserva = tk.Toplevel(self.root)
        top_adicionar_reserva.title("Adicionar Reserva")

        # Dicionário com os campos e widgets
        fields = {
            "Data Início": DateEntry(top_adicionar_reserva, date_pattern='dd-mm-yyyy'),
            "Data Fim": DateEntry(top_adicionar_reserva, date_pattern='dd-mm-yyyy'),
            "Selecionar Categoria do Veículo": ttk.Combobox(top_adicionar_reserva, state="readonly", textvariable=self.categoria_var),
            "Selecionar Veículo": self.lista_veiculo_selecionado,
            "Forma de Pagamento": ttk.Combobox(top_adicionar_reserva, state="readonly")
        }
        # Criação e posicionamento dinâmico dos widgets
        for i, (label, widget) in enumerate(fields.items()):
            tk.Label(top_adicionar_reserva, text=label + ":").grid(row=i, column=0, padx=10, pady=5)
            if isinstance(widget, tk.StringVar):
                tk.Label(top_adicionar_reserva, textvariable=widget).grid(row=i, column=1, padx=10, pady=5)
            else:
                widget.grid(row=i, column=1, padx=10, pady=5)

        # Botão para selecionar veículo
        btn_selecionar_veiculo = tk.Button(
            top_adicionar_reserva,
            text="Selecionar Veículo",
            command=self.open_listar_veiculos_disponiveis
        )
        btn_selecionar_veiculo.grid(row=3, column=2, padx=10, pady=5)

        # Botões de seleção de tipo de cliente
        cliente_frame = tk.Frame(top_adicionar_reserva)
        cliente_frame.grid(row=5, column=1, padx=10, pady=5, columnspan=2)

        tk.Radiobutton(cliente_frame, text="Novo Cliente", variable=self.novo_cliente_var, value=True,
                       command=self.toggle_cliente).grid(row=5, column=1, padx=10, pady=5)
        tk.Radiobutton(cliente_frame, text="Cliente Existente", variable=self.novo_cliente_var, value=False,
                       command=self.toggle_cliente).grid(row=5, column=2, padx=10, pady=5)

        # Área de novo cliente
        self.novo_cliente_frame = tk.Frame(top_adicionar_reserva)
        self.novo_cliente_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=5)
        tk.Label(self.novo_cliente_frame, text="Nome (Novo Cliente):").grid(row=0, column=0, padx=10, pady=5)
        nome_entry = tk.Entry(self.novo_cliente_frame)
        nome_entry.grid(row=0, column=1, padx=10, pady=5)
        tk.Label(self.novo_cliente_frame, text="Email (Novo Cliente):").grid(row=1, column=0, padx=10, pady=5)
        email_entry = tk.Entry(self.novo_cliente_frame)
        email_entry.grid(row=1, column=1, padx=10, pady=5)
        tk.Label(self.novo_cliente_frame, text="Telefone (Novo Cliente):").grid(row=2, column=0, padx=10, pady=5)
        telefone_entry = tk.Entry(self.novo_cliente_frame)
        telefone_entry.grid(row=2, column=1, padx=10, pady=5)
        tk.Label(self.novo_cliente_frame, text="Endereço (Novo Cliente):").grid(row=3, column=0, padx=10, pady=5)
        endereco_entry = tk.Entry(self.novo_cliente_frame)
        endereco_entry.grid(row=3, column=1, padx=10, pady=5)
        tk.Label(self.novo_cliente_frame, text="Documento ID (Novo Cliente):").grid(row=4, column=0, padx=10, pady=5)
        documento_id_entry = tk.Entry(self.novo_cliente_frame)
        documento_id_entry.grid(row=4, column=1, padx=10, pady=5)

        # Área de cliente existente
        self.existente_cliente_frame = tk.Frame(top_adicionar_reserva)
        self.existente_cliente_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=5)
        tk.Label(self.existente_cliente_frame, text="Cliente Existente:").grid(row=0, column=0, padx=10, pady=5)
        self.cliente_existente_combobox = ttk.Combobox(self.existente_cliente_frame, state="readonly")
        self.cliente_existente_combobox.grid(row=0, column=1, padx=10, pady=5)

        # Atualiza o dicionário fields com base no tipo de cliente
        def update_fields():
            if self.novo_cliente_var.get():
                # Adiciona campos do novo cliente
                fields.update({
                    "Nome (Novo Cliente)": nome_entry,
                    "Email (Novo Cliente)": email_entry,
                    "Telefone (Novo Cliente)": telefone_entry,
                    "Endereço (Novo Cliente)": endereco_entry,
                    "Documento ID (Novo Cliente)": documento_id_entry
                })
                self.existente_cliente_frame.grid_forget()  # Esconde a área de cliente existente
            else:
                # Adiciona cliente existente
                fields["Cliente Existente"] = self.cliente_existente_combobox
                self.novo_cliente_frame.grid_forget()  # Esconde a área de novo cliente
            return fields


        # Botão para adicionar reserva
        btn_adicionar = tk.Button(
            top_adicionar_reserva,
            text="Adicionar Reserva",
            command=lambda: self.data_manager.adicionar_reserva(update_fields(), self.novo_cliente_var, top_adicionar_reserva)
        )
        btn_adicionar.grid(row=8, columnspan=2, pady=10)

        # Preenchimento dos comboboxes
        self.preencher_categorias_veiculos(fields["Selecionar Categoria do Veículo"])
        self.data_manager.preencher_formas_pagamento(fields["Forma de Pagamento"])
        self.data_manager.preencher_clientes_existentes(self.cliente_existente_combobox)

        # Inicializa os frames de cliente
        self.toggle_cliente()

    def preencher_categorias_veiculos(self, widget):
        categorias = [
            "Econômico", "Compacto", "Standard", "SUV", "Premium/Luxo",
            "Minivan", "Van", "Conversível", "Esportivo", "Camionete"
        ]
        widget['values'] = categorias

    def open_listar_veiculos_disponiveis(self):
        if self.categoria_var.get() == "":
            messagebox.showwarning("Aviso", "Selecione uma categoria de veículo.")
            return

        self.top_listar_veiculos = tk.Toplevel(self.root)
        self.top_listar_veiculos.title("Listar Veículos Disponíveis")

        self.veiculos_frame = tk.Frame(self.top_listar_veiculos)
        self.veiculos_frame.pack(pady=10)

        # Listar veículos disponíveis da categoria selecionada
        self.data_manager.listar_veiculos_disponiveis(self.categoria_var.get(), self.veiculos_frame, self.selecionar_veiculo)

    def selecionar_veiculo(self, veiculo):
        veiculo_texto = f"{veiculo[1]} {veiculo[2]} - Matrícula: {veiculo[8]} - Diária: R${veiculo[9]}"
        self.lista_veiculo_selecionado.set(f"{veiculo[0]} {veiculo_texto}")
        self.top_listar_veiculos.destroy()

    def toggle_cliente(self):
        if self.novo_cliente_var.get():
            self.novo_cliente_frame.grid()
            self.existente_cliente_frame.grid_remove()
        else:
            self.novo_cliente_frame.grid_remove()
            self.existente_cliente_frame.grid()

    def listar_reservas_interface(self):
        try:
            # Chama a função para obter a lista de reservas do banco de dados
            reservas = self.data_manager.listar_reservas()
            refresh_list = True

            # Cria uma nova janela Toplevel para exibir as reservas
            top = tk.Toplevel(self.root)
            top.title("Lista de Reservas")

            columns = ["ID Reserva", "Data Início", "Data Fim", "Cliente", "Veículo",
                "Pagamento", "Valor Total", "Editar", "Apagar"]

            # Cria uma treeview para exibir as reservas em forma de tabela
            tree = ttk.Treeview(top, columns=columns, show="headings")
            for col in columns:
                tree.column(col, anchor=tk.W, width=100)
                tree.heading(col, text=col, anchor=tk.W)

            # Inserir Reservas na Treeview com tags para identificar botões de ação
            for reserva in reservas:
                # Montar os valores da reserva para inserir na Treeview
                id_reserva = reserva[0]
                data_inicio = reserva[1]
                data_fim = reserva[2]
                cliente = f"{reserva[3]} {reserva[4]}"
                veiculo = f"{reserva[5]} {reserva[6]} {reserva[7]}"
                forma_pagamento = f"{reserva[8]} - {reserva[9]}"
                valor_total = reserva[10]
                tree.insert("", tk.END, values=(id_reserva, data_inicio, data_fim, cliente, veiculo, forma_pagamento,
                                                valor_total) + ("Editar", "Apagar"))

            scrollbar = ttk.Scrollbar(top, orient="vertical", command=tree.yview)
            tree.configure(yscroll=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.pack(fill=tk.BOTH, expand=True)

            # Definir evento de clique na Treeview
            tree.bind("<ButtonRelease-1>", lambda event: self.tree_click_reservas(event, tree, top, refresh_list))

        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao listar Reservas: {e}")

    def tree_click_reservas(self, event, tree, top, refresh_list):
        item_id = tree.identify_row(event.y)
        column_id = tree.identify_column(event.x)

        if not item_id:
            return

        actions = {
            '#8':  self.janela_edicao_reserva,
            '#9':  self.confirmar_remover_reserva
        }

        action = actions.get(column_id)
        if action:
            reserva_id = tree.item(item_id)["values"][0]
            top.destroy()
            action(reserva_id, refresh_list)

    def janela_edicao_reserva(self, reserva_id, refresh_list):
        reserva = self.data_manager.buscar_editar_reserva(reserva_id)

        if not reserva:
            messagebox.showerror("Erro", "Reserva não encontrada.")
            return

        top_editar_reserva = tk.Toplevel(self.root)
        top_editar_reserva.title(f"Editar Reserva ID {reserva_id}")

        self.forma_pagamento_var = tk.StringVar()
        self.lista_veiculo_selecionado = tk.StringVar()
        self.categoria_var = tk.StringVar()

        # Dicionário com os campos e widgets
        fields = [
            ("ID da Reserva", tk.Label, reserva[0]),
            ("Nome do Cliente", tk.Label, reserva[7]),
            ("Veículo Atual", tk.Label,
             f"{reserva[8]} - {reserva[9]}" if reserva[8] and reserva[9] else "Veículo não selecionado"),
            ("Data Início", DateEntry, reserva[4], {'date_pattern': 'dd-mm-yyyy'}),
            ("Data Fim", DateEntry, reserva[5], {'date_pattern': 'dd-mm-yyyy'}),
            ("Forma de Pagamento", ttk.Combobox,
             {'textvariable': self.forma_pagamento_var, 'state': 'readonly'})
        ]

        # 1. Criação e posicionamento dinâmico dos widgets
        entries = []
        for i, (label_text, widget_type, value, *options) in enumerate(fields):
            tk.Label(top_editar_reserva, text=f"{label_text}:").grid(row=i, column=0, padx=10, pady=5)

            # Criando os widgets de acordo com o tipo
            if widget_type == tk.Label:
                widget = widget_type(top_editar_reserva, text=value)
            elif widget_type == ttk.Combobox:
                widget = widget_type(top_editar_reserva, **(options[0] if options else {}))
                # Defina o valor atual para o Combobox
                widget.set(f"{reserva[3]} - {reserva[10]}" if reserva [3] and reserva[10] else "")
                self.data_manager.preencher_formas_pagamento(widget)
                fields[i] = (label_text, widget_type, widget)
            elif widget_type == DateEntry:
                widget = widget_type(top_editar_reserva, **(options[0] if options else {}))
                widget.set_date(value)

            widget.grid(row=i, column=1, padx=10, pady=5)
            entries.append(widget)

            # 2. Seção de Veículo: Manter ou Alterar
            tk.Label(top_editar_reserva, text="Deseja alterar o veículo:").grid(row=len(fields), column=0, columnspan=2,
                                                                                padx=10, pady=5)

            # Botão para manter o veículo atual
            btn_manter_veiculo = tk.Button(top_editar_reserva, text="Manter Veículo Atual",
                                           command=lambda: self.atualizar_veiculo_selecionado(
                                               manter=True,
                                               veiculo_info=f"{reserva[2]} {reserva[8]} {reserva[9]}"
                                           ))
            btn_manter_veiculo.grid(row=len(fields) + 1, column=0, padx=10, pady=5)

            # Combobox para selecionar nova categoria
            tk.Label(top_editar_reserva, text="Selecione a nova categoria:").grid(row=len(fields) + 2, column=0,
                                                                                  padx=10, pady=5)
            self.categoria_combobox = ttk.Combobox(top_editar_reserva, textvariable=self.categoria_var,
                                                   state='readonly')
            self.categoria_combobox.grid(row=len(fields) + 2, column=1, padx=10, pady=5)

            # Preencher as categorias no Combobox
            self.preencher_categorias_veiculos(self.categoria_combobox)

            # Botão para selecionar nova categoria e veículo
            btn_nova_categoria = tk.Button(top_editar_reserva, text="Selecionar Veículo",
                                           command=lambda: self.selecionar_nova_categoria(top_editar_reserva))
            btn_nova_categoria.grid(row=len(fields) + 3, column=1, padx=10, pady=5)

            # 3. Informações do veículo selecionado ou mantido
            tk.Label(top_editar_reserva, text="Veículo Selecionado:").grid(row=len(fields) + 4, column=0, padx=10,
                                                                           pady=5)
            label_veiculo_selecionado = tk.Label(top_editar_reserva, textvariable=self.lista_veiculo_selecionado)
            label_veiculo_selecionado.grid(row=len(fields) + 4, column=1, padx=10, pady=5)

            # 4. Botão para confirmar edição da reserva
            btn_confirmar = tk.Button(top_editar_reserva, text="Confirmar Edição",
                                      command=lambda: self.data_manager.editar_reserva(reserva_id, {
                                          'Nome do Cliente': reserva[7],
                                          # Obtém o texto do Label correspondente
                                          'Data Início': entries[3].get_date(),
                                          'Data Fim': entries[4].get_date(),
                                          'Veículo Selecionado': self.lista_veiculo_selecionado.get(),
                                          'Forma de Pagamento': self.forma_pagamento_var.get()
                                          if self.forma_pagamento_var.get() else f"{reserva[3]} {reserva[10]}",
                                      }, top_editar_reserva)
                                                      or (self.listar_reservas_interface() if refresh_list
                                                          else self.exibir_reserva(reserva_id))
                                      )
            btn_confirmar.grid(row=len(fields) + 5, columnspan=2, pady=10)

            # Botão de Cancelar Edição
            btn_cancelar = tk.Button(top_editar_reserva, text="Cancelar",
                                     command=lambda: (
                                         top_editar_reserva.destroy(),  # Fecha a janela sem salvar
                                         self.listar_reservas_interface() if refresh_list else self.exibir_reserva(
                                             reserva_id)
                                     ))
            btn_cancelar.grid(row=len(fields) + 6, columnspan=2, pady=10)

    def atualizar_veiculo_selecionado(self, manter, veiculo_info):
        """Atualiza a exibição do veículo selecionado ou mantido."""
        if manter:
            self.lista_veiculo_selecionado.set(f"{veiculo_info} (mantendo veículo atual)")
        else:
            # Se o usuário selecionar um novo veículo, esse campo será atualizado pelo método selecionar_veiculo
            self.lista_veiculo_selecionado.set("Novo veículo selecionado")

    def selecionar_nova_categoria(self, top_editar_reserva):
        # Verifica se uma categoria foi selecionada
        if self.categoria_var.get() == "":
            messagebox.showwarning("Aviso", "Selecione uma categoria de veículo.")
            return

        # Abre a janela para listar os veículos disponíveis da categoria selecionada
        self.open_listar_veiculos_disponiveis()

    def confirmar_remover_reserva(self, reserva_id, refresh_list):
        if messagebox.askyesno("Confirmar Remoção",
                               f"Tem certeza que deseja remover a reserva com ID {reserva_id}?"):
            self.data_manager.remover_reserva(reserva_id, refresh_list)
        if refresh_list:
            self.listar_reservas_interface()
        else:
            self.exibir_reserva(reserva_id)

    def open_busca_reserva(self):
        try:
            # Criar uma nova janela Toplevel para buscar reservas
            self.top_busca_reserva = tk.Toplevel(self.root)
            self.top_busca_reserva.title("Buscar Reserva")

            # Campo para ID da reserva
            tk.Label(self.top_busca_reserva, text="ID da Reserva").grid(row=0,
                                                                        column=0,
                                                                        padx=10,
                                                                        pady=5)
            self.entry_id_reserva = tk.Entry(self.top_busca_reserva)
            self.entry_id_reserva.grid(row=0, column=1, padx=10, pady=5)

            # Botão para buscar reservas
            btn_buscar = tk.Button(self.top_busca_reserva, text="Buscar", command=lambda: self.exibir_reserva(self.entry_id_reserva.get().strip()))
            btn_buscar.grid(row=1, columnspan=2, pady=10)

            # Frame para mostrar os resultados
            self.frame_resultados = tk.Frame(self.top_busca_reserva)
            self.frame_resultados.grid(row=2, columnspan=2, pady=10)

        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao abrir busca de reservas: {e}")

    def exibir_reserva(self, id_reserva):
        # Chamar o método de busca do dataManager
        reserva = self.data_manager.buscar_reserva(id_reserva)
        if not reserva:
            messagebox.showinfo("Resultado", "Nenhuma reserva encontrada com os critérios fornecidos.")
            return


        try:
            refresh_list = False
            top = tk.Toplevel(self.root)
            top.title(f"Detalhes da Reserva")

            # Criar um novo frame para os resultados
            frame_resultados = tk.Frame(top)
            frame_resultados.grid(row=0, column=0, padx=10, pady=10)

            # Exibir os resultados
            tk.Label(frame_resultados, text=f"Reserva ID: {reserva[0]}").grid(row=0, column=0, padx=10, pady=5)
            tk.Label(frame_resultados, text=f"Cliente: {reserva[7]}").grid(row=0, column=1, padx=10, pady=5)
            tk.Label(frame_resultados, text=f"Veículo: {reserva[8]} {reserva[9]} ({reserva[10]})").grid(row=0,
                                                                                                        column=2,
                                                                                                        padx=10,
                                                                                                        pady=5)
            tk.Label(frame_resultados, text=f"Data Início: {reserva[4]}").grid(row=0, column=3, padx=10, pady=5)
            tk.Label(frame_resultados, text=f"Data Fim: {reserva[5]}").grid(row=0, column=4, padx=10, pady=5)

            # Frame para os botões de ação
            frame_botoes = tk.Frame(top)
            frame_botoes.grid(row=1, column=0, columnspan=5, pady=10)

            # Botões de ação: Editar e Apagar
            botoes_acao = [
                ("Editar Reserva", lambda: [top.destroy(), self.janela_edicao_reserva(reserva[0], refresh_list)]),
                ("Apagar Reserva", lambda: [top.destroy(), self.confirmar_remover_reserva(reserva[0], refresh_list)])
            ]

            for texto, comando in botoes_acao:
                tk.Button(frame_botoes, text=texto, command=comando).pack(side=tk.LEFT, padx=5)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exibir Reserva: {e}")

# endregion

'''fim'''