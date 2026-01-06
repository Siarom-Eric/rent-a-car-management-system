import sqlite3
import pandas as pd
from tkinter import messagebox
import datetime
from datetime import timedelta, datetime
import tkinter as tk
from dateutil.relativedelta import relativedelta

class DataManager:
    def __init__(self):
        self.conn = sqlite3.connect('aluguel_carros.db')
        self.cursor = self.conn.cursor()
        self.initialize_database()

# region Inicialização do Banco de Dados
    def initialize_database(self):
        """ Inicializa o banco de dados e cria tabelas, se necessário. """
        try:
            tabelas = [
                '''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    telefone TEXT,
                    senha_hash TEXT NOT NULL,
                    data_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ultimo_acesso TIMESTAMP
                );''',
                '''CREATE TABLE IF NOT EXISTS veiculos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    marca TEXT NOT NULL,
                    modelo TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    transmissao TEXT NOT NULL,
                    capacidade INTEGER NOT NULL,
                    diaria REAL NOT NULL,
                    ultima_revisao DATE,
                    proxima_revisao DATE,
                    ultima_inspecao DATE,
                    proxima_inspecao DATE,
                    cor TEXT,
                    chassis TEXT,
                    ano_fabricacao INTEGER,
                    quilometragem INTEGER,
                    matricula TEXT NOT NULL UNIQUE,
                    imagem TEXT,
                    disponibilidade TEXT DEFAULT 'Disponível'
                );''',
                '''CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    telefone TEXT,
                    endereco TEXT,
                    documento_id TEXT NOT NULL UNIQUE
                );''',
                '''CREATE TABLE IF NOT EXISTS reservas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_cliente INTEGER NOT NULL,
                    id_veiculo INTEGER NOT NULL,
                    id_forma_pagamento INTEGER NOT NULL,
                    data_inicio DATE NOT NULL,
                    data_fim DATE NOT NULL,
                    valor_total REAL NOT NULL,
                    FOREIGN KEY (id_cliente) REFERENCES clientes(id),
                    FOREIGN KEY (id_veiculo) REFERENCES veiculos(id),
                    FOREIGN KEY (id_forma_pagamento) REFERENCES formas_pagamento(id)
                );''',
                '''CREATE TABLE IF NOT EXISTS formas_pagamento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    descricao TEXT,
                    ativo INTEGER DEFAULT 1
                );'''
            ]

            for tabela in tabelas:
                self.cursor.execute(tabela)

            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Erro ao inicializar banco de dados: {e}")
# endregion

# region Informações para o Display
    """ Funções relacionadas ao display """
    def get_veiculos_alugados(self, hoje):
        self.cursor.execute('''
            SELECT v.marca, v.modelo, julianday(r.data_fim) - julianday(?) as dias_restantes
            FROM reservas r
            JOIN veiculos v ON r.id_veiculo = v.id
            WHERE julianday(r.data_fim) >= julianday(?)
        ''', (hoje, hoje))
        return self.cursor.fetchall()

    def get_ultimos_clientes(self):
        self.cursor.execute('''
            SELECT nome, email FROM clientes
            ORDER BY id DESC LIMIT 5
        ''')
        return self.cursor.fetchall()

    def get_veiculos_disponiveis_categoria(self):
        self.cursor.execute('''
            SELECT categoria, COUNT(*)
            FROM veiculos
            WHERE disponibilidade = 'Disponível'
            GROUP BY categoria
        ''')
        return self.cursor.fetchall()

    def get_veiculos_disponiveis_tipo(self):
        self.cursor.execute('''
            SELECT tipo, COUNT(*)
            FROM veiculos
            WHERE disponibilidade = 'Disponível'
            GROUP BY tipo
        ''')
        return self.cursor.fetchall()

    def get_lucro_ultimos_seis_meses(self):
        # Obter os lucros dos últimos seis meses, tratando as datas no formato DD-MM-YYYY
        self.cursor.execute('''
            SELECT strftime('%m-%Y', substr(data_inicio, 7, 4) || '-' || substr(data_inicio, 4, 2) || '-' || substr(data_inicio, 1, 2)) AS mes, 
                   SUM(valor_total) AS lucro_total 
            FROM reservas 
            WHERE date(substr(data_inicio, 7, 4) || '-' || substr(data_inicio, 4, 2) || '-' || substr(data_inicio, 1, 2)) >= date('now', '-6 months')
            GROUP BY mes
            ORDER BY mes;
        ''')

        resultados = self.cursor.fetchall()

        # Criar uma lista de meses para os últimos 6 meses
        meses_atual = [(datetime.today() - timedelta(days=i * 30)).strftime('%m-%Y') for i in range(6)][
                      ::-1]  # Inverter para ficar do mais antigo para o mais recente

        # Criar um dicionário para armazenar os lucros por mês
        lucro_dict = {mes: 0 for mes in meses_atual}  # Inicializa todos os meses com 0

        # Preencher o dicionário com os lucros reais
        for mes, valor in resultados:
            lucro_dict[mes] = valor if valor is not None else 0  # Se o valor for None, define como 0

        return lucro_dict

    def get_veiculos_revisao(self, hoje):
        self.cursor.execute('''
            SELECT marca, modelo, proxima_revisao
            FROM veiculos
            WHERE julianday(proxima_revisao) - julianday(?) <= 15
        ''', (hoje,))
        return self.cursor.fetchall()

    def get_veiculos_inspecao(self, hoje):
        self.cursor.execute('''
            SELECT marca, modelo, proxima_inspecao
            FROM veiculos
            WHERE julianday(proxima_inspecao) - julianday(?) <= 15
        ''', (hoje,))
        return self.cursor.fetchall()
