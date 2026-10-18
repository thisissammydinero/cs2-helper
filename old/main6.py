import os
import shutil
import winreg
import webbrowser
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog

# Настройка темы интерфейса
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Словарь локализации (Русский / Английский)
LANGUAGES = {
    "ru": {
        "title": "CS2 Helper",
        "active_acc": "Активный аккаунт (ID): ",
        "find_id": "Где найти ID в Steam?",
        "sec_acc": "Управление аккаунтом",
        "btn_change_acc": "Сменить аккаунт",
        "btn_save_cfg": "Сохранить конфиг",
        "sec_files": "Файлы и папки игры",
        "btn_cfg": "Открыть папку CFG",
        "btn_userdata": "Открыть папку userdata",
        "btn_demos": "🎬 Управление демками (.dem)",
        "sec_service": "Обслуживание",
        "btn_cache": "🧹 Очистить кэш игры",
        "err_registry": "Не удалось найти установленный Steam в реестре!",
        "err_steam_path": "Путь к Steam не определен.",
        "err_no_acc": "Аккаунты не найдены в папке userdata.",
        "success_backup": "Архив успешно создан!\n\nФайл сохранен:\n",
        "cache_title": "Очистка кэша CS2",
        "cache_msg": "Это действие очистит скачанные карты из Мастерской Steam и кэш шейдеров игры (App ID 730).\n\nЭто поможет освободить место и избавиться от возможных фризов.\n\nПродолжить?",
        "cache_success": "Кэш и временные файлы CS2 успешно очищены!",
        "cache_empty": "Временные файлы CS2 не найдены (папки уже пусты).",
        "lang_btn": "🌐 EN"
    },
    "en": {
        "title": "CS2 Helper",
        "active_acc": "Active Account (ID): ",
        "find_id": "Where to find ID in Steam?",
        "sec_acc": "Account Management",
        "btn_change_acc": "Change Account",
        "btn_save_cfg": "Save Config Backup",
        "sec_files": "Game Files & Folders",
        "btn_cfg": "Open CFG Folder",
        "btn_userdata": "Open Userdata Folder",
        "btn_demos": "🎬 Demo Manager (.dem)",
        "sec_service": "Maintenance",
        "btn_cache": "🧹 Clear Game Cache",
        "err_registry": "Failed to find installed Steam in registry!",
        "err_steam_path": "Steam path is not defined.",
        "err_no_acc": "No accounts found in userdata folder.",
        "success_backup": "Archive successfully created!\n\nFile saved to:\n",
        "cache_title": "Clear CS2 Cache",
        "cache_msg": "This action will clear downloaded Steam Workshop maps and game shader cache (App ID 730).\n\nThis helps free up space and reduce stuttering.\n\nContinue?",
        "cache_success": "CS2 cache and temp files successfully cleared!",
        "cache_empty": "CS2 temporary files not found (folders are already empty).",
        "lang_btn": "🌐 RU"
    }
}

def get_steam_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)
        return os.path.normpath(steam_path)
    except Exception:
        return None

def get_steam_accounts(steam_path):
    userdata_path = os.path.join(steam_path, "userdata")
    accounts = []
    
    if os.path.exists(userdata_path):
        for folder_name in os.listdir(userdata_path):
            folder_path = os.path.join(userdata_path, folder_name)
            if os.path.isdir(folder_path) and folder_name.isdigit() and folder_name != "0":
                accounts.append(folder_name)
    return accounts

class AccountSelector(ctk.CTkToplevel):
    def __init__(self, parent, accounts, steam_path, lang):
        super().__init__(parent)
        self.title("Сменить аккаунт" if lang == "ru" else "Change Account")
        
        window_width = 440
        window_height = 360
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)
        self.attributes("-toolwindow", True)
        self.grab_set()
        
        self.selected_account = None

        lbl_title = ctk.CTkLabel(self, text="Сменить аккаунт" if lang == "ru" else "Change Account", font=("Arial", 16, "bold"))
        lbl_title.pack(pady=15)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=400, height=240, fg_color="transparent")
        self.scroll_frame.pack(pady=5, padx=20)

        for acc_id in accounts:
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b", corner_radius=6)
            row_frame.pack(fill="x", pady=4, padx=5)

            lbl_avatar = ctk.CTkLabel(row_frame, text="👤", font=("Arial", 16), width=32)
            lbl_avatar.pack(side="left", padx=10, pady=6)

            lbl_id = ctk.CTkLabel(row_frame, text=f"ID: {acc_id}", font=("Arial", 12, "bold"))
            lbl_id.pack(side="left", padx=5, pady=10)

            btn_select = ctk.CTkButton(
                row_frame, 
                text="Выбрать" if lang == "ru" else "Select", 
                width=90, 
                height=28,
                command=lambda a=acc_id: self.choose_account(a)
            )
            btn_select.pack(side="right", padx=10)

    def choose_account(self, acc_id):
        self.selected_account = acc_id
        self.destroy()

class DemoManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent, demos_path, lang):
        super().__init__(parent)
        self.lang = lang
        self.title("Менеджер демо-записей CS2" if lang == "ru" else "CS2 Demo Manager")
        
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

        lbl_title = ctk.CTkLabel(self, text="Найденные демо-записи (.dem)" if lang == "ru" else "Found Demos (.dem)", font=("Arial", 16, "bold"))
        lbl_title.pack(pady=10)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=460, height=260, fg_color="transparent")
        self.scroll_frame.pack(pady=5, padx=20)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=10)

        self.btn_open_dir = ctk.CTkButton(self.btn_frame, text="📁 " + ("Открыть папку" if lang == "ru" else "Open Folder"), command=self.open_folder, width=140, fg_color="#333333", hover_color="#444444")
        self.btn_open_dir.pack(side="left", padx=5)

        self.btn_refresh = ctk.CTkButton(self.btn_frame, text="🔄 " + ("Обновить список" if lang == "ru" else "Refresh"), command=self.load_demos, width=140, fg_color="#333333", hover_color="#444444")
        self.btn_refresh.pack(side="left", padx=5)

        self.load_demos()

    def load_demos(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not os.path.exists(self.demos_path):
            txt = "Папка с демками не найдена." if self.lang == "ru" else "Demos folder not found."
            lbl_empty = ctk.CTkLabel(self.scroll_frame, text=txt, text_color="gray")
            lbl_empty.pack(pady=20)
            return

        dem_files = [f for f in os.listdir(self.demos_path) if f.endswith('.dem')]

        if not dem_files:
            txt = "Демо-записи не найдены." if self.lang == "ru" else "No demos found."
            lbl_empty = ctk.CTkLabel(self.scroll_frame, text=txt, text_color="gray")
            lbl_empty.pack(pady=20)
            return

        dem_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.demos_path, x)), reverse=True)

        for dem in dem_files:
            file_path = os.path.join(self.demos_path, dem)
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b", corner_radius=6)
            row_frame.pack(fill="x", pady=4, padx=5)

            lbl_name = ctk.CTkLabel(row_frame, text=dem, font=("Arial", 11), anchor="w", width=280)
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
        title = "Подтверждение" if self.lang == "ru" else "Confirmation"
        msg = f"Удалить демку?\n{name}" if self.lang == "ru" else f"Delete demo?\n{name}"
        if messagebox.askyesno(title, msg):
            try:
                os.remove(file_path)
                self.load_demos()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить файл:\n{str(e)}")

    def open_folder(self):
        if os.path.exists(self.demos_path):
            os.startfile(self.demos_path)

