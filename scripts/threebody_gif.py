import argparse
from collections import deque
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.colors as mcolors
from PIL import Image

def accel(x, m, G=1.0, eps=1e-3):
    # x: (N,2)
    N = x.shape[0]
    a = np.zeros_like(x)
    for i in range(N):
        for j in range(i + 1, N):
            r = x[j] - x[i]
            d2 = np.dot(r, r) + eps**2
            inv_d3 = 1.0 / (d2 * np.sqrt(d2))
            f = G * r * inv_d3
            a[i] += m[j] * f
            a[j] -= m[i] * f
    return a

def leapfrog(x, v, m, dt, steps):
    a = accel(x, m)
    for _ in range(steps):
        v += 0.5 * dt * a
        x += dt * v
        a = accel(x, m)
        v += 0.5 * dt * a
        yield x.copy()

def render_gif(out_path: str, frames=180, dt=0.008, substeps=10, trail=10, dpi=110):
    # Figure-eight initial conditions (equal masses)
    m = np.array([1.0, 1.0, 1.0])

    x = np.array([
        [ 0.97000436, -0.24308753],
        [-0.97000436,  0.24308753],
        [ 0.0,         0.0       ],
    ], dtype=float)

    v = np.array([
        [ 0.466203685,  0.43236573 ],
        [ 0.466203685,  0.43236573 ],
        [-0.93240737,  -0.86473146 ],
    ], dtype=float)

    # Keep a short trail for each body
    trails = [deque(maxlen=trail) for _ in range(3)]
    imgs = []

    # fixed plot limits (looks clean)
    lim = 1.6

    sim = leapfrog(x, v, m, dt=dt, steps=frames * substeps)

    for k, state in enumerate(sim):
        # sample every 'substeps'
        if k % substeps != 0:
            continue

        for i in range(3):
            trails[i].append(state[i].copy())

        fig = plt.figure(figsize=(7.2, 3.2), dpi=dpi)
        ax = fig.add_subplot(111)
        ax.set_facecolor("#0d1117")
        fig.patch.set_facecolor("#0d1117")

        # draw trails + bodies
        for i in range(3):
            t = np.array(trails[i])
            if len(t) > 1:
                ax.plot(t[:, 0], t[:, 1], linewidth=0.2, alpha=0.95)
            ax.scatter(state[i, 0], state[i, 1], s=36)

        ax.set_xlim(-lim, lim)
        ax.set_ylim(-0.95, 0.95)
        ax.axis("off")

        fig.canvas.draw()

        buf = np.asarray(fig.canvas.buffer_rgba())      # shape: (h, w, 4)
        img = buf[..., :3].copy()                       # RGB (h, w, 3)

        imgs.append(Image.fromarray(img))
        plt.close(fig)

    # Save GIF
    imgs[0].save(
        out_path,
        save_all=True,
        append_images=imgs[1:],
        duration=45,
        loop=0,
        optimize=True,
    )

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="assets/threebody.gif")
    ap.add_argument("--frames", type=int, default=180)
    args = ap.parse_args()
    render_gif(args.out, frames=args.frames)
    print(f"Saved: {args.out}")