import customtkinter as ctk
import plotly.graph_objects as go
from plotly.offline import plot
import tempfile
import webbrowser
from tkinter import ttk

class StatsWindow(ctk.CTkToplevel):
    def __init__(self, parent, drop_collector):
        super().__init__(parent)
        self.parent = parent
        self.drop_collector = drop_collector
        self.title("Статистика дропа")
        self.geometry("800x600")
        self.transient(parent)
        self.grab_set()

        self.stats = drop_collector.get_stats()
        self.create_widgets()

    def create_widgets(self):
        card_frame = ctk.CTkFrame(self)
        card_frame.pack(pady=10, padx=10, fill="x")

        stats = [
            ("Сегодня", self.stats['today'], "#4CAF50"),
            ("Неделя", self.stats['week'], "#2196F3"),
            ("Месяц", self.stats['month'], "#FF9800"),
            ("Всего", self.stats['total'], "#9C27B0"),
        ]

        for i, (label, value, color) in enumerate(stats):
            card = ctk.CTkFrame(card_frame, fg_color=color, corner_radius=10)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            card_frame.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=label, font=("Segoe UI", 14, "bold"), text_color="white").pack(pady=5)
            ctk.CTkLabel(card, text=str(value), font=("Segoe UI", 20, "bold"), text_color="white").pack(pady=5)

        ctk.CTkButton(self, text="📊 Открыть интерактивный график", command=self.show_interactive_plot,
                     font=("Segoe UI", 14), height=40).pack(pady=10)

        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ["Аккаунт", "Дроп всего"]
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        tree.heading("Аккаунт", text="Аккаунт")
        tree.heading("Дроп всего", text="Дроп всего")
        tree.column("Аккаунт", width=250)
        tree.column("Дроп всего", width=150)

        for acc in self.stats['per_account']:
            tree.insert("", "end", values=(acc['username'], acc['drop']))

        tree.pack(side="left", fill="both", expand=True)
        scrollbar = ctk.CTkScrollbar(table_frame, command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)

    def show_interactive_plot(self):
        accounts = [a['username'] for a in self.stats['per_account']]
        drops = [a['drop'] for a in self.stats['per_account']]

        fig = go.Figure(data=[
            go.Bar(x=accounts, y=drops, marker_color='#4CAF50', text=drops, textposition='auto')
        ])
        fig.update_layout(
            title="Распределение дропа по аккаунтам",
            xaxis_title="Аккаунт",
            yaxis_title="Дроп всего",
            template="plotly_dark" if ctk.get_appearance_mode() == "Dark" else "plotly_white"
        )

        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            fig.write_html(tmp.name)
            webbrowser.open(f"file://{tmp.name}")