class CS2HelperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.lang = "ru"  # Язык по умолчанию

        window_width = 440
        window_height = 560
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)

        try:
            self.iconbitmap("icon.ico")
        except Exception:
            pass

        self.steam_path = get_steam_path()
        self.current_account = None

        if not self.steam_path:
            messagebox.showerror("Ошибка", LANGUAGES[self.lang]["err_registry"])
            self.destroy()
            return
        
        self.accounts = get_steam_accounts(self.steam_path)
        if self.accounts:
            self.current_account = self.accounts[0]

        # --- Верхняя панель (переключение языка) ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=20, pady=(10, 0))

        self.btn_lang = ctk.CTkButton(
            self.top_frame, 
            text=LANGUAGES[self.lang]["lang_btn"], 
            width=60, 
            height=24, 
            fg_color="#333333", 
            hover_color="#444444",
            command=self.toggle_language
        )
        self.btn_lang.pack(side="right")

        # --- Шапка приложения ---
        self.label_title = ctk.CTkLabel(self, text="CS2 Helper V.1", font=("Arial", 18, "bold"))
        self.label_title.pack(pady=(5, 5))

        self.lbl_acc_info = ctk.CTkLabel(self, text=f"{LANGUAGES[self.lang]['active_acc']}{self.current_account}", font=("Arial", 11), text_color="cyan")
        self.lbl_acc_info.pack(pady=(0, 2))

        self.lbl_link = ctk.CTkLabel(
            self, 
            text=LANGUAGES[self.lang]["find_id"], 
            font=("Arial", 10, "underline"), 
            text_color="#3399ff", 
            cursor="hand2"
        )
        self.lbl_link.pack(pady=(0, 10))
        self.lbl_link.bind("<Button-1>", lambda e: webbrowser.open("https://steamcommunity.com/my/tradeoffers/privacy"))

        # ==========================================
        # КАТЕГОРИЯ 1: Аккаунт и Конфиг
        # ==========================================
        self.frame_acc = ctk.CTkFrame(self, fg_color="#222222", corner_radius=8)
        self.frame_acc.pack(pady=5, padx=20, fill="x")

        self.lbl_sec1 = ctk.CTkLabel(self.frame_acc, text=LANGUAGES[self.lang]["sec_acc"], font=("Arial", 11, "bold"), text_color="gray")
        self.lbl_sec1.pack(anchor="w", padx=12, pady=(8, 2))

        self.btn_change_acc = ctk.CTkButton(self.frame_acc, text=LANGUAGES[self.lang]["btn_change_acc"], command=self.open_account_window, width=360, height=32, fg_color="#333333", hover_color="#444444")
        self.btn_change_acc.pack(padx=12, pady=4)

        self.btn_save = ctk.CTkButton(self.frame_acc, text=LANGUAGES[self.lang]["btn_save_cfg"], command=self.save_config, width=360, height=34, fg_color="#1f538d", hover_color="#14375e")
        self.btn_save.pack(padx=12, pady=(4, 10))

        # ==========================================
        # КАТЕГОРИЯ 2: Папки и Демки
        # ==========================================
        self.frame_files = ctk.CTkFrame(self, fg_color="#222222", corner_radius=8)
        self.frame_files.pack(pady=5, padx=20, fill="x")

        self.lbl_sec2 = ctk.CTkLabel(self.frame_files, text=LANGUAGES[self.lang]["sec_files"], font=("Arial", 11, "bold"), text_color="gray")
        self.lbl_sec2.pack(anchor="w", padx=12, pady=(8, 2))

        self.btn_open_cfg = ctk.CTkButton(self.frame_files, text=LANGUAGES[self.lang]["btn_cfg"], command=self.open_cfg_folder, width=360, height=32, fg_color="#333333", hover_color="#444444")
        self.btn_open_cfg.pack(padx=12, pady=4)

        self.btn_open_userdata = ctk.CTkButton(self.frame_files, text=LANGUAGES[self.lang]["btn_userdata"], command=self.open_userdata_folder, width=360, height=32, fg_color="#333333", hover_color="#444444")
        self.btn_open_userdata.pack(padx=12, pady=4)

        self.btn_demos = ctk.CTkButton(self.frame_files, text=LANGUAGES[self.lang]["btn_demos"], command=self.open_demos_folder, width=360, height=32, fg_color="#333333", hover_color="#444444")
        self.btn_demos.pack(padx=12, pady=(4, 10))

        # ==========================================
        # КАТЕГОРИЯ 3: Обслуживание
        # ==========================================
        self.frame_service = ctk.CTkFrame(self, fg_color="#222222", corner_radius=8)
        self.frame_service.pack(pady=5, padx=20, fill="x")

        self.lbl_sec3 = ctk.CTkLabel(self.frame_service, text=LANGUAGES[self.lang]["sec_service"], font=("Arial", 11, "bold"), text_color="gray")
        self.lbl_sec3.pack(anchor="w", padx=12, pady=(8, 2))

        self.btn_clear_cache = ctk.CTkButton(self.frame_service, text=LANGUAGES[self.lang]["btn_cache"], command=self.clear_game_cache, width=360, height=32, fg_color="#4d2222", hover_color="#662e2e")
        self.btn_clear_cache.pack(padx=12, pady=(4, 10))

        self.update_ui_texts()

    def toggle_language(self):
        """Переключение языка интерфейса"""
        self.lang = "en" if self.lang == "ru" else "ru"
        self.update_ui_texts()

    def update_ui_texts(self):
        """Обновление всех текстов в интерфейсе при смене языка"""
        t = LANGUAGES[self.lang]
        self.title(t["title"])
        self.btn_lang.configure(text=t["lang_btn"])
        self.lbl_acc_info.configure(text=f"{t['active_acc']}{self.current_account}")
        self.lbl_link.configure(text=t["find_id"])
        
        self.lbl_sec1.configure(text=t["sec_acc"])
        self.btn_change_acc.configure(text=t["btn_change_acc"])
        self.btn_save.configure(text=t["btn_save_cfg"])
        
        self.lbl_sec2.configure(text=t["sec_files"])
        self.btn_open_cfg.configure(text=t["btn_cfg"])
        self.btn_open_userdata.configure(text=t["btn_userdata"])
        self.btn_demos.configure(text=t["btn_demos"])
        
        self.lbl_sec3.configure(text=t["sec_service"])
        self.btn_clear_cache.configure(text=t["btn_cache"])

    def open_account_window(self):
        if not self.accounts:
            messagebox.showwarning("Внимание" if self.lang == "ru" else "Warning", LANGUAGES[self.lang]["err_no_acc"])
            return
        
        selector = AccountSelector(self, self.accounts, self.steam_path, self.lang)
        self.wait_window(selector)
        
        if selector.selected_account:
            self.current_account = selector.selected_account
            self.lbl_acc_info.configure(text=f"{LANGUAGES[self.lang]['active_acc']}{self.current_account}")

    def get_current_cfg_path(self):
        if self.current_account:
            userdata_cfg = os.path.join(self.steam_path, "userdata", self.current_account, "730", "remote")
            if os.path.exists(userdata_cfg):
                return userdata_cfg
                
        return os.path.join(self.steam_path, "steamapps", "common", "Counter-Strike Global Offensive", "game", "csgo")

    def save_config(self):
        try:
            target_cfg_path = self.get_current_cfg_path()
            remote_path = os.path.dirname(target_cfg_path) if target_cfg_path.endswith("cfg") else target_cfg_path
            
            if not os.path.exists(remote_path):
                messagebox.showerror("Ошибка", f"Папка remote не найдена по пути:\n{remote_path}")
                return

            default_dir = os.path.expanduser(r"~\Documents\CS2_Backups")
            if not os.path.exists(default_dir):
                os.makedirs(default_dir, exist_ok=True)
                
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            default_filename = f"remote_backup_ID_{self.current_account}_{timestamp}.zip"
            
            file_path = filedialog.asksaveasfilename(
                initialdir=default_dir,
                initialfile=default_filename,
                defaultextension=".zip",
                filetypes=[("ZIP архивы", "*.zip"), ("Все файлы", "*.*")],
                title="Сохранить бэкап настроек CS2"
            )
            
            if not file_path:
                return
            
            base_archive_path = file_path[:-4] if file_path.lower().endswith('.zip') else file_path
            shutil.make_archive(base_archive_path, 'zip', remote_path)
            
            msg = LANGUAGES[self.lang]["success_backup"] + file_path
            messagebox.showinfo("Успех" if self.lang == "ru" else "Success", msg)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать архив: {str(e)}")

    def open_userdata_folder(self):
        if self.steam_path:
            userdata_path = os.path.join(self.steam_path, "userdata")
            if os.path.exists(userdata_path):
                os.startfile(userdata_path)
            else:
                messagebox.showerror("Ошибка", f"Папка userdata не найдена по пути:\n{userdata_path}")
        else:
            messagebox.showerror("Ошибка", LANGUAGES[self.lang]["err_steam_path"])

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
        if not self.steam_path:
            messagebox.showerror("Ошибка", LANGUAGES[self.lang]["err_steam_path"])
            return

        workshop_path = os.path.join(self.steam_path, "steamapps", "workshop", "content", "730")
        shader_cache_path = os.path.join(self.steam_path, "steamapps", "shadercache", "730")

        t = LANGUAGES[self.lang]
        confirm = messagebox.askyesno(t["cache_title"], t["cache_msg"])

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
                messagebox.showinfo("Успех" if self.lang == "ru" else "Success", t["cache_success"])
            else:
                messagebox.showinfo("Информация" if self.lang == "ru" else "Info", t["cache_empty"])

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось полностью очистить кэш:\n{str(e)}")

    def open_demos_folder(self):
        if not self.steam_path:
            messagebox.showerror("Ошибка", LANGUAGES[self.lang]["err_steam_path"])
            return

        demos_path = os.path.join(self.steam_path, "steamapps", "common", "Counter-Strike Global Offensive", "game", "csgo")
        DemoManagerWindow(self, demos_path, self.lang)
        
if __name__ == "__main__":
    app = CS2HelperApp()
    app.mainloop()