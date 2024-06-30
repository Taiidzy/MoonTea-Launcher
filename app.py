import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
import os
import shutil
import subprocess
import requests
import json
import uuid
import logging
import platform
import minecraft_launcher_lib as mll
from PIL import Image, ImageTk

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MinecraftLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MoonTea Launcher")
        self.geometry("600x400")
        self.configure(bg='black')  # Set background color to black

        # Установить иконку
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        self.iconbitmap("icon.ico")

        # Load settings
        self.settings = self.load_settings()

        # Apply theme
        self.theme = self.settings.get("theme", "light")
        self.apply_theme()

        # Load background image
        self.background_image = Image.open("background.jpg")
        self.background_photo = ImageTk.PhotoImage(self.background_image.resize((600, 400), Image.LANCZOS))
        self.background_label = tk.Label(self, image=self.background_photo)
        self.background_label.place(relwidth=1, relheight=1)

        self.skin_path = ""
        self.builds = self.load_builds()
        self.nickname = self.settings.get("nickname", "")
        self.selected_build = self.settings.get("selected_build", "")

        self.create_widgets()

    def apply_theme(self):
        if self.theme == "dark":
            self.style = ttk.Style()
            self.style.theme_use("clam")
            self.configure(bg="black")
            self.style.configure("TLabel", background="black", foreground="white")
            self.style.configure("TButton", background="black", foreground="white")
            self.style.configure("TFrame", background="black")
        else:
            self.style = ttk.Style()
            self.style.theme_use("clam")
            self.configure(bg="white")
            self.style.configure("TLabel", background="white", foreground="black")
            self.style.configure("TButton", background="white", foreground="black")
            self.style.configure("TFrame", background="white")

    def create_widgets(self):
        frame = ttk.Frame(self, padding="10")
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        ttk.Label(frame, text="Введите никнейм:").pack(pady=5)
        self.nickname_entry = ttk.Entry(frame)
        self.nickname_entry.insert(0, self.nickname)
        self.nickname_entry.pack(pady=5)

        ttk.Label(frame, text="Выберите сборку:").pack(pady=5)
        self.build_var = tk.StringVar(self)
        self.build_menu = ttk.Combobox(frame, textvariable=self.build_var, values=self.builds)
        self.build_var.set(self.selected_build)
        self.build_menu.pack(pady=5)

        ttk.Button(frame, text="Выбрать скин", command=self.choose_skin).pack(pady=5)
        ttk.Button(frame, text="Настройки", command=self.open_settings).pack(pady=5)
        ttk.Button(frame, text="Запустить", command=self.launch_game).pack(pady=20)

    def choose_skin(self):
        logging.debug("Choosing skin")
        file_path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if file_path:
            self.skin_path = file_path
            self.apply_skin(self.nickname_entry.get(), self.skin_path)

    def apply_skin(self, nickname, skin_path):
        logging.debug(f"Applying skin for nickname: {nickname}, skin path: {skin_path}")
        mc_directory = os.path.join("userfiles")
        skin_directory = os.path.join(mc_directory, "skins")
        if not os.path.exists(skin_directory):
            os.makedirs(skin_directory)
            logging.debug(f"Created skin directory: {skin_directory}")
        shutil.copy(skin_path, os.path.join(skin_directory, f"{nickname}.png"))
        logging.info(f"Skin applied for {nickname}")

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_settings(self):
        self.settings["nickname"] = self.nickname_entry.get()
        self.settings["selected_build"] = self.build_var.get()
        with open("settings.json", "w") as f:
            json.dump(self.settings, f, indent=4)

    def load_builds(self):
        logging.debug("Loading builds from server")
        try:
            response = requests.get("http://178.173.82.2:1000/builds")
            response.raise_for_status()
            builds = response.json()
            logging.debug(f"Loaded builds: {builds}")
            return builds
        except requests.RequestException as e:
            logging.error(f"Failed to load builds: {e}")
            messagebox.showerror("Error", "Failed to load builds")
            return []

    def download_build(self, build_name):
        build_path = os.path.join("builds", build_name)
        os.makedirs(build_path, exist_ok=True)

        for folder in ["mods", "shaderpacks", "resourcepacks"]:
            folder_path = os.path.join(build_path, folder)
            os.makedirs(folder_path, exist_ok=True)

            logging.info(f"Downloading files for build {build_name} in {folder}")
            try:
                response = requests.get(f"http://178.173.82.2:1000/build/{build_name}")
                response.raise_for_status()
                build_info = response.json()
                logging.debug(f"Received build info: {build_info}")

                for file_info in build_info.get(folder, []):
                    if "name" in file_info:
                        file_name = file_info["name"]
                        file_path = os.path.join(folder_path, file_name)

                        url = f"http://178.173.82.2:1000/build/download/{build_name}/{folder}/{file_name}"
                        with requests.get(url, stream=True) as r:
                            r.raise_for_status()
                            with open(file_path, 'wb') as f:
                                shutil.copyfileobj(r.raw, f)
                        logging.info(f"Downloaded {file_name} successfully")
                    else:
                        logging.error(f"Missing 'name' in file info: {file_info}")
            except requests.RequestException as e:
                logging.error(f"Failed to download files for {build_name} in {folder}: {e}")
                messagebox.showerror("Error", f"Failed to download files for {build_name} in {folder}")
                return

    def launch_game(self):
        nickname = self.nickname_entry.get()
        build = self.build_var.get()
        logging.debug(f"Launching game with nickname: {nickname}, build: {build}")
        if not nickname:
            logging.error("No nickname entered")
            messagebox.showerror("Error", "Please enter a nickname")
            return
        if not build:
            logging.error("No build selected")
            messagebox.showerror("Error", "Please select a build")
            return

        self.save_settings()
        self.download_build(build)
        self.run_minecraft(nickname, build)

    def run_minecraft(self, nickname, build):
        ram = self.settings.get("ram", 4000)
        close_launcher = self.settings.get("close_launcher", False)

        try:
            logging.debug(f"Fetching version details for build {build}")
            response = requests.get(f"http://178.173.82.2:1000/build/{build}")
            response.raise_for_status()
            build_info = response.json()
            logging.debug(f"Received build info: {build_info}")
            version_name = build_info["version"]
            mc_directory = os.path.join("builds", build_info["name"])

            logging.debug(f"Fetching version details for {version_name}")
            response = requests.get(f"http://178.173.82.2:1000/versions")
            response.raise_for_status()
            versions = response.json()
            if version_name not in versions:
                raise ValueError(f"Version {version_name} not found in available versions")
            version_details = versions[version_name]
            forge_version = version_details["forge_version"]
            name_version = version_details["name"]

            version_path = os.path.join(mc_directory, "versions", version_name)
            logging.debug(f"Version path: {version_path}")
            if not os.path.exists(version_path):
                os.makedirs(version_path, exist_ok=True)
                logging.debug(f"Downloading Minecraft version {name_version}")
                try:
                    response = requests.get(f"http://178.173.82.2:1000/version/download/{version_name}")
                    response.raise_for_status()
                    with open(os.path.join(version_path, f"{forge_version}.jar"), "wb") as f:
                        f.write(response.content)
                except requests.exceptions.RequestException as e:
                    logging.error(f"Error downloading Minecraft version {forge_version}: {e}")
                except Exception as e:
                    logging.error(f"Error saving Minecraft version {forge_version}: {e}")
            mll.forge.install_forge_version(forge_version, mc_directory)

            options = {
                "username": nickname,
                "uuid": str(uuid.uuid4()),
                "token": "0",
                "jvmArguments": [f"-Xmx{ram}M"]
            }
            logging.debug(f"Getting Minecraft command for version: {version_name}")
            command = mll.command.get_minecraft_command(name_version, mc_directory, options)

            logging.info(f"Launching Minecraft with command: {command}")

            if close_launcher:
                self.withdraw()
                process = subprocess.Popen(command)
                process.wait()
                self.deiconify()
            else:
                if self.settings.get("dev_mode", False):
                    subprocess.Popen(command)
                else:
                    subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        except Exception as e:
            logging.error(f"Failed to launch game: {e}")
            messagebox.showerror("Error", f"Failed to launch game: {e}")

    def open_settings(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Настройки")
        settings_window.geometry("300x400")

        ttk.Label(settings_window, text="Выделенная память (MB):").pack(pady=5)
        ram_value = tk.IntVar()
        ram_slider = ttk.Scale(settings_window, from_=1024, to=16384, orient=tk.HORIZONTAL, variable=ram_value)
        ram_slider.set(self.settings.get("ram", 4000))
        ram_slider.pack(pady=5)

        ram_label = ttk.Label(settings_window, text=f"{ram_slider.get()} MB")
        ram_label.pack(pady=5)

        def update_ram_label(value):
            ram_label.config(text=f"{int(float(value))} MB")
        ram_slider.config(command=update_ram_label)

        dev_mode_var = tk.BooleanVar(value=self.settings.get("dev_mode", False))
        ttk.Checkbutton(settings_window, text="Запуск в режиме разработчика", variable=dev_mode_var).pack(pady=5)

        theme_var = tk.StringVar(value=self.theme)
        ttk.Radiobutton(settings_window, text="Светлая тема", variable=theme_var, value="light").pack(pady=5)
        ttk.Radiobutton(settings_window, text="Тёмная тема", variable=theme_var, value="dark").pack(pady=5)

        close_launcher_var = tk.BooleanVar(value=self.settings.get("close_launcher", False))
        ttk.Checkbutton(settings_window, text="Закрыть лаунчер при запуске игры", variable=close_launcher_var).pack(pady=5)

        ttk.Button(settings_window, text="Показать файлы игры", command=self.show_game_files).pack(pady=10)

        def save_and_close():
            self.settings["ram"] = int(ram_slider.get())
            self.settings["dev_mode"] = dev_mode_var.get()
            self.settings["theme"] = theme_var.get()
            self.settings["close_launcher"] = close_launcher_var.get()
            self.apply_theme()
            self.save_settings()
            settings_window.destroy()

        ttk.Button(settings_window, text="Сохранить", command=save_and_close).pack(pady=20)

    def show_game_files(self):
        game_files_path = os.path.join("builds")
        logging.info(f"Opening game files at: {game_files_path}")
        try:
            if platform.system() == "Windows":
                os.startfile(game_files_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", game_files_path])
            else:
                subprocess.Popen(["xdg-open", game_files_path])
        except Exception as e:
            logging.error(f"Failed to open game files: {e}")
            messagebox.showerror("Error", f"Failed to open game files: {e}")

if __name__ == "__main__":
    logging.info("Starting Minecraft Launcher")
    app = MinecraftLauncher()
    app.mainloop()
