import os
import shutil
import zipfile
import winreg
import urllib.request
import xml.etree.ElementTree as ET
from PIL import Image
import customtkinter as ctk
from tkinter import messagebox, filedialog

# Настройка темы CustomTkinter
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


class DemoManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent, demos_path):
        super().__init__(parent)
        self.title("Менеджер демо-записей CS2")
        
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

        lbl_title = ctk.CTkLabel(self, text="Найденные демо-записи (.dem)", font=("Arial", 16, "bold"))
        lbl_title.pack(pady=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=460, height=260, fg_color="transparent")
        self.scroll_frame.pack(pady=5, padx=20)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=10)

        self.btn_open_dir = ctk.CTkButton(self.btn_frame, text="📁 Открыть папку", command=self.open_folder, width=140, fg_color="#333333", hover_color="#444444")
        self.btn_open_dir.pack(side="left", padx=5)

        self.btn_refresh = ctk.CTkButton(self.btn_frame, text="🔄 Обновить список", command=self.load_demos, width=140, fg_color="#333333", hover_color="#444444")
        self.btn_refresh.pack(side="left", padx=5)

        self.load_demos()

    def load_demos(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not os.path.exists(self.demos_path):
            lbl_empty = ctk.CTkLabel(self.scroll_frame, text="Папка с демками не найдена.", text_color="gray")
            lbl_empty.pack(pady=20)
            return

        dem_files = [f for f in os.listdir(self.demos_path) if f.endswith('.dem')]

        if not dem_files:
            lbl_empty = ctk.CTkLabel(self.scroll_frame, text="Демо-записи не найдены.", text_color="gray")
            lbl_empty.pack(pady=20)
            return

        dem_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.demos_path, x)), reverse=True)

        for dem in dem_files:
            file_path = os.path.join(self.demos_path, dem)
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b", corner_radius=6)
            row_frame.pack(fill="x", pady=4, padx=5)

            lbl_name = ctk.CTkLabel(row_frame, text=dem, font=("Arial", 11), anchor="w", width=260)
            lbl_name.pack(side="left", padx=10, pady=8)

            lbl_size = ctk.CTkLabel(row_frame, text=f"{file_size_mb:.1f} MB", font=("Arial", 10), text_color="gray", width=60)
            lbl_size.pack(side="left", padx=5)

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
                self.load_demos()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить файл:\n{str(e)}")

    def open_folder(self):
        if os.path.exists(self.demos_path):
            os.startfile(self.demos_path)


