import customtkinter as ctk
import tkinter as tk  # Импортируем стандартный tkinter для Canvas

# Настройка темы
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class GridDemoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CS2 Helper - Grid Background Demo")
        self.geometry("460x350")
        self.resizable(False, False)

        # Используем стандартный tk.Canvas вместо ctk.CTkCanvas
        self.bg_canvas = tk.Canvas(
            self, 
            width=460, 
            height=350, 
            highlightthickness=0, 
            bg="#121212"
        )
        self.bg_canvas.pack(fill="both", expand=True)

        # Рисуем сетку из точек (шаг 24 пикселя)
        self.draw_grid_dots(spacing=24, dot_color="#222222")

        # Карточка поверх сетки
        self.card = ctk.CTkFrame(
            self, 
            fg_color="#1a1a1a", 
            corner_radius=12, 
            border_width=1, 
            border_color="#2a2a2a"
        )
        self.card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.85, relheight=0.75)

        # Содержимое карточки
        self.lbl_title = ctk.CTkLabel(
            self.card, 
            text="Пример карточки с сеткой", 
            font=("Segoe UI", 16, "bold")
        )
        self.lbl_title.pack(pady=(25, 10))

        self.lbl_sub = ctk.CTkLabel(
            self.card, 
            text="Фон выглядит стильно и технологично", 
            font=("Segoe UI", 12), 
            text_color="gray"
        )
        self.lbl_sub.pack(pady=(0, 20))

        self.btn_action = ctk.CTkButton(
            self.card, 
            text="Тестовая кнопка", 
            font=("Segoe UI", 12, "bold"),
            fg_color="#2a475e", 
            hover_color="#1b2838",
            height=36
        )
        self.btn_action.pack(pady=10, padx=30, fill="x")

    def draw_grid_dots(self, spacing, dot_color):
        """Отрисовка точечной сетки по всей площади холста"""
        width = 460
        height = 350
        for x in range(12, width, spacing):
            for y in range(12, height, spacing):
                self.bg_canvas.create_oval(
                    x, y, x + 2, y + 2, 
                    fill=dot_color, 
                    outline=dot_color
                )

if __name__ == "__main__":
    app = GridDemoApp()
    app.mainloop()