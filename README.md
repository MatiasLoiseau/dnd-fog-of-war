# D&D Fog of War

Pequeña app de escritorio en Python que permite revelar zonas de un mapa de D&D con efecto “fog of war”. Carga una imagen, y con el mouse vas revelando el mapa en círculos. El radio se puede ajustar con la rueda del mouse.

## Requisitos

- Python 3.10+
- Dependencias de Python:
  - Pillow
  - screeninfo (opcional, mejora el ajuste al monitor)

Instalación rápida:

```bash
pip install -r requirements.txt
```

## Uso

1. Ejecutá el programa y seleccioná una imagen cuando lo pida.
2. Click o arrastre con el mouse para revelar áreas.
3. Usá la rueda del mouse para aumentar o disminuir el radio.

Parámetros disponibles:

- `-i`, `--image`: ruta al archivo del mapa.
- `-r`, `--radius`: radio inicial de revelado (en px).

## Ejemplo

```bash
python main.py --image ./images/mi-mapa.png --radius 80
```

Si no pasás `--image`, se abrirá un diálogo para elegir el archivo.
