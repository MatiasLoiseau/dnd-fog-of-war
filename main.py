import argparse
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageDraw, ImageTk


DEFAULT_RADIUS = 60


def load_map_image(path: str) -> Image.Image:
    try:
        image = Image.open(path).convert("RGB")
    except Exception as exc:
        raise RuntimeError(f"No se pudo abrir la imagen: {path}\n{exc}") from exc
    return image


def pick_image_via_dialog() -> str | None:
    return filedialog.askopenfilename(
        title="Seleccionar mapa",
        filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.webp")],
    )


def build_display_image(map_image: Image.Image, mask: Image.Image) -> Image.Image:
    black = Image.new("RGB", map_image.size, (0, 0, 0))
    return Image.composite(map_image, black, mask)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fog of War para mapas de D&D")
    parser.add_argument("--image", "-i", help="Ruta de la imagen del mapa")
    parser.add_argument("--radius", "-r", type=int, default=DEFAULT_RADIUS, help="Radio de revelado")
    args = parser.parse_args()

    root = tk.Tk()
    root.title("D&D Fog of War")

    image_path = args.image
    if not image_path:
        image_path = pick_image_via_dialog()
        if not image_path:
            messagebox.showinfo("Sin imagen", "No se seleccionó ninguna imagen.")
            return

    if not os.path.exists(image_path):
        messagebox.showerror("Imagen no encontrada", f"No existe: {image_path}")
        return

    try:
        map_image = load_map_image(image_path)
    except RuntimeError as exc:
        messagebox.showerror("Error", str(exc))
        return

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    usable_width = max(200, screen_width - 80)
    usable_height = max(200, screen_height - 160)

    scale = min(1.0, usable_width / map_image.width, usable_height / map_image.height)
    display_size = (int(map_image.width * scale), int(map_image.height * scale))
    display_map = map_image.resize(display_size, Image.Resampling.LANCZOS) if scale < 1.0 else map_image

    radius = max(5, int(args.radius * scale))

    mask = Image.new("L", display_map.size, 0)
    mask_draw = ImageDraw.Draw(mask)

    display_image = build_display_image(display_map, mask)
    tk_image = ImageTk.PhotoImage(display_image)

    root.geometry(f"{display_map.width}x{display_map.height + 24}")

    canvas = tk.Canvas(root, width=display_map.width, height=display_map.height, highlightthickness=0)
    canvas.pack()

    image_id = canvas.create_image(0, 0, anchor="nw", image=tk_image)

    def refresh_display() -> None:
        nonlocal tk_image
        updated = build_display_image(display_map, mask)
        tk_image = ImageTk.PhotoImage(updated)
        canvas.itemconfigure(image_id, image=tk_image)

    def reveal_at(x: int, y: int) -> None:
        left = x - radius
        top = y - radius
        right = x + radius
        bottom = y + radius
        mask_draw.ellipse([left, top, right, bottom], fill=255)
        refresh_display()

    def on_click(event: tk.Event) -> None:
        reveal_at(event.x, event.y)

    def on_drag(event: tk.Event) -> None:
        reveal_at(event.x, event.y)

    canvas.bind("<Button-1>", on_click)
    canvas.bind("<B1-Motion>", on_drag)

    def on_mouse_wheel(event: tk.Event) -> None:
        nonlocal radius
        delta = event.delta if event.delta != 0 else (1 if event.num == 4 else -1)
        if delta > 0:
            radius = min(300, radius + 5)
        else:
            radius = max(5, radius - 5)
        status_var.set(f"Radio: {radius}px")

    status_var = tk.StringVar(value=f"Radio: {radius}px")
    status = tk.Label(root, textvariable=status_var, anchor="w")
    status.pack(fill="x")

    canvas.bind("<MouseWheel>", on_mouse_wheel)
    canvas.bind("<Button-4>", on_mouse_wheel)
    canvas.bind("<Button-5>", on_mouse_wheel)

    root.mainloop()


if __name__ == "__main__":
    main()