# endregion

# region Exportação de Dados
    def exportar_para_excel(self, seccoes_escolhidas, file_path):
        """ Exporta os dados selecionados para um arquivo Excel. """
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for seccao, query in self.get_seccoes_queries().items():
                if seccao in seccoes_escolhidas:
                    data = pd.read_sql_query(query, self.conn)
                    data.to_excel(writer, sheet_name=seccao, index=False)

    def exportar_para_csv(self, seccoes_escolhidas, dir_path):
        """ Exporta os dados selecionados para arquivos CSV. """
        for seccao, query in self.get_seccoes_queries().items():
            if seccao in seccoes_escolhidas:
                data = pd.read_sql_query(query, self.conn)
                data.to_csv(f"{dir_path}/{seccao.lower()}.csv", index=False)

    def get_seccoes_queries(self):
        """ Retorna as consultas SQL para cada seção. """
        return {
            'Veículos': "SELECT * FROM veiculos",
            'Clientes': "SELECT * FROM clientes",
            'Reservas': "SELECT * FROM reservas",
            'Formas de Pagamento': "SELECT * FROM formas_pagamento"
        }
# endregion

# region Operações com Veículos
    def atualizar_disponibilidade_todos(self):
        self.cursor.execute('SELECT id FROM veiculos')
        veiculos = self.cursor.fetchall()
        for veiculo in veiculos:
            self.atualizar_disponibilidade_veiculo(veiculo[0])
    def atualizar_disponibilidade_veiculo(self, veiculo_id):
        hoje = datetime.today().date()

        # Obter informações do veículo
        self.cursor.execute('''SELECT proxima_revisao, proxima_inspecao, disponibilidade FROM veiculos WHERE id = ?''',
                            (veiculo_id,))
        veiculo = self.cursor.fetchone()

        if veiculo is None:
            print(f"Veículo com ID {veiculo_id} não encontrado.")
            return

        proxima_revisao = veiculo[0]
        proxima_inspecao = veiculo[1]
        disponibilidade_actual = veiculo[2]

        # Verificar se está em manutenção
        if disponibilidade_actual == 'Em Manutenção':
            # Não alterar se estiver em manutenção
            return

        if proxima_revisao and proxima_inspecao:
            try:
                # Ajuste o formato da data conforme necessário
                data_proxima_revisao = datetime.strptime(proxima_revisao, "%d-%m-%Y").date()
                data_proxima_inspecao = datetime.strptime(proxima_inspecao, "%d-%m-%Y").date()
            except ValueError as e:
                print(f"Erro ao converter datas: {e}")
                return

            data_inicio_inspecao = data_proxima_revisao - timedelta(days=1)
            data_fim_inspecao = data_proxima_inspecao + timedelta(days=1)

            if data_inicio_inspecao <= hoje <= data_fim_inspecao:
                disponibilidade = 'Em período de inspeção'
            else:
                # Se não estiver no período de inspeção, verificar a reserva
                # Obter as reservas para o veículo
                self.cursor.execute(
                    '''SELECT data_fim FROM reservas WHERE id_veiculo = ? AND ? BETWEEN data_inicio AND data_fim''',
                    (veiculo_id, hoje))
                reserva = self.cursor.fetchone()

                if reserva:
                    # Converter a data de fim da reserva para datetime.date
                    data_fim_reserva = datetime.strptime(reserva[0], "%d-%m-%Y").date()
                    # Se houver uma reserva ativa, marcar como reservado
                    if hoje <= data_fim_reserva:
                        disponibilidade = 'Reservado'
                    else:
                        disponibilidade = 'Disponível'
                else:
                    # Se não houver reserva, verificar se há uma reserva futura para o próximo dia
                    self.cursor.execute('''SELECT data_inicio FROM reservas WHERE id_veiculo = ? AND data_inicio = ?''',
                                        (veiculo_id, hoje + timedelta(days=1)))
                    reserva_futura = self.cursor.fetchone()

                    if reserva_futura:
                        disponibilidade = 'Reservado'
                    else:
                        disponibilidade = 'Disponível'

                # Atualizar a disponibilidade do veículo
            self.cursor.execute('''UPDATE veiculos SET disponibilidade = ? WHERE id = ?''',
                                (disponibilidade, veiculo_id))
            self.conn.commit()

    def reportar_avaria(self, veiculo_id):
        try:
            # Atualizar disponibilidade para "Avariado"
            self.cursor.execute('''UPDATE veiculos SET disponibilidade = ? WHERE id = ?''', ('Em Manutenção', veiculo_id))
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao reportar avaria do veículo: {e}")
    def marcar_como_disponivel(self, id_veiculo):
        try:
            # Atualizar a disponibilidade do veículo para 'Disponível'
            self.cursor.execute("UPDATE veiculos SET disponibilidade = 'Disponível' WHERE id = ?", (id_veiculo,))
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao atualizar disponibilidade do veículo: {e}")
    def adicionar_veiculo(self, fields, top):
        try:
            # Obtenção de dados e validações
            data = {key: field.get() for key, field in fields.items()}
            data['Capacidade'] = int(data['Capacidade'])
            data['Diária'] = float(data['Diária'])
            data['Quilometragem'] = int(data['Quilometragem'])
            data['Ano de Fabricação'] = self.validar_ano_fabricacao(data['Ano de Fabricação'])
            data['Imagem'] = data['Imagem'] if data['Imagem'] else None

            # Inserção no banco de dados
            self.cursor.execute('''
                    INSERT INTO veiculos (
                        marca, modelo, categoria, tipo, transmissao, capacidade, diaria, ultima_revisao,
                        proxima_revisao, ultima_inspecao, proxima_inspecao, cor, chassis, ano_fabricacao,
                        quilometragem, matricula, imagem, disponibilidade
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                data['Marca'], data['Modelo'], data['Categoria'], data['Tipo'], data['Transmissão'], data['Capacidade'],
                data['Diária'], data['Última Revisão'], data['Próxima Revisão'], data['Última Inspeção'],
                data['Próxima Inspeção'], data['Cor'], data['Chassis'], data['Ano de Fabricação'],
                data['Quilometragem'], data['Matrícula'], data['Imagem'], 'Disponível'
            ))
            self.conn.commit()
            self.atualizar_disponibilidade_veiculo(self.cursor.lastrowid)
            messagebox.showinfo("Sucesso", "Veículo adicionado com sucesso!")
            top.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao adicionar veículo: {e}")
    def validar_ano_fabricacao(self, ano_fabricacao):
        "Função para validar o ano de fabricação"
        try:
            if not (ano_fabricacao and len(ano_fabricacao.split('/')) == 2):
                raise ValueError("Formato inválido para Ano de Fabricação. Use MM/AAAA.")

            mes, ano = map(int, ano_fabricacao.split('/'))
            ano_atual = datetime.now().year
            mes_atual = datetime.now().month

            # Verificar se o mês está entre 1 e 12
            if not (1 <= mes <= 12):
                raise ValueError("Mês inválido. Use um valor entre 1 e 12.")

            # Verificar se o ano está no intervalo válido
            if not (1900 <= ano <= ano_atual):
                raise ValueError("Ano de fabricação inválido.")

            # Se o ano for o atual, o mês não pode ultrapassar o mês atual
            if ano == ano_atual and mes > mes_atual:
                raise ValueError("O mês de fabricação não pode ser no futuro.")

            return ano_fabricacao
        except ValueError as e:
            raise ValueError(f"Ano de fabricação: {e}")
    def listar_veiculos(self):
        try:
            self.cursor.execute('SELECT * FROM veiculos')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao listar veículos: {e}")
            return []
    def buscar_editar_veiculo(self, veiculo_id):
        try:
            self.cursor.execute('SELECT * FROM veiculos WHERE id = ?', (veiculo_id,))
            return self.cursor.fetchone()

        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao buscar veículo: {e}")
    def editar_veiculo(self, veiculo_id, valores, top):
        try:
            # Lógica de validação e atualização dos dados
            chassis, ano_fabricacao = valores[12], valores[13]
            if len(chassis) != 5 or not chassis.isdigit():
                raise ValueError("Chassis deve ser composto por 5 números.")

            self.validar_ano_fabricacao(ano_fabricacao)

            imagem = valores[16] if valores[16] else None
            valores[16] = imagem

            query = """UPDATE veiculos SET marca=?, modelo=?, categoria=?, tipo=?, transmissao=?, capacidade=?, diaria=?, 
                           ultima_revisao=?, proxima_revisao=?, ultima_inspecao=?, proxima_inspecao=?, cor=?, chassis=?, 
                           ano_fabricacao=?, quilometragem=?, matricula=?, imagem=? WHERE id=?"""

            self.cursor.execute(query, valores + [veiculo_id])
            self.conn.commit()
            self.atualizar_disponibilidade_veiculo(veiculo_id)
            messagebox.showinfo("Sucesso", f"Veículo ID {veiculo_id} editado com sucesso!")
            top.destroy()

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao editar veículo: {e}")
    def remover_veiculo(self, id_veiculo):
        try:
            self.cursor.execute('DELETE FROM veiculos WHERE id = ?', (id_veiculo,))
            self.conn.commit()
            print(f"Veículo com ID {id_veiculo} removido com sucesso.")
        except sqlite3.Error as e:
            print(f"Erro ao remover veículo: {e}")
    def buscar_veiculo(self, veiculo_id=None, matricula=None):
        try:
            # Consulta o veículo com base no ID ou matrícula
            query = 'SELECT * FROM veiculos WHERE id = ?' if veiculo_id else 'SELECT * FROM veiculos WHERE matricula = ?'
            valor = (veiculo_id,) if veiculo_id else (matricula,)
            self.cursor.execute(query, valor)
            veiculo = self.cursor.fetchone()
            return veiculo
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar veículo: {e}")
            return None
# endregion

# region Operações com Clientes
    def adicionar_cliente(self, fields, top):
        try:
            # Obtenção de dados e validações
            data = {key: field.get() for key, field in fields.items()}

            # Inserção no banco de dados
            self.cursor.execute('''INSERT INTO clientes (nome, email, telefone, endereco, documento_id)
                                       VALUES (?, ?, ?, ?, ?)''', (
                data['Nome'], data['Email'], data['Telefone'], data['Endereço'], data['Documento de Identificação']
            ))
            self.conn.commit()
            messagebox.showinfo("Sucesso", "Cliente adicionado com sucesso!")
            top.destroy()
        except ValueError:
            messagebox.showerror("Erro", "Telefone deve conter apenas números.")
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao adicionar cliente ao banco de dados: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro inesperado: {e}")

    def listar_clientes(self):
        try:
            self.cursor.execute('SELECT * FROM clientes')

            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao listar clientes: {e}")
        return []

    def buscar_editar_cliente(self, cliente_id):
        try:
            # Consultar cliente pelo ID no banco de dados
            self.cursor.execute('SELECT * FROM clientes WHERE id = ?', (cliente_id,))
            return self.cursor.fetchone()

        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao buscar cliente: {e}")

    def editar_cliente(self, cliente_id, valores, top):
        try:
            # Construção da query de atualização
            query = """UPDATE clientes SET nome=?, email=?, telefone=?, endereco=?, documento_id=? WHERE id=?"""

            # Execução da query
            self.cursor.execute(query, valores + [cliente_id])
            self.conn.commit()
            messagebox.showinfo("Sucesso", f"Cliente ID {cliente_id} editado com sucesso!")
            top.destroy()


        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao editar cliente: {e}")

    def remover_cliente(self, cliente_id):
        try:
            self.cursor.execute('DELETE FROM clientes WHERE id = ?', (cliente_id,))
            self.conn.commit()
            print(f"Cliente com ID {cliente_id} removido com sucesso.")
        except sqlite3.Error as e:
            print(f"Erro ao remover cliente: {e}")

    def buscar_cliente(self, cliente_id=None, email=None, documento_id=None):
        try:
            if cliente_id is not None:
                query = 'SELECT * FROM clientes WHERE id = ?'
                valor = (cliente_id,)
            elif email is not None:
                query = 'SELECT * FROM clientes WHERE email = ?'
                valor = (email,)
            elif documento_id is not None:
                query = 'SELECT * FROM clientes WHERE documento_id = ?'
                valor = (documento_id,)
            else:
                messagebox.showerror("Erro", "Nenhum critério de busca fornecido.")
                return

            self.cursor.execute(query, valor)
            return self.cursor.fetchone()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao buscar cliente: {e}")

# endregion

# region Operações com Formas de Pagamento
    def adicionar_forma_pagamento(self, fields, top):
        tipo = fields["Tipo"].get()
        descricao = fields["Descrição"].get()

        if not tipo:
            messagebox.showerror("Erro", "O tipo de pagamento é obrigatório.")
            return

        try:
            self.cursor.execute("INSERT INTO formas_pagamento (tipo, descricao) VALUES (?, ?)", (tipo, descricao))
            self.conn.commit()
            print(f"Forma de pagamento a '{tipo}' adicionado com sucesso.")
            top.destroy()
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao adicionar forma de pagamento: {e}")

    def listar_formas_pagamento(self):
        try:
            self.cursor.execute('SELECT * FROM formas_pagamento')

            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao listar formas de pagamento: {e}")
        return []

    def buscar_forma_pagamento(self, forma_pagamento_id):
        try:
            self.cursor.execute('SELECT * FROM formas_pagamento WHERE id = ?', (forma_pagamento_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao buscar forma de pagamento: {e}")

    def editar_forma_pagamento(self, forma_pagamento_id, valores, top):
        try:
            # Construção da query de atualização
            query = """UPDATE formas_pagamento SET tipo=?, descricao=? WHERE id=?"""

            # Execução da query
            self.cursor.execute(query, valores + [forma_pagamento_id])
            self.conn.commit()
            messagebox.showinfo("Sucesso", f"Forma de pagamento ID {forma_pagamento_id} editado com sucesso!")
            top.destroy()

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao editar forma de pagamento: {e}")

    def alterar_estado_forma_pagamento(self, forma_pagamento_id):
        try:
            # Obter o estado atual da forma de pagamento
            self.cursor.execute('SELECT ativo FROM formas_pagamento WHERE id = ?', (forma_pagamento_id,))
            estado_atual = self.cursor.fetchone()[0]

            # Alternar o estado
            novo_estado = 0 if estado_atual == 1 else 1

            # Atualizar o estado no banco de dados
            self.cursor.execute('UPDATE formas_pagamento SET ativo = ? WHERE id = ?', (novo_estado, forma_pagamento_id))
            self.conn.commit()
            messagebox.showinfo("Sucesso",
                                f"Estado da forma de pagamento ID {forma_pagamento_id} alterado com sucesso.")

        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao alterar estado da forma de pagamento: {e}")

    def remover_forma_pagamento(self, forma_pagamento_id):
        try:
            self.cursor.execute('DELETE FROM formas_pagamento WHERE id = ?', (forma_pagamento_id,))
            self.conn.commit()
            print(f"Forma de pagamento com ID {forma_pagamento_id} removido com sucesso.")
        except sqlite3.Error as e:
            print(f"Erro ao remover forma de pagamento: {e}")

# endregion

# region Operações com Reservas
    def preencher_clientes_existentes(self, widget):
        try:
            self.cursor.execute("SELECT id, nome FROM clientes")
            clientes = self.cursor.fetchall()
            widget['values'] = [f"{cliente[0]} - {cliente[1]}" for cliente in clientes]
        except sqlite3.Error as e:
            print(f"Erro ao buscar clientes existentes: {e}")

    def listar_veiculos_disponiveis(self, categoria, veiculos_frame, callback_selecionar):
        try:
            self.cursor.execute('''SELECT id, marca, modelo, tipo, transmissao, cor, capacidade, quilometragem, matricula, diaria
                                       FROM veiculos
                                       WHERE categoria = ? AND disponibilidade = 'Disponível' ''', (categoria,))
            veiculos = self.cursor.fetchall()

            for widget in veiculos_frame.winfo_children():
                widget.destroy()

            if not veiculos:
                tk.Label(veiculos_frame, text="Nenhum veículo disponível para a categoria selecionada.").pack(pady=5)
                return

            for veiculo in veiculos:
                veiculo_texto = f"{veiculo[1]} {veiculo[2]} {veiculo[3]} {veiculo[4]} {veiculo[5]} - Capacidade: {veiculo[6]} pessoas - Quilometragem: {veiculo[7]}Kms - Matrícula: {veiculo[8]} - Diária: {veiculo[9]}€"
                tk.Label(veiculos_frame, text=veiculo_texto).pack(anchor='w')

                btn_selecionar = tk.Button(
                    veiculos_frame,
                    text="Selecionar",
                    command=lambda v=veiculo: callback_selecionar(v)
                )
                btn_selecionar.pack(anchor='e')

        except sqlite3.Error as e:
            print(f"Erro ao buscar veículos disponíveis: {e}")

    def preencher_formas_pagamento(self, widget):
        try:
            self.cursor.execute("SELECT id, tipo FROM formas_pagamento")
            formas_pagamento = self.cursor.fetchall()
            widget['values'] = [f"{forma[0]} - {forma[1]}" for forma in formas_pagamento]
        except sqlite3.Error as e:
            print(f"Erro ao buscar formas de pagamento: {e}")

    def adicionar_reserva(self, fields, novo_cliente_var, top):
        try:
            # Verificar se a data de fim é posterior à data de início
            data_inicio = datetime.strptime(fields["Data Início"].get(), '%d-%m-%Y')
            data_fim = datetime.strptime(fields["Data Fim"].get(), '%d-%m-%Y')
            if data_fim <= data_inicio:
                messagebox.showerror("Erro", "A data de fim deve ser posterior à data de início.")
                return

            # Verificar se o veículo está disponível durante o período de reserva
            id_veiculo = fields["Selecionar Veículo"].get().split(' ')[0]
            if self.verificar_disponibilidade_veiculo(id_veiculo, data_inicio, data_fim):
                return

            # Verificar se cliente é novo ou existente e pegar os dados apropriados
            if novo_cliente_var.get():
                nome = fields["Nome (Novo Cliente)"].get()
                email = fields["Email (Novo Cliente)"].get()
                telefone = fields["Telefone (Novo Cliente)"].get()
                endereco = fields["Endereço (Novo Cliente)"].get()
                documento_id = fields["Documento ID (Novo Cliente)"].get()

                try:
                    self.cursor.execute(
                        "INSERT INTO clientes (nome, email, telefone, endereco, documento_id) VALUES (?, ?, ?, ?, ?)",
                        (nome, email, telefone, endereco, documento_id))
                    self.conn.commit()
                    id_cliente = self.cursor.lastrowid
                except sqlite3.Error as e:
                    messagebox.showerror("Erro", f"Erro ao adicionar novo cliente: {e}")
                    return
            else:
                id_cliente = fields["Cliente Existente"].get().split(' ')[0]

            forma_pagamento = fields["Forma de Pagamento"].get().split(' ')[0]

            # Calcular valor total com base na diária do veículo e na duração da reserva
            self.cursor.execute("SELECT diaria FROM veiculos WHERE id = ?", (id_veiculo,))
            diaria = self.cursor.fetchone()[0]
            dias_reserva = (data_fim - data_inicio).days + 1
            valor_total = diaria * dias_reserva

            # Formatar as datas antes de armazená-las
            data_inicio_formatada = data_inicio.strftime('%d-%m-%Y')
            data_fim_formatada = data_fim.strftime('%d-%m-%Y')

            self.cursor.execute(
                "INSERT INTO reservas (id_cliente, id_veiculo, data_inicio, data_fim, valor_total, id_forma_pagamento) VALUES (?, ?, ?, ?, ?, ?)",
                (id_cliente, id_veiculo, data_inicio_formatada, data_fim_formatada, valor_total, forma_pagamento))
            self.conn.commit()
            self.atualizar_disponibilidade_veiculo(id_veiculo)


            messagebox.showinfo("Sucesso", "Reserva adicionada com sucesso!")
            top.destroy()

        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao adicionar reserva: {e}")

    def verificar_disponibilidade_veiculo(self, id_veiculo, data_inicio, data_fim):
        try:
            # Obter a data de próxima revisão (ajuste conforme seu modelo de dados)
            self.cursor.execute("SELECT proxima_revisao, proxima_inspecao FROM veiculos WHERE id = ?",
                                (id_veiculo,))
            periodo_inspecao = self.cursor.fetchone()
            if periodo_inspecao:
                proxima_revisao_str, proxima_inspecao_str = periodo_inspecao
                if proxima_revisao_str and proxima_inspecao_str:
                    # Convertendo datas para o formato datetime
                    proxima_revisao = datetime.strptime(proxima_revisao_str, '%d-%m-%Y')
                    proxima_inspecao = datetime.strptime(proxima_inspecao_str, '%d-%m-%Y')

                    # Calculando o período de inspeção
                    data_inicio_revisao = proxima_revisao - timedelta(days=1)
                    data_fim_revisao = proxima_inspecao

                    # Convertendo data_inicio e data_fim para datetime se necessário
                    if isinstance(data_inicio, datetime):
                        data_inicio_dt = data_inicio
                    else:
                        data_inicio_dt = datetime.combine(data_inicio, datetime.min.time())

                    if isinstance(data_fim, datetime):
                        data_fim_dt = data_fim
                    else:
                        data_fim_dt = datetime.combine(data_fim, datetime.min.time())

                    # Verificar se o período da reserva coincide com o período de inspeção
                    if data_inicio_dt < data_fim_revisao and data_fim_dt > data_inicio_revisao:
                        messagebox.showwarning("Aviso",
                                               f"O veículo estará em inspeção de {data_inicio_revisao.date()} até {data_fim_revisao.date()}. Por favor, escolha outro veículo.")
                        return True

            # Verificar se o veículo está reservado no período
            self.cursor.execute('''SELECT data_inicio, data_fim FROM reservas
                                   WHERE id_veiculo = ? AND (? < data_fim AND ? > data_inicio)''',
                                (id_veiculo, data_fim, data_inicio))
            reserva = self.cursor.fetchone()

            if reserva:
                data_inicio_reserva_str, data_fim_reserva_str = reserva
                # Converter datas da reserva para datetime
                data_inicio_reserva = datetime.strptime(data_inicio_reserva_str, '%d-%m-%Y')
                data_fim_reserva = datetime.strptime(data_fim_reserva_str, '%d-%m-%Y')
                if data_inicio_dt < data_fim_reserva and data_fim_dt > data_inicio_reserva:

                    messagebox.showwarning("Aviso",
                                           f"O veículo estará reservado de {data_inicio_reserva} até {data_fim_reserva}. Por favor, escolha outro veículo.")
                    return True


            return False

        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao verificar disponibilidade do veículo: {e}")
            return True

    def listar_reservas(self):
        try:
            query = '''SELECT reservas.id, reservas.data_inicio, reservas.data_fim,
                                          clientes.id, clientes.nome,
                                          veiculos.id, veiculos.marca, veiculos.modelo,
                                          formas_pagamento.id, formas_pagamento.tipo,
                                          reservas.valor_total
                                   FROM reservas
                                   JOIN clientes ON reservas.id_cliente = clientes.id
                                   JOIN veiculos ON reservas.id_veiculo = veiculos.id
                                   JOIN formas_pagamento ON reservas.id_forma_pagamento = formas_pagamento.id'''
            self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Erro ao listar reservas: {e}")
        return []

    def buscar_editar_reserva(self, reserva_id):
        try:
            # Buscar os dados da reserva a ser editada
            self.cursor.execute('''SELECT reservas.id, reservas.id_cliente, reservas.id_veiculo, reservas.id_forma_pagamento,
                                                     reservas.data_inicio, reservas.data_fim, reservas.valor_total,
                                                     clientes.nome, veiculos.marca, veiculos.modelo,
                                                     formas_pagamento.tipo, veiculos.diaria
                                              FROM reservas
                                              JOIN clientes ON reservas.id_cliente = clientes.id
                                              LEFT JOIN veiculos ON reservas.id_veiculo = veiculos.id
                                              LEFT JOIN formas_pagamento ON reservas.id_forma_pagamento = formas_pagamento.id
                                              WHERE reservas.id = ?''', (reserva_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao buscar reserva: {e}")

    def editar_reserva(self, reserva_id, fields, top):
        try:
            # Validar dados editados
            if "Data Início" not in fields or "Data Fim" not in fields:
                messagebox.showerror("Erro", "As datas de início e fim devem estar presentes.")
                return

            data_inicio_str = fields["Data Início"]  # Direto, pois já chamamos get_date() na função anterior
            data_fim_str = fields["Data Fim"]

            # Verificar se as variáveis são do tipo str
            if isinstance(data_inicio_str, str):
                data_inicio = datetime.strptime(data_inicio_str, '%d-%m-%Y')
            else:
                data_inicio = data_inicio_str  # Se já for datetime.date

            if isinstance(data_fim_str, str):
                data_fim = datetime.strptime(data_fim_str, '%d-%m-%Y')
            else:
                data_fim = data_fim_str  # Se já for datetime.date

            if data_fim <= data_inicio:
                messagebox.showerror("Erro", "A data de fim deve ser posterior à data de início.")
                return

            # Obter dados da reserva original
            self.cursor.execute('''SELECT id_veiculo, id_forma_pagamento, data_inicio, data_fim
                                      FROM reservas WHERE id = ?''', (reserva_id,))
            reserva_original = self.cursor.fetchone()
            if not reserva_original:
                messagebox.showerror("Erro", "Reserva não encontrada.")
                return

            veiculo_anterior_id = reserva_original[0]
            forma_pagamento_anterior_id = reserva_original[1]

            # Obter novo veículo selecionado
            veiculo_selecionado = fields["Veículo Selecionado"]
            if veiculo_selecionado:
                id_veiculo = veiculo_selecionado.split(' ')[0]
            else:
                id_veiculo = veiculo_anterior_id

            # Obter nova forma de pagamento selecionada
            forma_pagamento_selecionada = fields.get("Forma de Pagamento")
            if forma_pagamento_selecionada:
                id_forma_pagamento = forma_pagamento_selecionada.split(' ')[0]
            else:
                id_forma_pagamento = forma_pagamento_anterior_id

            # Recalcular valor total com base no novo veículo selecionado
            if id_veiculo != veiculo_anterior_id:
                if self.verificar_disponibilidade_veiculo(id_veiculo, data_inicio, data_fim):
                    return

                self.cursor.execute("SELECT diaria FROM veiculos WHERE id = ?", (id_veiculo,))
                diaria_resultado = self.cursor.fetchone()
                if diaria_resultado:
                    diaria = diaria_resultado[0]
                else:
                    messagebox.showerror("Erro", "Veículo selecionado não encontrado.")
                    return

                dias_reserva = (data_fim - data_inicio).days + 1
                valor_total = diaria * dias_reserva
            else:
                # Usar o valor total existente se o veículo não mudar
                self.cursor.execute('SELECT valor_total FROM reservas WHERE id = ?', (reserva_id,))
                valor_total = self.cursor.fetchone()[0]

            # Atualizar reserva no banco de dados
            self.cursor.execute(
                "UPDATE reservas SET id_veiculo = ?, id_forma_pagamento = ?, data_inicio = ?, data_fim = ?, valor_total = ? WHERE id = ?",
                (id_veiculo, id_forma_pagamento, data_inicio.strftime('%d-%m-%Y'), data_fim.strftime('%d-%m-%Y'), valor_total, reserva_id))
            self.conn.commit()
            self.atualizar_disponibilidade_veiculo(id_veiculo)


            messagebox.showinfo("Sucesso", "Reserva editada com sucesso!")
            top.destroy()

        except sqlite3.Error as e:
            messagebox.showerror("Erro", f"Erro ao editar reserva: {e}")

    def remover_reserva(self, reserva_id):
        try:
            self.cursor.execute('DELETE FROM reservas WHERE id = ?', (reserva_id,))
            self.conn.commit()
            print(f"Reserva com ID {reserva_id} removida com sucesso.")
        except sqlite3.Error as e:
            print(f"Erro ao remover reserva: {e}")

    def buscar_reserva(self, id_reserva):
        try:
            query = '''
                        SELECT reservas.id, reservas.id_cliente, reservas.id_veiculo, reservas.id_forma_pagamento,
                               reservas.data_inicio, reservas.data_fim, reservas.valor_total,
                               clientes.nome, veiculos.marca, veiculos.modelo, veiculos.matricula, formas_pagamento.tipo
                        FROM reservas
                        JOIN clientes ON reservas.id_cliente = clientes.id
                        LEFT JOIN veiculos ON reservas.id_veiculo = veiculos.id
                        LEFT JOIN formas_pagamento ON reservas.id_forma_pagamento = formas_pagamento.id
                        WHERE reservas.id = ?
                    '''

            self.cursor.execute(query, (id_reserva,))
            return self.cursor.fetchone()  # Retorna os resultados da busca

        except sqlite3.Error as e:
            print(f"Erro ao buscar reserva: {e}")
            return []



# endregion


    def fechar_conexao(self):
        try:
            self.conn.close()
            print("Conexão com o banco de dados fechada.")
        except sqlite3.Error as e:
            print(f"Erro ao fechar conexão com o banco de dados: {e}")
