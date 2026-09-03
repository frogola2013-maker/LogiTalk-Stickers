import base64
import io
import os
import threading
from socket import socket, AF_INET, SOCK_STREAM

from customtkinter import *
from tkinter import filedialog
from PIL import Image


HOST = "2.tcp.eu.ngrok.io"
PORT = 17270

STICKERS = [
    "STICKERS/image (1).jpg",
    "STICKERS/image (2).jpg",
    "STICKERS/image (3).jpg",
    "STICKERS/image (4).jpg",
    "STICKERS/image (5).jpg",
    "STICKERS/image (6).jpg",
    "STICKERS/image (7).jpg"
]


class MainWindow(CTk):
    def __init__(self):
        super().__init__()

        self.geometry("400x300")
        self.title("Chat Client")
        self.username = "new user"

        self.stickers = {}
        self.sticker_images = []
        self.message_images = []
        self.sticker_menu = None

        self.load_stickers()

        self.label = None
        self.menu_frame = CTkFrame(self, width=30, height=300)
        self.menu_frame.pack_propagate(False)
        self.menu_frame.place(x=0, y=0)

        self.is_show_menu = False
        self.speed_animate_menu = -20

        self.btn = CTkButton(self, text="▶️", width=30, command=self.toggle_show_menu)
        self.btn.place(x=0, y=0)

        self.chat_field = CTkScrollableFrame(self)
        self.chat_field.place(x=0, y=0)

        self.message_entry_frame = CTkFrame(self, fg_color="transparent")
        self.message_entry_frame.place(x=0, y=0)

        self.message_entry = CTkEntry(
            self.message_entry_frame,
            placeholder_text="Введіть повідомлення:",
            height=40
        )
        self.message_entry.place(x=0, y=0)

        self.sticker_button = CTkButton(self.message_entry_frame, text="🙂", width=40, height=34, command=self.toggle_sticker_menu)
        self.sticker_button.place(relx=1, x=-5, rely=0.5, anchor="e")

        self.send_button = CTkButton(self, text=">", width=50, height=40, command=self.send_message)
        self.send_button.place(x=0, y=0)

        self.open_img_button = CTkButton(self, text="📂", width=50, height=40, command=self.open_image)
        self.open_img_button.place(x=0, y=0)

        self.adaptive_ui()

        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            self.sock.send(f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n".encode("utf-8"))
            threading.Thread(target=self.recv_message, daemon=True).start()
        except Exception as e:
            self.add_message(f"Не вдалося підключитися до сервера: {e}")

    def toggle_show_menu(self):
        self.is_show_menu = not self.is_show_menu
        self.speed_animate_menu *= -1
        self.btn.configure(text="◀️" if self.is_show_menu else "▶️")
        self.show_menu()

        if self.is_show_menu:
            self.label = CTkLabel(self.menu_frame, text="Імʼя")
            self.label.pack(pady=30)

            self.entry = CTkEntry(self.menu_frame, placeholder_text="Ваш нік...")
            self.entry.pack()

            self.save_button = CTkButton(self.menu_frame, text="Зберегти", command=self.save_name)
            self.save_button.pack()

    def show_menu(self, *args):
        width = self.menu_frame.winfo_width() + self.speed_animate_menu
        self.menu_frame.configure(width=width)

        if self.is_show_menu and width < 200:
            self.after(10, self.show_menu, *args)
        elif not self.is_show_menu and width >= 60:
            self.after(10, self.show_menu, *args)
            for widget in ("label", "entry", "save_button"):
                obj = getattr(self, widget, None)
                if obj:
                    obj.destroy()

    def save_name(self):
        name = self.entry.get().strip()
        if name:
            self.username = name
            self.add_message(f"Ваш новий нік: {self.username}")

    def adaptive_ui(self, *args):
        menu_width = self.menu_frame.winfo_width()
        width = self.winfo_width()
        height = self.winfo_height()

        self.menu_frame.configure(height=height)
        self.chat_field.place(x=menu_width)
        self.chat_field.configure(width=width - menu_width - 20, height=height - 40)

        self.send_button.place(x=width - 50, y=height - 40)
        self.open_img_button.place(x=width - 105, y=self.send_button.winfo_y())

        self.message_entry_frame.place(x=menu_width, y=self.send_button.winfo_y())
        self.message_entry_frame.configure(width=width - menu_width - 110, height=40)
        self.message_entry.configure(width=self.message_entry_frame.winfo_width())

        self.after(50, self.adaptive_ui, *args)

    def add_message(self, message, img=None):
        frame = CTkFrame(self.chat_field, fg_color="grey")
        frame.pack(pady=5, anchor="w")

        wraplength = (self.winfo_width() - self.menu_frame.winfo_width() - 40)

        label = CTkLabel(frame, text=message, wraplength=wraplength, text_color="white", justify="left", image=img, compound="top")
        label.pack(padx=10, pady=5)

        if img:
            self.message_images.append(img)

    def send_message(self):
        message = self.message_entry.get().strip()

        if message:
            self.add_message(f"{self.username}: {message}")
            try:
                self.sock.sendall(f"TEXT@{self.username}@{message}\n".encode("utf-8"))
            except:
                pass

        self.message_entry.delete(0, END)

    def recv_message(self):
        buffer = ""
        while True:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.after(0, self.handle_line, line.strip())
            except:
                break
        self.sock.close()

    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 3)
        msg_type = parts[0]
        if msg_type == "TEXT" and len(parts) >= 3:
            self.add_message(f"{parts[1]}: {parts[2]}")
        elif msg_type in ("IMAGE", "STICKER") and len(parts) >= 4:
            try:
                image = Image.open(io.BytesIO(base64.b64decode(parts[3])))
                image.load()
                size = (300, 300) if msg_type == "IMAGE" else (150, 150)
                img = CTkImage(light_image=image, dark_image=image, size=size)
                text = (f"{parts[1]} надіслав(ла) {'зображення' if msg_type == 'IMAGE' else 'стікер'}: {parts[2]}")

                self.add_message(text, img)

            except Exception as e:
                self.add_message(f"Помилка відображення {'зображення' if msg_type == 'IMAGE' else 'стікера'}: {e}")
        else:
            self.add_message(line)

    def open_image(self):
        file_name = filedialog.askopenfilename()
        if not file_name:
            return
        try:
            with open(file_name, "rb") as file:
                raw = file.read()
            name = os.path.basename(file_name)
            data = (f"IMAGE@{self.username}@{name}@{base64.b64encode(raw).decode()}\n")
            self.sock.sendall(data.encode())

            image = Image.open(file_name)
            image.load()
            img = CTkImage(light_image=image, dark_image=image, size=(300, 300))
            self.add_message(f"{self.username} надіслав(ла) зображення: {name}", img)
        except Exception as e:
            self.add_message(f"Не вдалося надіслати зображення: {e}")

    def toggle_sticker_menu(self):
        if self.sticker_menu and self.sticker_menu.winfo_exists():
            self.sticker_menu.destroy()
            self.sticker_menu = None
            return

        self.open_sticker_menu()

    def open_sticker_menu(self):
        self.sticker_menu = CTkToplevel(self)
        self.sticker_menu.overrideredirect(True)
        self.sticker_menu.transient(self)
        self.sticker_menu.resizable(False, False)

        width, height = 320, 320
        x = self.sticker_button.winfo_rootx()
        button_y = self.sticker_button.winfo_rooty()
        y = button_y - height - 5

        if y < 0:
            y = button_y + self.sticker_button.winfo_height() + 5

        self.sticker_menu.geometry(f"{width}x{height}+{x}+{y}")
        self.sticker_menu.lift()
        self.sticker_menu.attributes("-topmost", True)
        self.sticker_menu.focus_force()

        frame = CTkFrame(self.sticker_menu, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.sticker_images.clear()

        for index, (path, image) in enumerate(self.stickers.items()):
            image = image.copy()
            image.thumbnail((55, 55), Image.Resampling.LANCZOS)

            img = CTkImage(light_image=image, dark_image=image, size=(55, 55))
            self.sticker_images.append(img)

            button = CTkButton(frame, text="", image=img, width=65, height=65, command=lambda p=path: self.send_sticker(p))
            button.grid(row=index // 4, column=index % 4, padx=5, pady=5)

    def load_stickers(self):
        for path in STICKERS:
            try:
                image = Image.open(path).convert("RGBA")
                self.stickers[path] = image
            except Exception as e:
                print(f"Не вдалося завантажити локальний стікер {path}: {e}")

    def send_sticker(self, path):
        try:
            image = self.stickers.get(path)

            if image is None:
                self.add_message("Стікер недоступний")
                return

            image = image.copy()
            image.thumbnail((150, 150), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            image.save(buffer, format="PNG")

            filename = os.path.basename(path)
            data = (f"STICKER@{self.username}@{filename}@{base64.b64encode(buffer.getvalue()).decode()}\n")
            self.sock.sendall(data.encode())

            img = CTkImage(light_image=image, dark_image=image, size=(150, 150))

            self.add_message(f"{self.username} надіслав(ла) стікер: {filename}", img)

            if self.sticker_menu:
                self.sticker_menu.destroy()
                self.sticker_menu = None

        except Exception as e:
            self.add_message(f"Не вдалося надіслати стікер: {e}")


if __name__ == "__main__":
    MainWindow().mainloop()