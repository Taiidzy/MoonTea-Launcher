import os
import winshell
from urllib.request import urlretrieve
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

def download_files(urls, destination_folder, progress_callback):
    total_files = len(urls)
    for index, url in enumerate(urls):
        filename = os.path.basename(url)
        if filename == "exe":
            filename = "MoonTea.exe"
        elif filename == "ico":
            filename = "icon.ico"
        elif filename == "bg":
            filename = "background.jpg"
        destination_path = os.path.join(destination_folder, filename)
        urlretrieve(url, destination_path)
        progress_callback(index + 1, total_files)

def create_shortcut(target_file, shortcut_name, shortcut_folder, working_directory):
    shortcut_path = os.path.join(shortcut_folder, f"{shortcut_name}.lnk")
    with winshell.shortcut(shortcut_path) as link:
        link.path = target_file
        link.working_directory = working_directory
        link.description = f"Shortcut to {target_file}"
        link.write()

def start_installation(destination_folder, create_desktop, create_start_menu, progress_callback):
    file_urls = [
        "http://178.173.82.2:1000/launcher/download/exe",
        "http://178.173.82.2:1000/launcher/download/ico",
        "http://178.173.82.2:1000/launcher/download/bg"
    ]

    moontea_folder = os.path.join(destination_folder, "MoonTea")
    os.makedirs(moontea_folder, exist_ok=True)
    download_files(file_urls, moontea_folder, progress_callback)

    moon_tea_exe_path = os.path.join(moontea_folder, "MoonTea.exe")

    if create_desktop:
        create_shortcut(moon_tea_exe_path, "MoonTea", winshell.desktop(), moontea_folder)
    if create_start_menu:
        start_menu_folder = os.path.join(os.getenv("APPDATA"), "Microsoft\\Windows\\Start Menu\\Programs")
        create_shortcut(moon_tea_exe_path, "MoonTea", start_menu_folder, moontea_folder)

def main():
    def on_install():
        destination_folder = folder_var.get()
        create_desktop = desktop_var.get()
        create_start_menu = start_menu_var.get()
        start_installation(destination_folder, create_desktop, create_start_menu, update_progress)
        messagebox.showinfo("Установка завершена", "Установка завершена")
        root.quit()

    def browse_folder():
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            folder_var.set(folder_selected)

    def update_progress(current, total):
        progress_var.set(current / total * 100)

    root = tk.Tk()
    root.title("Установщик MoonTea")

    folder_var = tk.StringVar(value=os.path.expanduser("~"))
    desktop_var = tk.BooleanVar(value=True)
    start_menu_var = tk.BooleanVar(value=True)
    progress_var = tk.DoubleVar(value=0)

    ttk.Label(root, text="Путь для установки:").pack(padx=10, pady=5)
    path_frame = ttk.Frame(root)
    path_frame.pack(fill='x', padx=10)
    ttk.Entry(path_frame, textvariable=folder_var, width=50).pack(side='left', fill='x', expand=True)
    ttk.Button(path_frame, text="Обзор", command=browse_folder).pack(side='right')

    ttk.Checkbutton(root, text="Создать ярлык на рабочем столе", variable=desktop_var).pack(anchor='w', padx=10, pady=5)
    ttk.Checkbutton(root, text="Создать ярлык в меню Пуск", variable=start_menu_var).pack(anchor='w', padx=10, pady=5)

    ttk.Progressbar(root, variable=progress_var, maximum=100).pack(fill='x', padx=10, pady=10)

    ttk.Button(root, text="Установить", command=on_install).pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
