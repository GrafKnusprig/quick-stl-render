import argparse
import numpy as np
import pyvista as pv
from PIL import Image, ImageDraw, ImageFont


COLORS = {
    "black": (20, 20, 20),
    "grey": (150, 150, 150),
    "gray": (150, 150, 150),
    "red": (210, 30, 30),
    "green": (40, 140, 70),
    "blue": (40, 90, 180),
    "pink": (255, 92, 239),
    "violet": (155, 80, 230)
}


def get_font(size, bold=False):
    candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def render_view(mesh, camera_position, object_color, size=(850, 420)):
    plotter = pv.Plotter(off_screen=True, window_size=size)
    plotter.set_background("white")

    plotter.add_mesh(
        mesh,
        color=np.array(object_color) / 255.0,
        show_edges=False,
        edge_color=(70, 70, 70),
        line_width=0.05,
        smooth_shading=False,
        specular=0.55,
        roughness=0.65,
    )

    plotter.camera_position = camera_position
    plotter.camera.parallel_projection = True
    plotter.reset_camera()
    plotter.camera.zoom(1.35)

    img = plotter.screenshot(return_img=True)
    plotter.close()
    return Image.fromarray(img)


def draw_centered(draw, box, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = box[0] + (box[2] - box[0] - (bbox[2] - bbox[0])) / 2
    y = box[1] + (box[3] - box[1] - (bbox[3] - bbox[1])) / 2
    draw.text((x, y), text, font=font, fill=fill)


def draw_dimension(draw, p1, p2, label, color, font, text_side="bottom"):
    x1, y1 = p1
    x2, y2 = p2
    line_w = 3
    tick = 18

    draw.line((x1, y1, x2, y2), fill=color, width=line_w)

    if abs(y2 - y1) < abs(x2 - x1):  # horizontal
        draw.line((x1, y1 - tick, x1, y1 + tick), fill=color, width=line_w)
        draw.line((x2, y2 - tick, x2, y2 + tick), fill=color, width=line_w)

        bbox = draw.textbbox((0, 0), label, font=font)
        tx = (x1 + x2 - (bbox[2] - bbox[0])) / 2
        ty = y1 + 14
        draw.text((tx, ty), label, font=font, fill=color)

    else:  # vertical
        draw.line((x1 - tick, y1, x1 + tick, y1), fill=color, width=line_w)
        draw.line((x2 - tick, y2, x2 + tick, y2), fill=color, width=line_w)

        bbox = draw.textbbox((0, 0), label, font=font)
        tx = x1 + 24
        ty = (y1 + y2 - (bbox[3] - bbox[1])) / 2
        draw.text((tx, ty), label, font=font, fill=color)


def paste_view(canvas, draw, view_img, box, title, font_title, pad=70):
    x1, y1, x2, y2 = box

    draw_centered(draw, (x1, y1 + 5, x2, y1 + 42), title, font_title, (20, 20, 20))

    available = (x2 - x1 - 190, y2 - y1 - 145)
    view_img.thumbnail(available, Image.Resampling.LANCZOS)

    px = x1 + (x2 - x1 - view_img.width) // 2
    py = y1 + 60 + (y2 - y1 - 95 - view_img.height) // 2
    canvas.paste(view_img, (px, py))

    # find actual non-white object pixels
    arr = np.array(view_img.convert("RGB"))
    mask = np.any(arr < 245, axis=2)
    ys, xs = np.where(mask)

    ox1 = px + xs.min()
    ox2 = px + xs.max()
    oy1 = py + ys.min()
    oy2 = py + ys.max()

    return (px, py, px + view_img.width, py + view_img.height), (ox1, oy1, ox2, oy2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_stl")
    parser.add_argument("output_png")
    parser.add_argument("--title", default="")
    parser.add_argument("--author", default="")
    parser.add_argument("--dimensions", action="store_true")
    parser.add_argument("--dimensions-color", default="black", choices=COLORS.keys())
    parser.add_argument("--object-color", default="grey", choices=COLORS.keys())
    args = parser.parse_args()

    W, H = 1920, 1080
    canvas = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(canvas)

    title_font = get_font(46, bold=True)
    author_font = get_font(26)
    view_font = get_font(24, bold=True)
    dim_font = get_font(19)
    note_font = get_font(15)

    dim_color = COLORS[args.dimensions_color]
    obj_color = COLORS[args.object_color]

    mesh = pv.read(args.input_stl)
    bounds = mesh.bounds
    width = bounds[1] - bounds[0]   # X
    depth = bounds[3] - bounds[2]   # Y
    height = bounds[5] - bounds[4]  # Z

    mesh.translate(
        (
            -(bounds[0] + bounds[1]) / 2,
            -(bounds[2] + bounds[3]) / 2,
            -(bounds[4] + bounds[5]) / 2,
        ),
        inplace=True,
    )

    # page title
    if args.title:
        draw_centered(draw, (0, 20, W, 80), args.title, title_font, (10, 10, 10))
    if args.author:
        draw_centered(draw, (0, 78, W, 118), args.author, author_font, (30, 30, 30))

    # subtle border and separators
    draw.rectangle((16, 16, W - 16, H - 16), outline=(30, 30, 30), width=2)
    draw.line((W // 2, 150, W // 2, H - 45), fill=(210, 210, 210), width=2)
    draw.line((40, H // 2, W - 40, H // 2), fill=(210, 210, 210), width=2)

    boxes = {
        "front": (40, 145, W // 2 - 20, H // 2 - 10),
        "left": (W // 2 + 20, 145, W - 40, H // 2 - 10),
        "top": (40, H // 2 + 10, W // 2 - 20, H - 60),
        "iso": (W // 2 + 20, H // 2 + 10, W - 40, H - 60),
    }

    views = {
        # looking along -Y, showing X/Z
        "front": render_view(
            mesh,
            [(0, -1, 0), (0, 0, 0), (0, 0, 1)],
            obj_color
        ),

        # looking along -X, showing Y/Z
        "left": render_view(
            mesh,
            [(-1, 0, 0), (0, 0, 0), (0, 0, 1)],
            obj_color
        ),

        # looking along +Z, showing X/Y
        "top": render_view(
            mesh,
            [(0, 0, 1), (0, 0, 0), (0, 1, 0)],
            obj_color
        ),

        # z-up isometric
        "iso": render_view(
            mesh,
            [(1.8, -2.1, 1.4), (0, 0, 0), (0, 0, 1)],
            obj_color
        ),
    }

    img_boxes = {}
    obj_boxes = {}

    img_boxes["front"], obj_boxes["front"] = paste_view(canvas, draw, views["front"], boxes["front"], "Front", view_font)
    img_boxes["left"], obj_boxes["left"] = paste_view(canvas, draw, views["left"], boxes["left"], "Left Side", view_font)
    img_boxes["top"], obj_boxes["top"] = paste_view(canvas, draw, views["top"], boxes["top"], "Top", view_font)
    img_boxes["iso"], obj_boxes["iso"] = paste_view(canvas, draw, views["iso"], boxes["iso"], "Isometric", view_font)

    if args.dimensions:
        dim_gap = 32

        for key, w_label, h_label in [
            ("front", width, height),
            ("left", depth, height),
            ("top", width, depth),
        ]:
            bx1, by1, bx2, by2 = boxes[key]
            ox1, oy1, ox2, oy2 = obj_boxes[key]

            bottom_y = min(oy2 + dim_gap, by2 - 42)
            side_x = min(ox2 + dim_gap, bx2 - 95)

            draw_dimension(
                draw,
                (ox1, bottom_y),
                (ox2, bottom_y),
                f"{w_label:.1f}",
                dim_color,
                dim_font,
                "bottom",
            )

            draw_dimension(
                draw,
                (side_x, oy1),
                (side_x, oy2),
                f"{h_label:.1f}",
                dim_color,
                dim_font,
                "right",
            )

        draw.text((38, H - 38), "All dimensions in mm", font=note_font, fill=(20, 20, 20))

    canvas.save(args.output_png)
    print(f"Saved: {args.output_png}")


if __name__ == "__main__":
    main()