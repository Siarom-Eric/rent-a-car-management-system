import tkinter as tk
from tkinter import messagebox
from register import RegisterWindow
import sqlite3
import hashlib
from datetime import datetime

class LoginRegister:
    def __init__(self, app):
        self.app = app
        self.root = app.root

        self.create_widgets()

    def create_widgets(self):
        # Labels and Entries for Login
        tk.Label(self.root, text="Email").pack(pady=5)
        self.email_entry = tk.Entry(self.root)
        self.email_entry.pack(pady=5)

        tk.Label(self.root, text="Senha").pack(pady=5)
        self.senha_entry = tk.Entry(self.root, show="*")
        self.senha_entry.pack(pady=5)

        tk.Button(self.root, text="Login", command=self.login).pack(pady=5)
        tk.Button(self.root, text="Registrar", command=self.open_register_window).pack(pady=5)

    def open_register_window(self):
        RegisterWindow(self.root)

    def login(self):
        email = self.email_entry.get()
        senha = self.senha_entry.get()

        if self.authenticate_user(email, senha):
            messagebox.showinfo("Login", "Login bem-sucedido!")
            self.update_last_login(email)   # Atualiza o último login

            # Mostrar o Dashboard
            self.app.show_dashboard()

        else:
            messagebox.showerror("Login", "Email ou senha incorretos.")

    def authenticate_user(self, email, senha):
        conn = sqlite3.connect('aluguel_carros.db')
        cursor = conn.cursor()
        cursor.execute("SELECT senha_hash FROM usuarios WHERE email=?", (email,))
        result = cursor.fetchone()
        conn.close()

        if result and self.hash_password(senha) == result[0]:
            return True
        return False

    def hash_password(self, senha):
        return hashlib.sha256(senha.encode()).hexdigest()

    def update_last_login(self, email):
        """ Atualiza o timestamp do último acesso do usuário após o login bem-sucedido. """
        conn = sqlite3.connect('aluguel_carros.db')  # Atualizado para usar o banco de dados correto
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET ultimo_acesso = ? WHERE email = ?", (datetime.now(), email))
        conn.commit()
        conn.close()