class AccountSelector(ctk.CTkToplevel):
    def __init__(self, parent, accounts, callback):
        super().__init__(parent)
        self.title("Выбор аккаунта Steam")
        
        window_width = 400
        window_height = 350
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)
        self.attributes("-toolwindow", True)
        self.grab_set()

        self.accounts = accounts
        self.callback = callback
        self.selected_account = None

        lbl_title = ctk.CTkLabel(self, text="Найденные аккаунты Steam", font=("Arial", 16, "bold"))
        lbl_title.pack(pady=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=360, height=260, fg_color="transparent")
        self.scroll_frame.pack(pady=5, padx=20)

        self.load_accounts()

    def load_accounts(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.accounts:
            lbl_empty = ctk.CTkLabel(self.scroll_frame, text="Аккаунты Steam не найдены.", text_color="gray")
            lbl_empty.pack(pady=20)
            return

        for acc_id in self.accounts:
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b", corner_radius=6)
            row_frame.pack(fill="x", pady=4, padx=5)

            avatar_image = get_account_avatar(acc_id, size=(32, 32))

            if avatar_image:
                lbl_avatar = ctk.CTkLabel(row_frame, text="", image=avatar_image)
                lbl_avatar.pack(side="left", padx=10, pady=6)
            else:
                lbl_avatar = ctk.CTkLabel(row_frame, text="👤", font=("Arial", 14), width=32)
                lbl_avatar.pack(side="left", padx=10, pady=6)

            lbl_id = ctk.CTkLabel(row_frame, text=f"ID: {acc_id}", font=("Arial", 12, "bold"))
            lbl_id.pack(side="left", padx=5, pady=10)

            btn_select = ctk.CTkButton(
                row_frame, 
                text="Выбрать", 
                width=90, 
                height=28,
                command=lambda a=acc_id: self.select_account(a)
            )
            btn_select.pack(side="right", padx=10)

    def select_account(self, acc_id):
        self.selected_account = acc_id
        self.callback(acc_id)
        self.destroy()


class CS2HelperApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CS2 Config & Helper Utility")
        
        window_width = 340
        window_height = 460
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)

        self.steam_path = self.get_steam_path()
        self.current_account = None

        # Элементы интерфейса
        self.lbl_header = ctk.CTkLabel(self, text="CS2 Helper Panel", font=("Arial", 16, "bold"))
        self.lbl_header.pack(pady=15)

        self.btn_account = ctk.CTkButton(self, text="👤 Выбрать аккаунт", command=self.open_account_selector, width=280, height=35, fg_color="#1f538d", hover_color="#14375e")
        self.btn_account.pack(pady=5)

        self.btn_backup = ctk.CTkButton(self, text="💾 Сделать бэкап конфига (remote)", command=self.make_backup, width=280, height=35, fg_color="#333333", hover_color="#444444")
        self.btn_backup.pack(pady=5)

        self.btn_open_cfg = ctk.CTkButton(self, text="📂 Открыть папку cfg", command=self.open_cfg_folder, width=280, height=35, fg_color="#333333", hover_color="#444444")
        self.btn_open_cfg.pack(pady=5)

        self.btn_open_userdata = ctk.CTkButton(self, text="📂 Открыть папку userdata", command=self.open_userdata_folder, width=280, height=35, fg_color="#333333", hover_color="#444444")
        self.btn_open_userdata.pack(pady=5)

        self.btn_clear_cache = ctk.CTkButton(self, text="🧹 Очистить кэш игры", command=self.clear_game_cache, width=280, height=35, fg_color="#333333", hover_color="#444444")
        self.btn_clear_cache.pack(pady=5)

        self.btn_demos = ctk.CTkButton(self, text="🎬 Управление демками (.dem)", command=self.open_demos_folder, width=280, height=35, fg_color="#333333", hover_color="#444444")
        self.btn_demos.pack(pady=5)

        self.lbl_status = ctk.CTkLabel(self, text=f"Steam найден: {'Да' if self.steam_path else 'Нет'}", font=("Arial", 10), text_color="gray")
        self.lbl_status.pack(side="bottom", pady=10)

    def get_steam_path(self):
        """Автоматический поиск пути к Steam через реестр Windows"""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "SteamPath")
            winreg.CloseKey(key)
            return os.path.normpath(path)
        except Exception:
            return None

    def get_steam_accounts(self):
        """Сканирует папку userdata на наличие аккаунтов"""
        if not self.steam_path:
            return []
        userdata_path = os.path.join(self.steam_path, "userdata")
        if not os.path.exists(userdata_path):
            return []
        
        accounts = []
        for item in os.listdir(userdata_path):
            item_path = os.path.join(userdata_path, item)
            if os.path.isdir(item_path) and item.isdigit():
                accounts.append(item)
        return accounts

    def open_account_selector(self):
        if not self.steam_path:
            messagebox.showerror("Ошибка", "Путь к Steam не найден в реестре.")
            return
        
        accounts = self.get_steam_accounts()
        if not accounts:
            messagebox.showinfo("Информация", "В папке Steam не найдено аккаунтов.")
            return

        AccountSelector(self, accounts, self.on_account_selected)

    def on_account_selected(self, acc_id):
        self.current_account = acc_id
        self.btn_account.configure(text=f"👤 Аккаунт: {acc_id}")
        messagebox.showinfo("Выбор аккаунта", f"Выбран активный аккаунт ID: {acc_id}")

    def make_backup(self):
        """Архивирует папку remote выбранного аккаунта"""
        if not self.steam_path:
            messagebox.showerror("Ошибка", "Путь к Steam не определен.")
            return

        if not self.current_account:
            messagebox.showwarning("Внимание", "Аккаунт не выбран! Сначала выберите аккаунт через кнопку 'Выбрать аккаунт'.")
            return

        remote_path = os.path.join(self.steam_path, "userdata", self.current_account, "730", "remote")
        if not os.path.exists(remote_path):
            messagebox.showerror("Ошибка", f"Папка remote не найдена для аккаунта {self.current_account}.\nВозможно, в CS2 еще не сохранялись настройки.")
            return

        backup_file = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP архивы", "*.zip")],
            initialfile=f"cs2_backup_acc_{self.current_account}.zip"
        )

        if not backup_file:
            return

        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(remote_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, remote_path)
                        zipf.write(file_path, arcname)
            
            messagebox.showinfo("Успех", f"Бэкап успешно создан!\n{backup_file}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать архив:\n{str(e)}")

    def open_cfg_folder(self):
        if not self.steam_path:
            messagebox.showerror("Ошибка", "Путь к Steam не определен.")
            return
        cfg_path = os.path.join(self.steam_path, "steamapps", "common", "Counter-Strike Global Offensive", "game", "csgo", "cfg")
        if os.path.exists(cfg_path):
            os.startfile(cfg_path)
        else:
            messagebox.showerror("Ошибка", f"Папка cfg не найдена по пути:\n{cfg_path}")

    def open_userdata_folder(self):
        if not self.steam_path:
            messagebox.showerror("Ошибка", "Путь к Steam не определен.")
            return
        userdata_path = os.path.join(self.steam_path, "userdata")
        if os.path.exists(userdata_path):
            os.startfile(userdata_path)
        else:
            messagebox.showerror("Ошибка", "Папка userdata не найдена.")

    def clear_game_cache(self):
        """Очистка кэша карт Мастерской и шейдеров CS2"""
        if not self.steam_path:
            messagebox.showerror("Ошибка", "Путь к Steam не определен.")
            return

        workshop_path = os.path.join(self.steam_path, "steamapps", "workshop", "content", "730")
        shader_cache_path = os.path.join(self.steam_path, "steamapps", "shadercache", "730")

        confirm = messagebox.askyesno(
            "Очистка кэша CS2",
            "Это действие очистит скачанные карты из Мастерской Steam и кэш шейдеров игры (App ID 730).\n\n"
            "Это поможет освободить место и избавиться от возможных фризов.\n\nПродолжить?"
        )

        if not confirm:
            return

        deleted_something = False
        try:
            if os.path.exists(workshop_path):
                for item in os.listdir(workshop_path):
                    item_path = os.path.join(workshop_path, item)
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path, ignore_errors=True)
                    else:
                        os.remove(item_path)
                deleted_something = True

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
        DemoManagerWindow(self, demos_path)


if __name__ == "__main__":
    app = CS2HelperApp()
    app.mainloop()