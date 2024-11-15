from time import sleep

import cv2
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image

from robot.actions import RobotActions
from robot.transform import WorldTransform


def detect_aruco_positions(pil_image: Image.Image):
    # Convert the PIL image to a NumPy array
    cv_image = np.array(pil_image)

    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
    parameters = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(dictionary, parameters)

    # identify markers and compute center coordinates
    corners, ids, _ = detector.detectMarkers(cv_image)
    centers = [c[0].mean(axis=0) for c in corners]

    return dict(zip(ids[:, 0].tolist(), centers, strict=True))


if __name__ == "__main__":
    distance = 50
    brightness = 1.3
    contrast = 1.3

    validation_color = "blue"

    robot = RobotActions()
    _, axes = plt.subplots(3)

    # move to clearing position
    robot.clearing_position()
    sleep(1)

    # compute anchor coordinates
    image = robot.take_image(brightness, contrast)
    image_anchors = detect_aruco_positions(image)
    world_anchor = np.asarray(robot.get_position()[:2])

    print(image_anchors.keys())

    # plot anchor image and detected coordinates
    axes[0].imshow(image)
    for _i, pos in image_anchors.items():
        axes[0].scatter(*pos, marker="x")

    # move to point A
    robot.move_to(world_anchor[0] + distance, world_anchor[1])
    sleep(1)

    # compute point A coordinates
    image = robot.take_image(brightness, contrast)
    image_a = detect_aruco_positions(image)
    world_a = np.asarray(robot.get_position()[:2])

    print(image_a.keys())

    # plot points A image and detected coordinates
    axes[1].imshow(image)
    for _i, pos in image_a.items():
        axes[1].scatter(*pos, marker="x")

    # move to point B
    robot.move_to(world_anchor[0], world_anchor[1] + distance)
    sleep(1)

    # compute point B coordinates
    image = robot.take_image(brightness, contrast)
    image_b = detect_aruco_positions(image)
    world_b = np.asarray(robot.get_position()[:2])

    print(image_b.keys())

    # plot points B image and detected coordinates
    axes[2].imshow(image)
    for _i, pos in image_b.items():
        axes[2].scatter(*pos, marker="x")

    # show the plots
    plt.show()

    # build world transform
    transform = WorldTransform(
        np.asarray([image.width, image.height]),
        # specify anchor points and offset to account for difference between camera
        # and actuator in world space
        next(iter(image_anchors.values())),
        world_anchor + np.asarray([67, 0]),
        # compute the average transformation vectors in image space
        sum((image_a[p] - image_anchors[p]) for p in image_anchors.keys()) / len(image_anchors),
        sum((image_b[p] - image_anchors[p]) for p in image_anchors.keys()) / len(image_anchors),
        # compute the transformation vectors in world space
        world_a - world_anchor,
        world_b - world_anchor,
    )

    # save the world transform
    transform.save("./data/world_state.json")

    # identify position of the validation color
    robot.clearing_position()
    sleep(1)

    image = robot.take_image(brightness, contrast)
    image.show()

    for target in detect_aruco_positions(image).values():
        print("Moving to", target)

        # transform the validation position to world coordinates
        pos = transform.transform_pixel_to_world_coords(*target)

        # move to validation coordinates
        robot.move_cartesian(*pos, 65)

        sleep(2)

    robot.clearing_position()
