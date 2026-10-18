import os
import shutil
import winreg
import zipfile
import webbrowser
from datetime import datetime
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog

# Настройка темы интерфейса
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# --- Идеально стабильный класс тултипов на таймерах ---
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hide_tip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(300, self.show_tip)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def show_tip(self):
        if self.tip_window or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 10
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4

            self.tip_window = tw = ctk.CTkToplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.attributes("-topmost", True)
            tw.geometry(f"+{x}+{y}")

            label = ctk.CTkLabel(
                tw, 
                text=self.text, 
                font=("Segoe UI", 10), 
                fg_color="#1a1a1a", 
                text_color="#ffffff",
                corner_radius=4,
                padx=8,
                pady=4
            )
            label.pack()
        except Exception:
            pass

    def hide_tip(self):
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None

# --- Работа с реестром для имен аккаунтов ---
def get_saved_account_names():
    names = {}
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\CS2Helper\AccountNames", 0, winreg.KEY_READ)
        i = 0
        while True:
            try:
                acc_id, name, _ = winreg.EnumValue(key, i)
                names[acc_id] = name
                i += 1
            except WindowsError:
                break
        winreg.CloseKey(key)
    except Exception:
        pass
    return names

def save_account_name_to_registry(acc_id, name):
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\CS2Helper\AccountNames")
        winreg.SetValueEx(key, str(acc_id), 0, winreg.REG_SZ, str(name))
        winreg.CloseKey(key)
    except Exception:
        pass

def delete_account_name_from_registry(acc_id):
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\CS2Helper\AccountNames", 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, str(acc_id))
        winreg.CloseKey(key)
    except Exception:
        pass

