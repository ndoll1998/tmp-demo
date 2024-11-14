import numpy as np
import yaml


class WorldTransform:
    def __init__(self, config_file: str) -> None:
        with open(config_file) as fp:
            world_state = yaml.safe_load(fp)

        self.robot_a = np.array(
            [world_state["robot_coordinates"]["A"]["x"], world_state["robot_coordinates"]["A"]["y"]]
        )
        self.robot_b = np.array(
            [world_state["robot_coordinates"]["B"]["x"], world_state["robot_coordinates"]["B"]["y"]]
        )
        self.robot_c = np.array(
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

        self.v1_real = self.robot_b - self.robot_a
        self.v2_real = self.robot_c - self.robot_a

        v1 = self.pixel_b - self.pixel_a
        v2 = self.pixel_c - self.pixel_a
        self.A = np.column_stack((v1, v2))

    def transform_pixel_to_world_coords(self, x: int, y: int) -> tuple[float, float]:
        d = np.array([x, y])
        v = d - self.pixel_a
        coefficients, _, _, _ = np.linalg.lstsq(self.A, v, rcond=None)
        alpha, beta = coefficients

        d_real = alpha * self.v1_real + beta * self.v2_real + self.robot_a
        return (d_real[0], d_real[1])
