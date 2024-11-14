from cri_lib import CRIController
from atexit import register
from typing import Callable
from time import sleep

import time
 
class RobotActions(object):
 
    def __init__(self, ip: str = "192.168.3.11") -> None:
        # connect to robot
        self.controller = CRIController()
        self.controller.connect(ip)
        # setup
        self.setup_robot()
        register(self.shutdown)

        self.velocity = 50

    def setup_robot(self) -> None:
        self.controller.set_active_control(True)
        enabled = self.controller.enable()
        time.sleep(3)
        self.controller.wait_for_kinematics_ready()
        self.controller.set_override(90.0)

    @property
    def actions(self) -> list[Callable]:
        return [
            self.move_to,
            self.grab_object,
            self.release_object,
            self.clearing_position,
        ]

    def move_to(self, x: float, y: float) -> bool:
        """
        Commands the robot to move to a specified (x, y) position.

        This function sends a command to the robot to navigate to the given 
        (x, y) coordinates.

        Args:
            x (float): The x-coordinate of the target position.
            y (float): The y-coordinate of the target position.

        Returns:
            bool: True if the robot successfully reached the specified position, 
            False otherwise.
        """
        pos = (x, y, 300, 179, 0, 179, 0, 0, 0)
        return self.controller.move_cartesian(
            *pos, velocity=self.velocity, wait_move_finished=True
        )

    def clearing_position(self) -> bool:
        """Moves the robot to a clearing position.

        This function commands the robot to move to a position that clears the workspace 
        or prepares it for other operations.

        Returns:
            bool: True if the robot successfully moved to the clearing position, 
            False otherwise.
        """
        pos = (-7.1, -18.02, 122.5, 0.0, 75.5, -7.0, 0.0, 0.0, 0.0)
        return self.controller.move_joints(
            *pos, velocity=self.velocity, wait_move_finished=True
        )

    def grab_object(self) -> bool:
        """Commands the robot to grab the object at it's current position.

        This function instructs the robot to attempt to grasp an object 
        placed at it's current position..

        Returns:
            bool: True if the robot successfully grabbed the object, False otherwise.
        """
        return self.controller.set_dout(31,True)


    def release_object(self) -> bool:
        """Commands the robot to release a currently held object.

        This function sends a command to the robot to release the object it is 
        currently holding, dropping it at its current position.

        Returns:
            bool: True if the robot successfully released the object, False otherwise.
        """

        if not self.controller.set_dout(31, False):
            return False

        if not self.controller.set_dout(30, True):
            return False

        sleep(0.2)

        if not self.controller.set_dout(30, False):
            return False

        return True
 
    def shutdown(self):
        if self.controller.connected:
            self.controller.disable()
            self.controller.close()
 
    def __del__(self):
        self.shutdown()