# Словарь локализации
LANGUAGES = {
    "en": {
        "title": "CS2 Helper",
        "active_acc": "Active Account: ",
        "find_id": "Where to find ID in Steam?",
        "sec_acc": "Account Management",
        "btn_change_acc": "Change Account",
        "btn_save_cfg": "💾 Save Config",
        "btn_load_cfg": "📥 Load Config",
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
        "restore_confirm_title": "Load Config",
        "restore_confirm_msg": "Are you sure you want to restore settings from archive?\nExisting files in active account 'remote' folder will be overwritten.",
        "restore_success": "Config successfully restored!",
        "cache_title": "Clear CS2 Cache",
        "cache_msg": "This action will clear downloaded Steam Workshop maps and game shader cache (App ID 730).\n\nThis helps free up space and reduce stuttering.\n\nContinue?",
        "cache_success": "CS2 cache and temp files successfully cleared!\n\nFreed space: ",
        "cache_empty": "CS2 temporary files not found (folders are already empty).",
        "lang_btn": "🌐 RU",
        "faq_title": "Help & FAQ",
        "faq_btn": "❓",
        "faq_text": (
            "• Change Account: Switches active Steam account for config operations.\n\n"
            "• Save & Load Config: Archives or restores the 'remote' folder containing in-game settings (.zip).\n\n"
            "• Account Custom Names: Click the pencil icon to edit, floppy disk to save, or reset button to restore default Steam ID.\n\n"
            "• Open CFG Folder: Opens the official game configuration directory.\n\n"
            "• Open Userdata Folder: Opens the root Steam userdata directory.\n\n"
            "• Demo Manager: Lists all .dem files, shows their size, lets you delete or open folder.\n\n"
            "• Clear Game Cache: Clears Workshop maps and shader cache, calculates and shows freed space."
        ),
        "tip_edit": "Focus/Edit account name",
        "tip_save": "Save custom account name",
        "tip_reset": "Reset to default Steam ID",
        "tip_select": "Select active account"
    },
    "ru": {
        "title": "CS2 Helper",
        "active_acc": "Активный аккаунт: ",
        "find_id": "Где найти ID в Steam?",
        "sec_acc": "Управление аккаунтом",
        "btn_change_acc": "Сменить аккаунт",
        "btn_save_cfg": "💾 Сохранить",
        "btn_load_cfg": "📥 Загрузить",
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
        "restore_confirm_title": "Загрузка конфига",
        "restore_confirm_msg": "Вы уверены, что хотите восстановить настройки из архива?\nТекущие файлы в папке 'remote' активного аккаунта будут перезаписаны.",
        "restore_success": "Конфиг успешно восстановлен!",
        "cache_title": "Очистка кэша CS2",
        "cache_msg": "Это действие очистит скачанные карты из Мастерской Steam и кэш шейдеров игры (App ID 730).\n\nЭто поможет освободить место и избавиться от возможных фризов.\n\nПродолжить?",
        "cache_success": "Кэш и временные файлы CS2 успешно очищены!\n\nОсвобождено места: ",
        "cache_empty": "Временные файлы CS2 не найдены (папки уже пусты).",
        "lang_btn": "🌐 EN",
        "faq_title": "Справка и FAQ",
        "faq_btn": "❓",
        "faq_text": (
            "• Сменить аккаунт: Переключает активный аккаунт Steam для работы с конфигами.\n\n"
            "• Сохранить и Загрузить конфиг: Архивирует или восстанавливает папку 'remote' с настройками из .zip архива.\n\n"
            "• Имена аккаунтов: Нажмите на карандаш для редактирования, дискету для сохранения или сброс для возврата к Steam ID.\n\n"
            "• Открыть папку CFG: Открывает стандартную директорию конфигурации игры.\n\n"
            "• Открыть папку userdata: Открывает корневую папку userdata всех аккаунтов Steam.\n\n"
            "• Управление демками: Показывает список .dem файлов, размер, позволяет удалять или открывать папку.\n\n"
            "• Очистить кэш игры: Удаляет карты из Мастерской и кэш шейдеров, подсчитывая освобожденное место."
        ),
        "tip_edit": "Фокус/Редактировать имя",
        "tip_save": "Сохранить имя",
        "tip_reset": "Сбросить к Steam ID",
        "tip_select": "Выбрать активным"
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

class FAQWindow(ctk.CTkToplevel):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.title(LANGUAGES[lang]["faq_title"])
        
        window_width = 540
        window_height = 460
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)
        self.attributes("-toolwindow", True)
        self.grab_set()

        lbl_title = ctk.CTkLabel(self, text=LANGUAGES[lang]["faq_title"], font=("Segoe UI", 18, "bold"))
        lbl_title.pack(pady=15)

        txt_box = ctk.CTkTextbox(self, width=500, height=350, font=("Segoe UI", 12), fg_color="#222222", corner_radius=8, wrap="word")
        txt_box.pack(pady=5, padx=20)
        txt_box.insert("1.0", LANGUAGES[lang]["faq_text"])
        txt_box.configure(state="disabled")

class AccountSelector(ctk.CTkToplevel):
    def __init__(self, parent, accounts, steam_path, lang):
        super().__init__(parent)
        self.title("Change Account" if lang == "en" else "Сменить аккаунт")
        self.lang = lang
        
        window_width = 540
        window_height = 440
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)
        self.attributes("-toolwindow", True)
        self.grab_set()
        
        self.selected_account = None
        self.saved_names = get_saved_account_names()

        lbl_title = ctk.CTkLabel(self, text="Change Account" if lang == "en" else "Сменить аккаунт", font=("Segoe UI", 18, "bold"))
        lbl_title.pack(pady=15)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=490, height=300, fg_color="transparent")
        self.scroll_frame.pack(pady=5, padx=20)

        for acc_id in accounts:
            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b", corner_radius=8)
            row_frame.pack(fill="x", pady=6, padx=5)

            lbl_id = ctk.CTkLabel(row_frame, text=f"ID: {acc_id}", font=("Segoe UI", 10), text_color="gray", width=80, anchor="w")
            lbl_id.pack(side="left", padx=8, pady=8)

            current_name = self.saved_names.get(acc_id, acc_id)
            entry_name = ctk.CTkEntry(row_frame, font=("Segoe UI", 12), width=130, height=30)
            entry_name.insert(0, current_name)
            entry_name.pack(side="left", padx=4, pady=8)

            btn_edit = ctk.CTkButton(
                row_frame, text="✎", font=("Segoe UI", 14, "bold"), width=32, height=30,
                fg_color="#1f538d", hover_color="#14375e",
                command=lambda ent=entry_name: ent.focus()
            )
            btn_edit.pack(side="left", padx=2)
            ToolTip(btn_edit, LANGUAGES[lang]["tip_edit"])

            btn_save = ctk.CTkButton(
                row_frame, text="💾", font=("Segoe UI", 11), width=32, height=30,
                fg_color="#333333", hover_color="#444444",
                command=lambda aid=acc_id, ent=entry_name: self.save_name(aid, ent)
            )
            btn_save.pack(side="left", padx=2)
            ToolTip(btn_save, LANGUAGES[lang]["tip_save"])

            btn_reset = ctk.CTkButton(
                row_frame, text="↺", font=("Segoe UI", 12, "bold"), width=32, height=30,
                fg_color="#442222", hover_color="#662222",
                command=lambda aid=acc_id, ent=entry_name: self.reset_name(aid, ent)
            )
            btn_reset.pack(side="left", padx=2)
            ToolTip(btn_reset, LANGUAGES[lang]["tip_reset"])

            btn_select = ctk.CTkButton(
                row_frame, text="Select" if lang == "en" else "Выбрать", font=("Segoe UI", 11), width=75, height=30,
                command=lambda a=acc_id, ent=entry_name: self.choose_account(a, ent)
            )
            btn_select.pack(side="right", padx=8)
            ToolTip(btn_select, LANGUAGES[lang]["tip_select"])

    def save_name(self, acc_id, entry):
        new_name = entry.get().strip()
        if new_name:
            save_account_name_to_registry(acc_id, new_name)
            messagebox.showinfo("Success" if self.lang == "en" else "Успех", "Account name saved!" if self.lang == "en" else "Имя сохранено!")

    def reset_name(self, acc_id, entry):
        delete_account_name_from_registry(acc_id)
        entry.delete(0, "end")
        entry.insert(0, str(acc_id))

    def choose_account(self, acc_id, entry):
        new_name = entry.get().strip()
        if new_name:
            save_account_name_to_registry(acc_id, new_name)
            
        self.selected_account = acc_id
        self.destroy()

