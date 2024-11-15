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

    validation_color = "blue"

    robot = RobotActions()
    _, axes = plt.subplots(3)

    # run capture image because its moving the arm to the correct height
    image = robot.capture_image()

    image_anchors = detect_aruco_positions(image)
    world_anchor = np.asarray(robot.get_position())

    print(image_anchors.keys())

    anchor_ids = sorted(image_anchors.keys())
    # plot anchor image and detected coordinates
    axes[0].imshow(image)
    for i in anchor_ids:
        axes[0].scatter(*image_anchors[i], marker="x")

    # move to point A
    robot.move_cartesian(world_anchor[0] + distance, world_anchor[1], world_anchor[2])
    sleep(1)

    # compute point A coordinates
    image = robot.take_image()
    image_a = detect_aruco_positions(image)
    world_a = np.asarray(robot.get_position())

    print(image_a.keys())

    # plot points A image and detected coordinates
    axes[1].imshow(image)
    for i in image_anchors:
        if i in image_a:
            axes[1].scatter(*image_a[i], marker="x")

    # move to point B
    robot.move_cartesian(world_anchor[0], world_anchor[1] + distance, world_anchor[2])
    sleep(1)

    # compute point B coordinates
    image = robot.take_image()
    image_b = detect_aruco_positions(image)
    world_b = np.asarray(robot.get_position())

    print(image_b.keys())

    # plot points B image and detected coordinates
    axes[2].imshow(image)
    for i in image_anchors:
        if i in image_b:
            axes[2].scatter(*image_b[i], marker="x")

    # show the plots
    plt.show()

    def average_image_vector(image_pos):
        shared_ids = set(list(anchor_ids)) & set(list(image_pos.keys()))
        return sum((image_pos[p] - image_anchors[p]) for p in shared_ids) / len(shared_ids)

    # build world transform
    transform = WorldTransform(
        np.asarray([image.width, image.height]),
        # specify anchor points and offset to account for difference between camera
        # and actuator in world space
        next(iter(image_anchors.values())),
        world_anchor[:2] + np.asarray([67, 0]),
        # compute the average transformation vectors in image space
        average_image_vector(image_a),
        average_image_vector(image_b),
        # compute the transformation vectors in world space
        world_a[:2] - world_anchor[:2],
        world_b[:2] - world_anchor[:2],
    )

    # save the world transform
    transform.save("./data/world_state.json")

    image = robot.capture_image()
    image.show()

    for target in detect_aruco_positions(image).values():
        print("Moving to", target)

        # transform the validation position to world coordinates
        pos = transform.transform_pixel_to_world_coords(*target)

        # move to validation coordinates
        robot.move_cartesian(*pos, 65)

        sleep(2)

    robot.clearing_position()
