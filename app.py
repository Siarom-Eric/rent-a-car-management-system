import tkinter as tk
from dataManager import DataManager
from dashboardUI import DashboardUI
from login import LoginRegister


class App:
    def __init__(self, root):
        self.root = root
        self.default_title = "Sistema de Gestão Luxuary Wheels"  # Título padrão
        self.default_geometry = "1500x900"  # Dimensão padrão

        # Configurar título e dimensões iniciais
        self.root.title(self.default_title)
        self.root.geometry(self.default_geometry)

        # Inicializar o banco de dados
        self.data_manager = DataManager()

        # Exibir a tela de login primeiro
        self.show_login_screen()

    def __del__(self):
        self.data_manager.fechar_conexao()

    def show_login_screen(self):
        """ Cria a tela de login. """
        self.clear_window()
        # Alterar título e dimensão para a tela de login
        self.root.title("Login")
        self.root.geometry("300x200")
        self.login_screen = LoginRegister(self)

    def show_dashboard(self):
        """ Exibe o Dashboard após login bem-sucedido. """
        self.clear_window()
        self.root.title(self.default_title)
        self.root.geometry(self.default_geometry)
        self.dashboard = DashboardUI(self.root, self.data_manager)

    def clear_window(self):
        """ Limpa todos os widgets da janela. """
        for widget in self.root.winfo_children():
            widget.destroy()


# Executar a aplicação
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    try:
        root.mainloop()
    finally:
        app.__del__()  # Fechar conexão com o banco de dados ao encerrar a aplicação