class DemoManagerWindow(ctk.CTkToplevel):
    def __init__(self, parent, demos_path, lang):
        super().__init__(parent)
        self.lang = lang
        self.title("CS2 Demo Manager" if lang == "en" else "Менеджер демо-записей CS2")
        
        window_width = 520
        window_height = 420
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.resizable(False, False)
        self.attributes("-toolwindow", True)
        self.grab_set()

        self.demos_path = demos_path

        if not os.path.exists(self.demos_path):
            err_title = "Error" if self.lang == "en" else "Ошибка"
            err_msg = f"Demos folder not found:\n{self.demos_path}" if self.lang == "en" else f"Папка с демками не найдена:\n{self.demos_path}"
            messagebox.showerror(err_title, err_msg)
            self.destroy()
            return

        lbl_title = ctk.CTkLabel(self, text="Found Demos (.dem)" if lang == "en" else "Найденные демо-записи (.dem)", font=("Segoe UI", 18, "bold"))
        lbl_title.pack(pady=12)

        self.scroll_frame = ctk.CTkScrollableFrame(self, width=470, height=270, fg_color="transparent")
        self.scroll_frame.pack(pady=5, padx=20)

        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(pady=12)

        self.btn_open_dir = ctk.CTkButton(self.btn_frame, text="📁 " + ("Open Folder" if lang == "en" else "Открыть папку"), font=("Segoe UI", 12), command=self.open_folder, width=150, height=34, fg_color="#333333", hover_color="#444444")
        self.btn_open_dir.pack(side="left", padx=6)

        self.btn_refresh = ctk.CTkButton(self.btn_frame, text="🔄 " + ("Refresh" if lang == "en" else "Обновить список"), font=("Segoe UI", 12), command=self.load_demos, width=150, height=34, fg_color="#333333", hover_color="#444444")
        self.btn_refresh.pack(side="left", padx=6)

        self.load_demos()

    def load_demos(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not os.path.exists(self.demos_path):
            txt = "Demos folder not found." if self.lang == "en" else "Папка с демками не найдена."
            lbl_empty = ctk.CTkLabel(self.scroll_frame, text=txt, font=("Segoe UI", 12), text_color="gray")
            lbl_empty.pack(pady=20)
            return

        dem_files = [f for f in os.listdir(self.demos_path) if f.endswith('.dem')]

        if not dem_files:
            txt = "No demos found." if self.lang == "en" else "Демо-записи не найдены."
            lbl_empty = ctk.CTkLabel(self.scroll_frame, text=txt, font=("Segoe UI", 12), text_color="gray")
            lbl_empty.pack(pady=20)
            return

        dem_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.demos_path, x)), reverse=True)

        for dem in dem_files:
            file_path = os.path.join(self.demos_path, dem)
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

            row_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#2b2b2b", corner_radius=8)
            row_frame.pack(fill="x", pady=5, padx=5)

            lbl_name = ctk.CTkLabel(row_frame, text=dem, font=("Segoe UI", 12), anchor="w", width=290)
            lbl_name.pack(side="left", padx=12, pady=10)

            lbl_size = ctk.CTkLabel(row_frame, text=f"{file_size_mb:.1f} MB", font=("Segoe UI", 11), text_color="gray", width=65)
            lbl_size.pack(side="left", padx=5)

            btn_delete = ctk.CTkButton(
                row_frame, text="❌", font=("Segoe UI", 11), width=34, height=28, 
                fg_color="#552222", hover_color="#772222",
                command=lambda p=file_path, name=dem: self.delete_demo(p, name)
            )
            btn_delete.pack(side="right", padx=10)

    def delete_demo(self, file_path, name):
        title = "Confirmation" if self.lang == "en" else "Подтверждение"
        msg = f"Delete demo?\n{name}" if self.lang == "en" else f"Удалить демку?\n{name}"
        if messagebox.askyesno(title, msg):
            try:
                os.remove(file_path)
                self.load_demos()
            except Exception as e:
                messagebox.showerror("Error" if self.lang == "en" else "Ошибка", f"Failed to delete file:\n{str(e)}")

    def open_folder(self):
        if os.path.exists(self.demos_path):
            os.startfile(self.demos_path)
        else:
            err_title = "Error" if self.lang == "en" else "Ошибка"
            err_msg = f"Demos folder not found:\n{self.demos_path}" if self.lang == "en" else f"Папка с демками не найдена:\n{self.demos_path}"
            messagebox.showerror(err_title, err_msg)

