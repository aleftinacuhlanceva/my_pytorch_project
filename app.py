# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageTk


class ImageProcessingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Processing App")
        self.root.geometry("1080x720")
        self.root.minsize(900, 620)

        self.original_image = None
        self.current_image = None
        self.preview_image = None

        self.channel_var = tk.StringVar(value="R")
        self.threshold_var = tk.StringVar(value="150")
        self.x_var = tk.StringVar(value="40")
        self.y_var = tk.StringVar(value="40")
        self.width_var = tk.StringVar(value="220")
        self.height_var = tk.StringVar(value="140")
        self.status_var = tk.StringVar(value="Выберите изображение или сделайте снимок с веб-камеры.")

        self._build_ui()

    def _build_ui(self):
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        controls = tk.Frame(self.root, padx=12, pady=12)
        controls.grid(row=0, column=0, sticky="ns")

        preview = tk.Frame(self.root, bg="#202124", padx=12, pady=12)
        preview.grid(row=0, column=1, sticky="nsew")
        preview.columnconfigure(0, weight=1)
        preview.rowconfigure(0, weight=1)

        self.image_label = tk.Label(preview, bg="#202124", fg="white", text="Нет изображения")
        self.image_label.grid(row=0, column=0, sticky="nsew")

        tk.Label(controls, text="Источник").pack(anchor="w")
        tk.Button(controls, text="Загрузить PNG/JPG", command=self.load_image).pack(fill="x", pady=(4, 4))
        tk.Button(controls, text="Снимок с веб-камеры", command=self.capture_from_webcam).pack(fill="x", pady=(0, 10))

        tk.Label(controls, text="Просмотр").pack(anchor="w")
        tk.Button(controls, text="Показать исходное", command=self.show_original).pack(fill="x", pady=(4, 4))

        channel_frame = tk.Frame(controls)
        channel_frame.pack(fill="x", pady=(0, 4))
        for channel in ("R", "G", "B"):
            tk.Radiobutton(channel_frame, text=channel, variable=self.channel_var, value=channel).pack(side="left")
        tk.Button(controls, text="Показать канал", command=self.show_channel).pack(fill="x", pady=(0, 10))

        tk.Label(controls, text="Маска красного цвета").pack(anchor="w")
        threshold_frame = tk.Frame(controls)
        threshold_frame.pack(fill="x", pady=(4, 4))
        tk.Label(threshold_frame, text="Порог:").pack(side="left")
        tk.Entry(threshold_frame, textvariable=self.threshold_var, width=8).pack(side="left", padx=(6, 0))
        tk.Button(controls, text="Показать маску", command=self.show_red_mask).pack(fill="x", pady=(0, 10))

        tk.Label(controls, text="Обработка").pack(anchor="w")
        tk.Button(controls, text="Повысить резкость", command=self.sharpen_image).pack(fill="x", pady=(4, 10))

        tk.Label(controls, text="Синий прямоугольник").pack(anchor="w")
        rect_grid = tk.Frame(controls)
        rect_grid.pack(fill="x", pady=(4, 4))
        labels = ("X", "Y", "Ширина", "Высота")
        variables = (self.x_var, self.y_var, self.width_var, self.height_var)
        for i, (label, variable) in enumerate(zip(labels, variables)):
            tk.Label(rect_grid, text=label).grid(row=i, column=0, sticky="w", pady=2)
            tk.Entry(rect_grid, textvariable=variable, width=10).grid(row=i, column=1, sticky="ew", pady=2)
        tk.Button(controls, text="Нарисовать", command=self.draw_rectangle).pack(fill="x", pady=(0, 10))

        tk.Button(controls, text="Сохранить результат", command=self.save_current_image).pack(fill="x", pady=(8, 0))

        status = tk.Label(self.root, textvariable=self.status_var, anchor="w", padx=12, pady=6)
        status.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.root.bind("<Configure>", lambda _event: self.refresh_preview())

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение",
            filetypes=(("Images", "*.png *.jpg *.jpeg"), ("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg")),
        )
        if not file_path:
            return

        try:
            image = Image.open(file_path).convert("RGB")
        except Exception as exc:
            self.show_error("Не удалось открыть изображение", exc)
            return

        self.set_image(image, "Загружено изображение: {}".format(Path(file_path).name))

    def capture_from_webcam(self):
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not camera.isOpened():
            messagebox.showerror(
                "Ошибка веб-камеры",
                "Не удалось подключиться к веб-камере.\n\n"
                "Проверьте, подключена ли камера, не используется ли она другой программой, "
                "разрешён ли доступ к камере в настройках Windows и установлены ли драйверы.",
            )
            self.status_var.set("Веб-камера недоступна.")
            return

        ok, frame = camera.read()
        camera.release()

        if not ok or frame is None:
            messagebox.showerror("Ошибка веб-камеры", "Камера подключена, но снимок получить не удалось.")
            self.status_var.set("Не удалось получить кадр с веб-камеры.")
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)
        self.set_image(image, "Снимок с веб-камеры получен.")

    def show_original(self):
        if not self.ensure_image():
            return
        self.current_image = self.original_image.copy()
        self.status_var.set("Показано исходное изображение.")
        self.refresh_preview()

    def show_channel(self):
        if not self.ensure_image():
            return

        image_array = np.array(self.original_image)
        result = np.zeros_like(image_array)
        channel_index = {"R": 0, "G": 1, "B": 2}[self.channel_var.get()]
        result[:, :, channel_index] = image_array[:, :, channel_index]

        self.current_image = Image.fromarray(result)
        self.status_var.set("Показан {}-канал изображения.".format(self.channel_var.get()))
        self.refresh_preview()

    def show_red_mask(self):
        if not self.ensure_image():
            return

        threshold = self.read_int(self.threshold_var, "Порог", 0, 255)
        if threshold is None:
            return

        red = np.array(self.original_image)[:, :, 0]
        mask = np.where(red > threshold, 255, 0).astype(np.uint8)
        self.current_image = Image.fromarray(mask, mode="L").convert("RGB")
        self.status_var.set("Показана маска: красный канал > {}.".format(threshold))
        self.refresh_preview()

    def sharpen_image(self):
        if not self.ensure_image():
            return

        self.current_image = self.original_image.filter(ImageFilter.SHARPEN).filter(ImageFilter.SHARPEN)
        self.status_var.set("Резкость изображения повышена.")
        self.refresh_preview()

    def draw_rectangle(self):
        if not self.ensure_image():
            return

        x = self.read_int(self.x_var, "X", 0, self.original_image.width - 1)
        y = self.read_int(self.y_var, "Y", 0, self.original_image.height - 1)
        width = self.read_int(self.width_var, "Ширина", 1, self.original_image.width)
        height = self.read_int(self.height_var, "Высота", 1, self.original_image.height)
        if None in (x, y, width, height):
            return

        x2 = min(x + width, self.original_image.width - 1)
        y2 = min(y + height, self.original_image.height - 1)

        result = self.original_image.copy()
        draw = ImageDraw.Draw(result)
        draw.rectangle((x, y, x2, y2), outline=(0, 0, 255), width=4)
        self.current_image = result
        self.status_var.set("Нарисован синий прямоугольник.")
        self.refresh_preview()

    def save_current_image(self):
        if not self.ensure_image():
            return

        file_path = filedialog.asksaveasfilename(
            title="Сохранить результат",
            defaultextension=".png",
            filetypes=(("PNG", "*.png"), ("JPEG", "*.jpg")),
        )
        if not file_path:
            return

        try:
            self.current_image.save(file_path)
        except Exception as exc:
            self.show_error("Не удалось сохранить изображение", exc)
            return

        self.status_var.set("Результат сохранён: {}".format(Path(file_path).name))

    def set_image(self, image, status):
        self.original_image = image
        self.current_image = image.copy()
        self.status_var.set(status)
        self.refresh_preview()

    def ensure_image(self):
        if self.original_image is None:
            messagebox.showwarning("Нет изображения", "Сначала загрузите изображение или сделайте снимок.")
            self.status_var.set("Действие невозможно: изображение не выбрано.")
            return False
        return True

    def read_int(self, variable, name, minimum, maximum):
        try:
            value = int(variable.get())
        except ValueError:
            messagebox.showerror("Некорректный ввод", "{} должно быть целым числом.".format(name))
            self.status_var.set("Ошибка ввода: {}.".format(name))
            return None

        if value < minimum or value > maximum:
            messagebox.showerror(
                "Некорректный ввод",
                "{} должно быть в диапазоне от {} до {}.".format(name, minimum, maximum),
            )
            self.status_var.set("Ошибка диапазона: {}.".format(name))
            return None

        return value

    def refresh_preview(self):
        if self.current_image is None:
            return

        label_width = max(self.image_label.winfo_width(), 300)
        label_height = max(self.image_label.winfo_height(), 300)
        image = self.current_image.copy()
        image.thumbnail((label_width - 20, label_height - 20), Image.LANCZOS)
        self.preview_image = ImageTk.PhotoImage(image)
        self.image_label.configure(image=self.preview_image, text="")

    @staticmethod
    def show_error(title, exc):
        messagebox.showerror(title, "{}".format(exc))


if __name__ == "__main__":
    window = tk.Tk()
    app = ImageProcessingApp(window)
    window.mainloop()
