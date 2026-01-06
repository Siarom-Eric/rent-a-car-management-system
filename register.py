import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib
from datetime import datetime

class RegisterWindow:
    def __init__(self, master):
        self.master = master
        self.top = tk.Toplevel(master)
        self.top.title("Registro")
        self.top.geometry("300x250")

        self.fields = {
            "Nome": tk.Entry (self.top),
            "Email": tk.Entry(self.top),
            "Telefone": tk.Entry(self.top),
            "Senha": tk.Entry(self.top, show="*"),
            "Confirme a Senha": tk.Entry(self.top, show="*")
        }

        self.create_widgets()

    def create_widgets(self):
        """Cria dinamicamente os widgets com base no dicionário 'fields'."""
        row = 0
        for label_text, entry_widget in self.fields.items():
            tk.Label(self.top, text=label_text).grid(row=row, column=0, padx=10, pady=5, sticky="w")
            entry_widget.grid(row=row, column=1, padx=10, pady=5)
            row += 1

        # Botão de registro
        tk.Button(self.top, text="Registrar", command=self.register).grid(row=row, columnspan=2, pady=10)

    def register(self):
        # Coletar dados das entradas
        nome = self.fields["Nome"].get()
        email = self.fields["Email"].get()
        telefone = int(self.fields["Telefone"].get())
        senha = self.fields["Senha"].get()
        confirma_senha = self.fields["Confirme a Senha"].get()

        if senha != confirma_senha:
            messagebox.showerror("Registro", "As senhas não correspondem.")
            return

        if self.add_user(nome, email, telefone, senha):
            messagebox.showinfo("Registro", "Usuário registrado com sucesso!")
            self.top.destroy()
        else:
            messagebox.showerror("Registro", "Erro ao registrar usuário.")

    def add_user(self, nome, email, telefone, senha):
        hashed_senha = hashlib.sha256(senha.encode()).hexdigest()
        try:
            conn = sqlite3.connect('aluguel_carros.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (nome, email, telefone, senha_hash, data_registro) VALUES (?, ?, ?, ?, ?)",
                           (nome, email, telefone, hashed_senha, datetime.now()))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Erro ao inserir usuário: {e}")
            return False