class CS2HelperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.lang = "en"

        window_width = 460
        window_height = 600
        
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
            messagebox.showerror("Error", LANGUAGES[self.lang]["err_registry"])
            self.destroy()
            return
        
        self.accounts = get_steam_accounts(self.steam_path)
        if self.accounts:
            self.current_account = self.accounts[0]

        # --- Верхняя панель ---
        self.top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.top_frame.pack(fill="x", padx=20, pady=(12, 0))

        self.btn_faq = ctk.CTkButton(
            self.top_frame, text=LANGUAGES[self.lang]["faq_btn"], font=("Segoe UI", 12, "bold"),
            width=38, height=28, fg_color="#333333", hover_color="#444444",
            command=self.open_faq_window
        )
        self.btn_faq.pack(side="left")

        self.btn_lang = ctk.CTkButton(
            self.top_frame, text=LANGUAGES[self.lang]["lang_btn"], font=("Segoe UI", 12, "bold"),
            width=65, height=28, fg_color="#333333", hover_color="#444444",
            command=self.toggle_language
        )
        self.btn_lang.pack(side="right")

        # --- Шапка приложения ---
        self.label_title = ctk.CTkLabel(self, text="CS2 Helper V.1", font=("Segoe UI", 20, "bold"))
        self.label_title.pack(pady=(6, 4))

        saved_names = get_saved_account_names()
        display_acc_name = saved_names.get(self.current_account, self.current_account)

        self.lbl_acc_info = ctk.CTkLabel(self, text=f"{LANGUAGES[self.lang]['active_acc']}{display_acc_name}", font=("Segoe UI", 12), text_color="cyan")
        self.lbl_acc_info.pack(pady=(0, 2))

        self.lbl_link = ctk.CTkLabel(
            self, text=LANGUAGES[self.lang]["find_id"], font=("Segoe UI", 11, "underline"), 
            text_color="#3399ff", cursor="hand2"
        )
        self.lbl_link.pack(pady=(0, 12))
        self.lbl_link.bind("<Button-1>", lambda e: webbrowser.open("https://steamcommunity.com/my/tradeoffers/privacy"))

        # ==========================================
        # КАТЕГОРИЯ 1: Аккаунт и Конфиг
        # ==========================================
        self.frame_acc = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=10, border_width=1, border_color="#2a2a2a")
        self.frame_acc.pack(pady=6, padx=20, fill="x")
        self.frame_acc.grid_columnconfigure(0, weight=1)
        self.frame_acc.grid_columnconfigure(1, weight=1)

        self.lbl_sec1 = ctk.CTkLabel(self.frame_acc, text=LANGUAGES[self.lang]["sec_acc"], font=("Segoe UI", 12, "bold"), text_color="gray")
        self.lbl_sec1.grid(row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 4))

        self.btn_change_acc = ctk.CTkButton(
            self.frame_acc, text=LANGUAGES[self.lang]["btn_change_acc"], font=("Segoe UI", 12), 
            command=self.open_account_window, height=34, 
            fg_color="#2a475e", hover_color="#1b2838"
        )
        self.btn_change_acc.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=4)

        self.btn_save = ctk.CTkButton(
            self.frame_acc, text=LANGUAGES[self.lang]["btn_save_cfg"], font=("Segoe UI", 12, "bold"), 
            command=self.save_config, height=36, 
            fg_color="#3f51b5", hover_color="#303f9f"
        )
        self.btn_save.grid(row=2, column=0, sticky="ew", padx=(14, 4), pady=(4, 12))

        self.btn_load = ctk.CTkButton(
            self.frame_acc, text=LANGUAGES[self.lang]["btn_load_cfg"], font=("Segoe UI", 12, "bold"), 
            command=self.restore_config, height=36, 
            fg_color="#00897b", hover_color="#00695c"
        )
        self.btn_load.grid(row=2, column=1, sticky="ew", padx=(4, 14), pady=(4, 12))

        # ==========================================
        # КАТЕГОРИЯ 2: Папки и Демки
        # ==========================================
        self.frame_files = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=10, border_width=1, border_color="#2a2a2a")
        self.frame_files.pack(pady=6, padx=20, fill="x")

        self.lbl_sec2 = ctk.CTkLabel(self.frame_files, text=LANGUAGES[self.lang]["sec_files"], font=("Segoe UI", 12, "bold"), text_color="gray")
        self.lbl_sec2.pack(anchor="w", padx=14, pady=(10, 4))

        self.btn_open_cfg = ctk.CTkButton(self.frame_files, text=LANGUAGES[self.lang]["btn_cfg"], font=("Segoe UI", 12), command=self.open_cfg_folder, width=380, height=34, fg_color="#333333", hover_color="#444444")
        self.btn_open_cfg.pack(padx=14, pady=4)

        self.btn_open_userdata = ctk.CTkButton(self.frame_files, text=LANGUAGES[self.lang]["btn_userdata"], font=("Segoe UI", 12), command=self.open_userdata_folder, width=380, height=34, fg_color="#333333", hover_color="#444444")
        self.btn_open_userdata.pack(padx=14, pady=4)

        self.btn_demos = ctk.CTkButton(
            self.frame_files, text=LANGUAGES[self.lang]["btn_demos"], font=("Segoe UI", 12, "bold"), 
            command=self.open_demos_folder, width=380, height=34, 
            fg_color="#d97706", hover_color="#b45309"
        )
        self.btn_demos.pack(padx=14, pady=(4, 12))

        # ==========================================
        # КАТЕГОРИЯ 3: Обслуживание
        # ==========================================
        self.frame_service = ctk.CTkFrame(self, fg_color="#1a1a1a", corner_radius=10, border_width=1, border_color="#2a2a2a")
        self.frame_service.pack(pady=6, padx=20, fill="x")

        self.lbl_sec3 = ctk.CTkLabel(self.frame_service, text=LANGUAGES[self.lang]["sec_service"], font=("Segoe UI", 12, "bold"), text_color="gray")
        self.lbl_sec3.pack(anchor="w", padx=14, pady=(10, 4))

        self.btn_clear_cache = ctk.CTkButton(self.frame_service, text=LANGUAGES[self.lang]["btn_cache"], font=("Segoe UI", 12), command=self.clear_game_cache, width=380, height=34, fg_color="#4d2222", hover_color="#662e2e")
        self.btn_clear_cache.pack(padx=14, pady=(4, 12))

        self.update_ui_texts()

    def toggle_language(self):
        self.lang = "ru" if self.lang == "en" else "en"
        self.update_ui_texts()

    def open_faq_window(self):
        FAQWindow(self, self.lang)

    def update_ui_texts(self):
        t = LANGUAGES[self.lang]
        self.title(t["title"])
        self.btn_lang.configure(text=t["lang_btn"])
        self.btn_faq.configure(text=t["faq_btn"])
        
        saved_names = get_saved_account_names()
        display_acc_name = saved_names.get(self.current_account, self.current_account)
        self.lbl_acc_info.configure(text=f"{t['active_acc']}{display_acc_name}")
        
        self.lbl_link.configure(text=t["find_id"])
        
        self.lbl_sec1.configure(text=t["sec_acc"])
        self.btn_change_acc.configure(text=t["btn_change_acc"])
        self.btn_save.configure(text=t["btn_save_cfg"])
        self.btn_load.configure(text=t["btn_load_cfg"])
        
        self.lbl_sec2.configure(text=t["sec_files"])
        self.btn_open_cfg.configure(text=t["btn_cfg"])
        self.btn_open_userdata.configure(text=t["btn_userdata"])
        self.btn_demos.configure(text=t["btn_demos"])
        
        self.lbl_sec3.configure(text=t["sec_service"])
        self.btn_clear_cache.configure(text=t["btn_cache"])

    def open_account_window(self):
        if not self.accounts:
            messagebox.showwarning("Warning" if self.lang == "en" else "Внимание", LANGUAGES[self.lang]["err_no_acc"])
            return
        
        selector = AccountSelector(self, self.accounts, self.steam_path, self.lang)
        self.wait_window(selector)
        
        if selector.selected_account:
            self.current_account = selector.selected_account
            saved_names = get_saved_account_names()
            display_acc_name = saved_names.get(self.current_account, self.current_account)
            self.lbl_acc_info.configure(text=f"{LANGUAGES[self.lang]['active_acc']}{display_acc_name}")

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
                messagebox.showerror("Error" if self.lang == "en" else "Ошибка", f"Remote folder not found:\n{remote_path}")
                return

            default_dir = os.path.expanduser(r"~\Documents\CS2_Backups")
            if not os.path.exists(default_dir):
                os.makedirs(default_dir, exist_ok=True)
                
            saved_names = get_saved_account_names()
            acc_label = saved_names.get(self.current_account, self.current_account)
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            default_filename = f"remote_backup_{acc_label}_{timestamp}.zip"
            
            file_path = filedialog.asksaveasfilename(
                initialdir=default_dir,
                initialfile=default_filename,
                defaultextension=".zip",
                filetypes=[("ZIP archives", "*.zip"), ("All files", "*.*")],
                title="Save CS2 Settings Backup"
            )
            
            if not file_path:
                return
            
            base_archive_path = file_path[:-4] if file_path.lower().endswith('.zip') else file_path
            shutil.make_archive(base_archive_path, 'zip', remote_path)
            
            msg = LANGUAGES[self.lang]["success_backup"] + file_path
            messagebox.showinfo("Success" if self.lang == "en" else "Успех", msg)
            
        except Exception as e:
            messagebox.showerror("Error" if self.lang == "en" else "Ошибка", f"Failed to create archive: {str(e)}")

    def restore_config(self):
        try:
            target_cfg_path = self.get_current_cfg_path()
            remote_path = os.path.dirname(target_cfg_path) if target_cfg_path.endswith("cfg") else target_cfg_path

            default_dir = os.path.expanduser(r"~\Documents\CS2_Backups")
            if not os.path.exists(default_dir):
                default_dir = os.path.expanduser(r"~\Documents")

            file_path = filedialog.askopenfilename(
                initialdir=default_dir,
                filetypes=[("ZIP archives", "*.zip"), ("All files", "*.*")],
                title="Select CS2 Backup Archive"
            )

            if not file_path:
                return

            t = LANGUAGES[self.lang]
            confirm = messagebox.askyesno(t["restore_confirm_title"], t["restore_confirm_msg"])
            if not confirm:
                return

            os.makedirs(remote_path, exist_ok=True)

            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(remote_path)

            messagebox.showinfo("Success" if self.lang == "en" else "Успех", t["restore_success"])

        except Exception as e:
            messagebox.showerror("Error" if self.lang == "en" else "Ошибка", f"Failed to restore config:\n{str(e)}")

    def open_userdata_folder(self):
        if self.steam_path:
            userdata_path = os.path.join(self.steam_path, "userdata")
            if os.path.exists(userdata_path):
                os.startfile(userdata_path)
            else:
                messagebox.showerror("Error" if self.lang == "en" else "Ошибка", f"Userdata folder not found:\n{userdata_path}")
        else:
            messagebox.showerror("Error" if self.lang == "en" else "Ошибка", LANGUAGES[self.lang]["err_steam_path"])

    def open_cfg_folder(self):
        target_cfg_path = self.get_current_cfg_path()
        if os.path.exists(target_cfg_path):
            os.startfile(target_cfg_path)
        else:
            fallback_path = os.path.join(self.steam_path, "steamapps", "common", "Counter-Strike Global Offensive", "game", "csgo", "cfg")
            if os.path.exists(fallback_path):
                os.startfile(fallback_path)
            else:
                messagebox.showerror("Error" if self.lang == "en" else "Ошибка", "Config folder not found.")

    def clear_game_cache(self):
        if not self.steam_path:
            messagebox.showerror("Error" if self.lang == "en" else "Ошибка", LANGUAGES[self.lang]["err_steam_path"])
            return

        workshop_path = os.path.join(self.steam_path, "steamapps", "workshop", "content", "730")
        shader_cache_path = os.path.join(self.steam_path, "steamapps", "shadercache", "730")

        t = LANGUAGES[self.lang]
        confirm = messagebox.askyesno(t["cache_title"], t["cache_msg"])

        if not confirm:
            return

        total_size_bytes = 0

        def get_size(path):
            total = 0
            if os.path.isfile(path):
                total += os.path.getsize(path)
            elif os.path.isdir(path):
                for dirpath, _, filenames in os.walk(path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        if os.path.exists(fp):
                            total += os.path.getsize(fp)
            return total

        if os.path.exists(workshop_path):
            total_size_bytes += get_size(workshop_path)
        if os.path.exists(shader_cache_path):
            total_size_bytes += get_size(shader_cache_path)

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
                if total_size_bytes >= 1024 * 1024 * 1024:
                    size_str = f"{total_size_bytes / (1024 * 1024 * 1024):.2f} GB"
                else:
                    size_str = f"{total_size_bytes / (1024 * 1024):.1f} MB"
                
                messagebox.showinfo("Success" if self.lang == "en" else "Успех", t["cache_success"] + size_str)
            else:
                messagebox.showinfo("Info" if self.lang == "en" else "Информация", t["cache_empty"])

        except Exception as e:
            messagebox.showerror("Error" if self.lang == "en" else "Ошибка", f"Failed to clear cache:\n{str(e)}")

    def open_demos_folder(self):
        if not self.steam_path:
            messagebox.showerror("Error" if self.lang == "en" else "Ошибка", LANGUAGES[self.lang]["err_steam_path"])
            return

        demos_path = os.path.join(self.steam_path, "steamapps", "common", "Counter-Strike Global Offensive", "game", "csgo")
        DemoManagerWindow(self, demos_path, self.lang)
        
if __name__ == "__main__":
    app = CS2HelperApp()
    app.mainloop()