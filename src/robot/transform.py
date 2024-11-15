from __future__ import annotations

import json

import numpy as np
from numpy.typing import NDArray


class WorldTransform:
    def __init__(
        self,
        image_resolution: NDArray,
        image_anchor: NDArray,
        world_anchor: NDArray,
        image_v1: NDArray,
        image_v2: NDArray,
        world_v1: NDArray,
        world_v2: NDArray,
    ) -> None:
        # image resolution
        self.resolution = image_resolution
        # anchor points
        self.image_anchor = image_anchor
        self.world_anchor = world_anchor
        # transformation matrices
        self.image_transform = np.column_stack((image_v1, image_v2))
        self.world_transform = np.column_stack((world_v1, world_v2))

    def save(self, file_path: str) -> None:
        state = {
            "image_resolution": self.resolution.tolist(),
            "image_anchor": self.image_anchor.tolist(),
            "world_anchor": self.world_anchor.tolist(),
            "image_transform": self.image_transform.tolist(),
            "world_transform": self.world_transform.tolist(),
        }

        with open(file_path, "w+") as fp:
            fp.write(json.dumps(state, indent=2))

    @staticmethod
    def load(file_path: str) -> WorldTransform:
        with open(file_path, "r") as f:
            state = json.loads(f.read())

        return WorldTransform(
            image_resolution=np.asarray(state["image_resolution"]),
            image_anchor=np.asarray(state["image_anchor"]),
            world_anchor=np.asarray(state["world_anchor"]),
            image_v1=np.asarray(state["image_transform"][0]),
            image_v2=np.asarray(state["image_transform"][1]),
            world_v1=np.asarray(state["world_transform"][0]),
            world_v2=np.asarray(state["world_transform"][1]),
        )

    def transform_pixel_to_world_coords(self, x: int, y: int) -> tuple[float, float]:
        """Transform pixel coordinates to world coordinates.

        Args:
            x (int): The x-coordinate in pixel space.
            y (int): The y-coordinate in pixel space.
        Returns:
            tuple[float, float]: The corresponding point (x, y) in world space.
        """

        # transform pixel coordinate relative to camera center
        target = np.asarray([x, y])
        target = self.resolution / 2 + (self.image_anchor - target)

        v = target - self.image_anchor

        coefficients, _, _, _ = np.linalg.lstsq(self.image_transform, v, rcond=None)
        alpha, beta = coefficients

        target_world = (
            alpha * self.world_transform[:, 0]
            + beta * self.world_transform[:, 1]
            + self.world_anchor
        )

        return target_world[0], target_world[1]
