import os
import shutil
import winreg
import webbrowser
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageOps, ImageDraw
from tkinter import messagebox, filedialog
import urllib.request
import xml.etree.ElementTree as ET

# Настройка темы интерфейса
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def get_account_avatar(account_id, size=(32, 32)):
    """Пытается загрузить аватарку аккаунта через Steam Community XML по SteamID64"""
    cache_dir = "cache_avatars"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{account_id}.png")

    # Если аватарка уже есть в локальном кэше — берем её оттуда
    if os.path.exists(cache_path):
        try:
            img = Image.open(cache_path)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
        except Exception:
            pass

    # Иначе пробуем вытянуть через Steam Community XML
    try:
        steam_id_64 = int(account_id) + 76561197960265728
        xml_url = f"https://steamcommunity.com/profiles/{steam_id_64}/?xml=1"
        
        req = urllib.request.Request(xml_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=2) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        avatar_elem = root.find('avatarMedium')
        
        if avatar_elem is not None and avatar_elem.text:
            img_url = avatar_elem.text
            urllib.request.urlretrieve(img_url, cache_path)
            
            img = Image.open(cache_path)
            return ctk.CTkImage(light_image=img, dark_image=img, size=size)
            
    except Exception:
        pass

    return None

def get_steam_path():
    """Автоматически находит путь к Steam через реестр Windows"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
        return os.path.normpath(steam_path)
    except Exception:
        return None

def get_steam_accounts(steam_path):
    """Сканирует папку userdata и находит все ID аккаунтов"""
    userdata_path = os.path.join(steam_path, "userdata")
    accounts = []
    
    if os.path.exists(userdata_path):
        for folder_name in os.listdir(userdata_path):
            folder_path = os.path.join(userdata_path, folder_name)
            if os.path.isdir(folder_path) and folder_name.isdigit() and folder_name != "0":
                accounts.append(folder_name)
    return accounts

class AccountSelector(ctk.CTkToplevel):

    """Окно выбора аккаунта со скроллом и аватарками"""
    def __init__(self, parent, accounts, steam_path):
        super().__init__(parent)
        self.title("Сменить аккаунт")
        
        # --- Центрирование и фиксированный размер окна ---
        window_width = 480
        window_height = 280
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)
        self.attributes("-toolwindow", True) # Убирает кнопки сворачивания и развертывания
        
        # Делаем окно модальным
        self.grab_set()
        self.selected_account = None

        lbl_title = ctk.CTkLabel(self, text="Сменить аккаунт", font=("Arial", 18, "bold"))
        lbl_title.pack(pady=15)
        
        lbl_sub = ctk.CTkLabel(self, text="Выберите аккаунт для работы с конфигами", font=("Arial", 12), text_color="gray")
        lbl_sub.pack(pady=5)

        # Создаем скроллируемый фрейм (горизонтальный)
        self.scroll_frame = ctk.CTkScrollableFrame(self, orientation="horizontal", width=420, height=140, fg_color="transparent")
        self.scroll_frame.pack(pady=10, padx=20)

        for acc_id in accounts:
            avatar_img = self.load_account_avatar(steam_path, acc_id)

            btn_acc = ctk.CTkButton(
                self.scroll_frame, 
                text=f"\n{acc_id}", 
                image=avatar_img,
                compound="top",
                width=100, 
                height=120,
                corner_radius=10,
                font=("Arial", 11, "bold"),
                fg_color="#2b2b2b",
                hover_color="#383838",
                command=lambda aid=acc_id: self.choose_account(aid)
            )
            btn_acc.pack(side="left", padx=8)

    def load_accounts(self):
        # Очищаем старые элементы перед перезагрузкой
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.accounts:
            lbl_empty = ctk.CTkLabel(self.scroll_frame, text="Аккаунты Steam не найдены.", text_color="gray")
            lbl_empty.pack(pady=20)
            return

        for acc_id in self.accounts:
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b", corner_radius=6)
            row_frame.pack(fill="x", pady=4, padx=5)

            # Пытаемся получить аватарку аккаунта
            avatar_image = get_account_avatar(acc_id, size=(32, 32))

            if avatar_image:
                lbl_avatar = ctk.CTkLabel(row_frame, text="", image=avatar_image)
                lbl_avatar.pack(side="left", padx=10, pady=6)
            else:
                # Заглушка, если нет интернета или профиль закрыт/не найден
                lbl_avatar = ctk.CTkLabel(row_frame, text="👤", font=("Arial", 14), width=32)
                lbl_avatar.pack(side="left", padx=10, pady=6)

            # ID аккаунта
            lbl_id = ctk.CTkLabel(row_frame, text=f"ID: {acc_id}", font=("Arial", 12, "bold"))
            lbl_id.pack(side="left", padx=5, pady=10)

            # Кнопка выбора аккаунта
            btn_select = ctk.CTkButton(
                row_frame, 
                text="Выбрать", 
                width=90, 
                height=28,
                command=lambda a=acc_id: self.select_account(a)
            )
            btn_select.pack(side="right", padx=10)

    def choose_account(self, acc_id):
        self.selected_account = acc_id
        self.destroy()

class DemoManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent, demos_path):
        super().__init__(parent)
        self.title("Менеджер демо-записей CS2")
        
        # Размеры и центрирование окна
        window_width = 500
        window_height = 400
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)
        self.attributes("-toolwindow", True)
        self.grab_set()

        self.demos_path = demos_path

        # Заголовок
        lbl_title = ctk.CTkLabel(self, text="Найденные демо-записи (.dem)", font=("Arial", 16, "bold"))
        lbl_title.pack(pady=10)

        # Прокручиваемая область для списка демок
        self.scroll_frame = ctk.CTkScrollableFrame(self, width=460, height=260, fg_color="transparent")
        self.scroll_frame.pack(pady=5, padx=20)

        # Нижняя панель с кнопками управления
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=10)

        self.btn_open_dir = ctk.CTkButton(self.btn_frame, text="📁 Открыть папку", command=self.open_folder, width=140, fg_color="#333333", hover_color="#444444")
        self.btn_open_dir.pack(side="left", padx=5)

        self.btn_refresh = ctk.CTkButton(self.btn_frame, text="🔄 Обновить список", command=self.load_demos, width=140, fg_color="#333333", hover_color="#444444")
        self.btn_refresh.pack(side="left", padx=5)

        # Загружаем список при открытии
        self.load_demos()

    def load_demos(self):
        # Очищаем старые элементы в скролл-зоне
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not os.path.exists(self.demos_path):
            lbl_empty = ctk.CTkLabel(self.scroll_frame, text="Папка с демками не найдена.", text_color="gray")
            lbl_empty.pack(pady=20)
            return

        # Ищем все .dem файлы
        dem_files = [f for f in os.listdir(self.demos_path) if f.endswith('.dem')]

        if not dem_files:
            lbl_empty = ctk.CTkLabel(self.scroll_frame, text="Демо-записи не найдены.", text_color="gray")
            lbl_empty.pack(pady=20)
            return

        # Сортируем по времени изменения (свежие сверху)
        dem_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.demos_path, x)), reverse=True)

        for dem in dem_files:
            file_path = os.path.join(self.demos_path, dem)
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b", corner_radius=6)
            row_frame.pack(fill="x", pady=4, padx=5)

            # Название файла и размер
            lbl_name = ctk.CTkLabel(row_frame, text=dem, font=("Arial", 11), anchor="w", width=280)
            lbl_name.pack(side="left", padx=10, pady=8)

            lbl_size = ctk.CTkLabel(row_frame, text=f"{file_size_mb:.1f} MB", font=("Arial", 10), text_color="gray", width=60)
            lbl_size.pack(side="left", padx=5)

            # Кнопка удаления конкретной демки
            btn_delete = ctk.CTkButton(
                row_frame, 
                text="❌", 
                width=30, 
                height=25, 
                fg_color="#552222", 
                hover_color="#772222",
                command=lambda p=file_path, name=dem: self.delete_demo(p, name)
            )
            btn_delete.pack(side="right", padx=8)

    def delete_demo(self, file_path, name):
        if messagebox.askyesno("Подтверждение", f"Удалить демку?\n{name}"):
            try:
                os.remove(file_path)
                self.load_demos() # Перезагружаем список
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить файл:\n{str(e)}")
    def open_folder(self):
        if os.path.exists(self.demos_path):
            os.startfile(self.demos_path)

class CS2HelperApp(ctk.CTk):
    def __init__(self):
        super().__init__()


        self.title("CS2 Quick Utils")
       # Устанавливаем размер окна
        window_width = 500
        window_height = 450
        
        # Вычисляем координаты для центра экрана
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        # Применяем размер и позицию за один раз
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)

        self.steam_path = get_steam_path()
        self.current_account = None

        if not self.steam_path:
            messagebox.showerror("Ошибка", "Не удалось найти установленный Steam в реестре!")
            self.destroy()
            return
        
        self.accounts = get_steam_accounts(self.steam_path)
        if self.accounts:
            self.current_account = self.accounts[0]

        # --- Интерфейс ---
        self.label_title = ctk.CTkLabel(self, text="CS2 Config Manager", font=("Arial", 18, "bold"))
        self.label_title.pack(pady=20)

        self.lbl_acc_info = ctk.CTkLabel(self, text=f"Активный аккаунт (ID): {self.current_account}", font=("Arial", 11), text_color="cyan")
        self.lbl_acc_info.pack(pady=5)

        # --- Кликабельная подсказка-ссылка ---
        self.lbl_link = ctk.CTkLabel(
            self, 
            text="Где найти ID в Steam?", 
            font=("Arial", 11, "underline"), 
            text_color="#3399ff", 
            cursor="hand2"
            )
        
        self.lbl_link.pack(pady=(0, 5))
        # При клике открывается страница обмена/трейд-ссылки в браузере
        self.lbl_link.bind("<Button-1>", lambda e: webbrowser.open("https://steamcommunity.com/my/tradeoffers/privacy"))
        # -------------------------------------

        self.btn_change_acc = ctk.CTkButton(self, text="Сменить аккаунт", command=self.open_account_window, width=280, height=35, fg_color="#333333", hover_color="#444444")
        self.btn_change_acc.pack(pady=5)

        self.btn_save = ctk.CTkButton(self, text="Сохранить конфиг", command=self.save_config, width=280, height=40)
        self.btn_save.pack(pady=10)

        self.btn_open_cfg = ctk.CTkButton(self, text="Открыть папку CFG игры", command=self.open_cfg_folder, width=280, height=40, fg_color="gray")
        self.btn_open_cfg.pack(pady=10)

        # Кнопка Открытие userdata
        self.btn_open_userdata = ctk.CTkButton(self, text="Открыть папку userdata", command=self.open_userdata_folder, width=280, height=35, fg_color="#333333", hover_color="#444444")
        self.btn_open_userdata.pack(pady=5)

        # --- Кнопка очистки кэша ---
        self.btn_clear_cache = ctk.CTkButton(self, text="Очистить кэш игры", command=self.clear_game_cache, width=280, height=35, fg_color="#333333", hover_color="#444444")
        self.btn_clear_cache.pack(pady=5)
        # ---------------------------------

        # --- Новая кнопка для демок ---
        self.btn_demos = ctk.CTkButton(self, text="🎬 Управление демками (.dem)", command=self.open_demos_folder, width=280, height=35, fg_color="#333333", hover_color="#444444")
        self.btn_demos.pack(pady=5)
        # -----------------------------

    def open_account_window(self):
        if not self.accounts:
            messagebox.showwarning("Внимание", "Аккаунты не найдены в папке userdata.")
            return
        
        selector = AccountSelector(self, self.accounts, self.steam_path)
        self.wait_window(selector)
        
        if selector.selected_account:
            self.current_account = selector.selected_account
            self.lbl_acc_info.configure(text=f"Активный аккаунт (ID): {self.current_account}")

    def get_current_cfg_path(self):
        if self.current_account:
            userdata_cfg = os.path.join(self.steam_path, "userdata", self.current_account, "730", "remote")
            if os.path.exists(userdata_cfg):
                return userdata_cfg
                
        return os.path.join(self.steam_path, "steamapps", "common", "Counter-Strike Global Offensive", "game", "csgo")

    def save_config(self):
        try:
            # Получаем путь к папке 730 для выбранного аккаунта
            target_cfg_path = self.get_current_cfg_path()
            
            # Находим родительскую папку remote
            remote_path = os.path.dirname(target_cfg_path) if target_cfg_path.endswith("cfg") else target_cfg_path
            
            if not os.path.exists(remote_path):
                messagebox.showerror("Ошибка", f"Папка remote не найдена по пути:\n{remote_path}")
                return

            # Папка по умолчанию для предложения в диалоговом окне
            default_dir = os.path.expanduser(r"~\Documents\CS2_Backups")
            if not os.path.exists(default_dir):
                os.makedirs(default_dir, exist_ok=True)
                
            # Имя файла по умолчанию с датой, временем и ID аккаунта
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            default_filename = f"remote_backup_ID_{self.current_account}_{timestamp}.zip"
            
            # Открываем системное окно «Сохранить как»
            file_path = filedialog.asksaveasfilename(
                initialdir=default_dir,
                initialfile=default_filename,
                defaultextension=".zip",
                filetypes=[("ZIP архивы", "*.zip"), ("Все файлы", "*.*")],
                title="Сохранить бэкап настроек CS2"
            )
            
            # Если пользователь нажал «Отмена», просто выходим из функции
            if not file_path:
                return
            
            # shutil.make_archive требует путь БЕЗ расширения .zip на конце
            base_archive_path = file_path[:-4] if file_path.lower().endswith('.zip') else file_path
            
            # Создаем архив
            shutil.make_archive(base_archive_path, 'zip', remote_path)
            
            messagebox.showinfo(
                "Успех", 
                f"Архив успешно создан!\n\nФайл сохранен:\n{file_path}"
            )
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать архив: {str(e)}")

    def open_userdata_folder(self):
        """Открывает корневую папку userdata со всеми ID аккаунтов"""
        if self.steam_path:
            userdata_path = os.path.join(self.steam_path, "userdata")
            if os.path.exists(userdata_path):
                os.startfile(userdata_path)
            else:
                messagebox.showerror("Ошибка", f"Папка userdata не найдена по пути:\n{userdata_path}")
        else:
            messagebox.showerror("Ошибка", "Путь к Steam не определен.")

    def open_cfg_folder(self):
        target_cfg_path = self.get_current_cfg_path()
        if os.path.exists(target_cfg_path):
            os.startfile(target_cfg_path)
        else:
            fallback_path = os.path.join(self.steam_path, "steamapps", "common", "Counter-Strike Global Offensive", "game", "csgo", "cfg")
            if os.path.exists(fallback_path):
                os.startfile(fallback_path)
            else:
                messagebox.showerror("Ошибка", "Папка с конфигами не найдена.")

    def clear_game_cache(self):
        """Очистка кэша карт Мастерской и шейдеров CS2"""
        if not self.steam_path:
            messagebox.showerror("Ошибка", "Путь к Steam не определен.")
            return

        # Путь к картам Мастерской CS2 и кэшу шейдеров
        workshop_path = os.path.join(self.steam_path, "steamapps", "workshop", "content", "730")
        shader_cache_path = os.path.join(self.steam_path, "steamapps", "shadercache", "730")

        # Запрос подтверждения у пользователя перед удалением
        confirm = messagebox.askyesno(
            "Очистка кэша CS2",
            "Это действие очистит скачанные карты из Мастерской Steam и кэш шейдеров игры (App ID 730).\n\n"
            "Это поможет освободить место и избавиться от возможных фризов.\n\nПродолжить?"
        )

        if not confirm:
            return

        deleted_something = False
        try:
            # Очищаем содержимое папки мастерской 730
            if os.path.exists(workshop_path):
                for item in os.listdir(workshop_path):
                    item_path = os.path.join(workshop_path, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    else:
                        os.remove(item_path)
                deleted_something = True

            # Очищаем кэш шейдеров 730
            if os.path.exists(shader_cache_path):
                for item in os.listdir(shader_cache_path):
                    item_path = os.path.join(shader_cache_path, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    else:
                        os.remove(item_path)
                deleted_something = True

            if deleted_something:
                messagebox.showinfo("Успех", "Кэш и временные файлы CS2 успешно очищены!")
            else:
                messagebox.showinfo("Информация", "Временные файлы CS2 не найдены (папки уже пусты).")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось полностью очистить кэш:\n{str(e)}")

    def open_demos_folder(self):
        """Открывает окно управления демо-записями CS2"""
        if not self.steam_path:
            messagebox.showerror("Ошибка", "Путь к Steam не определен.")
            return

        demos_path = os.path.join(self.steam_path, "steamapps", "common", "Counter-Strike Global Offensive", "game", "csgo")
        
        # Просто открываем наше модальное окно
        DemoManagerWindow(self, demos_path)
        
if __name__ == "__main__":
    app = CS2HelperApp()
    app.mainloop()