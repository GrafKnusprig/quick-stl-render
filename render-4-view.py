import trimesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import sys

INPUT_STL = "model.stl"
OUTPUT_PNG = "stl_4view.png"

if len(sys.argv) >= 2:
    INPUT_STL = sys.argv[1]
if len(sys.argv) >= 3:
    OUTPUT_PNG = sys.argv[2]

mesh = trimesh.load(INPUT_STL)

# center and normalize
mesh.apply_translation(-mesh.centroid)
mesh.apply_scale(1.0 / mesh.extents.max())

faces = mesh.vertices[mesh.faces]

views = [
    ("Front", 0, -90),       # top left
    ("Left Side", 0, 180),   # top right
    ("Top", 90, -90),        # bottom left
    ("Isometric", 30, -45),  # bottom right
]

fig = plt.figure(figsize=(19.2, 10.8), dpi=100)
fig.patch.set_facecolor("white")

for i, (title, elev, azim) in enumerate(views, start=1):
    ax = fig.add_subplot(2, 2, i, projection="3d")

    poly = Poly3DCollection(
        faces,
        linewidths=0.08,
        edgecolors=(0.15, 0.15, 0.15),
        alpha=1.0
    )
    poly.set_facecolor((0.75, 0.75, 0.75))
    ax.add_collection3d(poly)

    # fixed normalized bounds, so model fits every view
    padding = 0.08
    limit = 0.5 + padding

    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)
    ax.set_zlim(-limit, limit)

    ax.view_init(elev=elev, azim=azim)
    ax.set_box_aspect([1, 1, 1])
    ax.set_axis_off()
    ax.set_title(title, fontsize=16, pad=8)

plt.subplots_adjust(left=0, right=1, top=0.96, bottom=0, wspace=0, hspace=0.05)
plt.savefig(OUTPUT_PNG, dpi=100, facecolor="white")
plt.close()

print(f"Saved: {OUTPUT_PNG}")