import time
from atexit import register
from time import sleep
from typing import Callable

import cv2
import numpy as np
from cri_lib import CRIController
from PIL import Image


class RobotActions(object):
    def __init__(self, ip: str = "192.168.3.11", device_id: int = 0) -> None:
        self.velocity = 100
        self.move_height = 150
        # connect to camera
        self.device_id = device_id
        self.cap = cv2.VideoCapture(self.device_id)
        if not self.cap.isOpened():
            raise ConnectionError(f"Could not connect to webcam with device_id={device_id}")

        # connect to robot
        self.controller = CRIController()
        self.controller.connect(ip)
        # setup
        self.setup_robot()
        register(self.shutdown)

        self.main_workspace = (190, -250, 400, 250)
        self.serving_workspace = (-200, 250, 100, 400)

        self.reset()

    def setup_robot(self) -> None:
        self.controller.set_active_control(True)
        self.controller.enable()
        time.sleep(3)
        self.controller.wait_for_kinematics_ready()
        self.controller.set_override(90.0)

    def get_position(self):
        return (
            self.controller.robot_state.position_robot.X,
            self.controller.robot_state.position_robot.Y,
            self.controller.robot_state.position_robot.Z,
        )

    @property
    def actions(self) -> list[Callable]:
        return [
            self.move_to,
            self.grab_object,
            self.release_object,
            self.clearing_position,
            self.capture_image,
        ]

    def reset(self) -> None:
        self.controller.set_dout(31, False)
        self.controller.set_dout(30, False)
        self.clearing_position()

    def move_cartesian(self, x: float, y: float, z: float) -> bool:
        def is_in_box(x, y, box):
            x1, y1, x2, y2 = box
            return (x1 <= x <= x2) and (y1 <= y <= y2)

        current_pos = self.get_position()[:2]

        if not (is_in_box(x, y, self.main_workspace) or is_in_box(x, y, self.serving_workspace)):
            return False

        current_space = 0 if is_in_box(*current_pos, self.main_workspace) else 1
        target_space = 0 if is_in_box(x, y, self.main_workspace) else 1

        if current_space != target_space:
            # move to transition point
            pos = (200, 350, z, 180, 0, 180, 0, 0, 0)
            self.controller.move_cartesian(*pos, velocity=self.velocity, wait_move_finished=True)

        pos = (x, y, z, 180, 0, 180, 0, 0, 0)
        return self.controller.move_cartesian(*pos, velocity=self.velocity, wait_move_finished=True)

    def move_to(self, x: float, y: float) -> bool:
        """
        Commands the robot to move to a specified (x, y) position in world space.

        Args:
            x (float): The x-coordinate of the target position in world space.
            y (float): The y-coordinate of the target position in world space.

        Returns:
            bool: True if the robot successfully reached the specified position,
            False otherwise.
        """
        return self.move_cartesian(x, y, self.move_height)

    def clearing_position(self) -> bool:
        """Moves the robot to a clearing position.

        This function commands the robot to move to a position that clears the workspace
        or prepares it for other operations.

        Returns:
            bool: True if the robot successfully moved to the clearing position,
            False otherwise.
        """
        return self.move_cartesian(200, 0, self.move_height)

    def grab_object(self) -> bool:
        """Commands the robot to grab the object at it's current position.

        This function instructs the robot to attempt to grasp an object
        placed at it's current position..

        Returns:
            bool: True if the robot successfully grabbed the object, False otherwise.
        """

        pos = self.get_position()

        if not self.move_cartesian(pos[0], pos[1], 65):
            return False

        if not self.controller.set_dout(31, True):
            return False

        sleep(0.5)

        return self.move_cartesian(pos[0], pos[1], self.move_height)

    def release_object(self) -> bool:
        """Commands the robot to release a currently held object.

        This function sends a command to the robot to release the object it is
        currently holding, dropping it at its current position.

        Returns:
            bool: True if the robot successfully released the object, False otherwise.
        """

        pos = self.get_position()

        if not self.move_cartesian(pos[0], pos[1], 100):
            return False

        if not self.controller.set_dout(31, False):
            return False

        if not self.controller.set_dout(30, True):
            return False

        sleep(1.0)

        if not self.controller.set_dout(30, False):
            return False

        return self.move_cartesian(pos[0], pos[1], self.move_height)

    def capture_image(self) -> Image.Image | None:
        """
        Capture an image from the webcam to see your environemt.
        Returns the image as a Pillow Image object.

        Returns:
            PIL.Image.Image | None: The image if capture is successful,
            or None if the image capture failed.
        """

        self.get_position()
        if not self.move_cartesian(200, 0, 350):
            return False

        sleep(1)

        return self.take_image()

    def take_image(self) -> Image.Image | None:
        ret, frame = self.cap.read()
        if not ret:
            return None
        # Convert the OpenCV frame (BGR) to RGB format (Pillow expects RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        gray = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY)

        # Calculate grayscale histogram
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])

        # Calculate cumulative distribution
        accumulator = hist.cumsum()

        # Locate points to clip
        max_value = accumulator[-1]
        clip_value = (max_value / 100.0) / 2.0
        min_gray = np.searchsorted(accumulator, clip_value)
        max_gray = np.searchsorted(accumulator, max_value - clip_value)

        # Stretch histogram
        alpha = 255 / (max_gray - min_gray)
        beta = -min_gray * alpha

        # Apply new alpha and beta to adjust brightness and contrast
        adjusted = cv2.convertScaleAbs(frame_rgb, alpha=alpha, beta=beta)

        # Convert and return the frame to a PIL image
        return Image.fromarray(adjusted)

    def shutdown(self):
        if self.controller.connected:
            self.controller.disable()
            self.controller.close()

    def __del__(self):
        self.shutdown()
