import numpy as np
import yaml


class WorldTransform:
    def __init__(self, config_file: str) -> None:
        with open(config_file) as fp:
            world_state = yaml.safe_load(fp)

        self.real_a = np.array(
            [world_state["robot_coordinates"]["A"]["x"], world_state["robot_coordinates"]["A"]["y"]]
        )
        self.real_b = np.array(
            [world_state["robot_coordinates"]["B"]["x"], world_state["robot_coordinates"]["B"]["y"]]
        )
        self.real_c = np.array(
            [world_state["robot_coordinates"]["C"]["x"], world_state["robot_coordinates"]["C"]["y"]]
        )
        self.pixel_a = np.array(
            [world_state["pixel_coordinates"]["A"]["x"], world_state["pixel_coordinates"]["A"]["y"]]
        )
        self.pixel_b = np.array(
            [world_state["pixel_coordinates"]["B"]["x"], world_state["pixel_coordinates"]["B"]["y"]]
        )
        self.pixel_c = np.array(
            [world_state["pixel_coordinates"]["C"]["x"], world_state["pixel_coordinates"]["C"]["y"]]
        )

        self.v1 = self.pixel_b - self.pixel_a
        self.v2 = self.pixel_c - self.pixel_a
        self.v1_real = self.real_b - self.real_a
        self.v2_real = self.real_c - self.real_a

        self.A = np.column_stack((self.v1, self.v2))
        self.A_real = np.column_stack((self.v1_real, self.v2_real))

    def transform_pixel_to_world_coords(self, x: int, y: int) -> tuple[float, float]:
        """Transform pixel coordinates to world coordinates.

        Args:
            x (int): The x-coordinate in pixel space.
            y (int): The y-coordinate in pixel space.
        Returns:
            tuple[float, float]: The corresponding point (x, y) in world space.
        """
        d = np.array([x, y])
        v = d - self.pixel_a
        coefficients, _, _, _ = np.linalg.lstsq(self.A, v, rcond=None)
        alpha, beta = coefficients

        d_real = alpha * self.v1_real + beta * self.v2_real + self.real_a
        return (d_real[0], d_real[1])

    def transform_world_to_pixel_coords(self, x: float, y: float) -> tuple[int, int]:
        """Transform world coordinates to pixel coordinates.

        Args:
            x (int): The x-coordinate in world space.
            y (int): The y-coordinate in world space.
        Returns:
            tuple[float, float]: The corresponding point (x, y) in pixel space.
        """
        d = np.array([x, y])
        v = d - self.real_a
        coefficients, _, _, _ = np.linalg.lstsq(self.A_real, v, rcond=None)
        alpha, beta = coefficients

        d_real = np.round(alpha * self.v1 + beta * self.v2 + self.pixel_a, decimals=0).astype(int)
        return (d_real[0], d_real[1])
