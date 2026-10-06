"""Future differentiable rasterizer boundary.

The placeholder solver is geometry-only. A PyTorch renderer can implement this module later
without changing the HTTP contracts.
"""


def renderer_available() -> bool:
    return False
