import argparse
import os
import tkinter as tk
import traceback
from tkinter import filedialog, messagebox

from PIL import Image, ImageDraw, ImageTk

try:
    from screeninfo import get_monitors
except Exception:  # pragma: no cover - fallback si no está instalado
    get_monitors = None


DEFAULT_RADIUS = 60
MARGIN_X = 8
MARGIN_Y = 56


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

    def report_callback_exception(exc: BaseException, val: BaseException, tb) -> None:  # type: ignore[override]
        traceback.print_exception(exc, val, tb)

    root.report_callback_exception = report_callback_exception

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

    def get_usable_area() -> tuple[int, int]:
        if get_monitors is None:
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            return max(200, screen_width - MARGIN_X), max(200, screen_height - MARGIN_Y)

        try:
            root.update_idletasks()
            win_x = root.winfo_rootx()
            win_y = root.winfo_rooty()
            win_w = max(1, root.winfo_width())
            win_h = max(1, root.winfo_height())
            center_x = win_x + win_w / 2
            center_y = win_y + win_h / 2

            for monitor in get_monitors():
                left = monitor.x
                top = monitor.y
                right = monitor.x + monitor.width
                bottom = monitor.y + monitor.height
                if left <= center_x <= right and top <= center_y <= bottom:
                    return max(200, monitor.width - MARGIN_X), max(200, monitor.height - MARGIN_Y)
        except Exception:
            pass

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        return max(200, screen_width - MARGIN_X), max(200, screen_height - MARGIN_Y)

    def compute_scale() -> float:
        usable_width, usable_height = get_usable_area()
        return min(1.0, usable_width / map_image.width, usable_height / map_image.height)

    scale = compute_scale()
    radius = max(5, int(args.radius * scale))

    mask_full = Image.new("L", map_image.size, 0)
    mask_full_draw = ImageDraw.Draw(mask_full)

    def build_display_assets() -> tuple[Image.Image, Image.Image]:
        display_size = (int(map_image.width * scale), int(map_image.height * scale))
        display_map = (
            map_image.resize(display_size, Image.Resampling.LANCZOS)
            if scale < 1.0
            else map_image
        )
        display_mask = (
            mask_full.resize(display_map.size, Image.Resampling.NEAREST)
            if scale < 1.0
            else mask_full
        )
        return display_map, display_mask

    display_map, display_mask = build_display_assets()
    display_image = build_display_image(display_map, display_mask)
    tk_image = ImageTk.PhotoImage(display_image)

    root.geometry(f"{display_map.width}x{display_map.height}")

    canvas = tk.Canvas(root, width=display_map.width, height=display_map.height, highlightthickness=0)
    canvas.pack()

    image_id = canvas.create_image(0, 0, anchor="nw", image=tk_image)

    updating_layout = False
    current_size = (display_map.width, display_map.height)

    def refresh_display() -> None:
        nonlocal tk_image, display_map, display_mask, updating_layout, current_size
        display_map, display_mask = build_display_assets()
        updated = build_display_image(display_map, display_mask)
        tk_image = ImageTk.PhotoImage(updated)
        canvas.itemconfigure(image_id, image=tk_image)
        new_size = (display_map.width, display_map.height)
        if new_size != current_size and not updating_layout:
            updating_layout = True
            try:
                canvas.config(width=display_map.width, height=display_map.height)
                root.geometry(f"{display_map.width}x{display_map.height}")
                current_size = new_size
            finally:
                updating_layout = False

    def reveal_at(x: int, y: int) -> None:
        if scale <= 0:
            return
        full_x = int(x / scale)
        full_y = int(y / scale)
        full_radius = max(1, int(radius / scale))
        left = full_x - full_radius
        top = full_y - full_radius
        right = full_x + full_radius
        bottom = full_y + full_radius
        mask_full_draw.ellipse([left, top, right, bottom], fill=255)
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
        root.title(f"D&D Fog of War — Radio: {radius}px")

    root.title(f"D&D Fog of War — Radio: {radius}px")

    def on_configure(event: tk.Event) -> None:
        nonlocal scale, radius
        if updating_layout:
            return
        new_scale = compute_scale()
        if abs(new_scale - scale) > 0.01:
            radius = max(5, int(radius * new_scale / scale))
            scale = new_scale
            root.title(f"D&D Fog of War — Radio: {radius}px")
            refresh_display()

    canvas.bind("<MouseWheel>", on_mouse_wheel)
    canvas.bind("<Button-4>", on_mouse_wheel)
    canvas.bind("<Button-5>", on_mouse_wheel)
    root.bind("<Configure>", on_configure)

    root.mainloop()


if __name__ == "__main__":
    main()
