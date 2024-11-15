import cv2
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image

from robot.actions import RobotActions
from robot.transform import WorldTransform


def compute_mask(image, color_ranges):
    """
    Computes a binary mask for a given color range.

    Parameters:
        image (numpy.ndarray): Input image in HSV color space.
        color_ranges (list): A list of tuples defining the HSV color ranges.

    Returns:
        numpy.ndarray: Binary mask for the given color range.
    """
    if len(color_ranges) == 2:
        # Single range
        lower, upper = color_ranges
        mask = cv2.inRange(image, np.array(lower), np.array(upper))
    elif len(color_ranges) == 4:
        # Two ranges (e.g., for red)
        lower1, upper1, lower2, upper2 = color_ranges
        mask1 = cv2.inRange(image, np.array(lower1), np.array(upper1))
        mask2 = cv2.inRange(image, np.array(lower2), np.array(upper2))
        mask = cv2.bitwise_or(mask1, mask2)
    else:
        raise ValueError("Color ranges must be either 2 or 4 elements long.")

    # Clean up the mask using morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    return mask


def compute_position_from_mask(mask, min_area=50):
    """
    Computes the centroid of the largest contour in the given mask.

    Parameters:
        mask (numpy.ndarray): Binary mask where the marker is highlighted.
        min_area (int): Minimum area threshold to ignore small blobs.

    Returns:
        tuple: (x, y) coordinates of the centroid if a valid contour is found, None otherwise.
    """
    # Find contours in the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        # Get the largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest_contour) > min_area:
            # Calculate the centroid using moments
            moments = cv2.moments(largest_contour)
            if moments["m00"] != 0:
                cx = int(moments["m10"] / moments["m00"])
                cy = int(moments["m01"] / moments["m00"])
                return np.asarray([cx, cy])

    # Return None if no valid contour is found
    return None


def find_marker_positions(image: Image.Image) -> dict[str, tuple[float, float]]:
    # Define color ranges in HSV
    color_ranges = {
        "red": [
            (0, 120, 70),
            (10, 255, 255),
            (170, 120, 70),
            (180, 255, 255),
        ],  # Red has two ranges (low and high hue)
        "green": [(40, 40, 40), (90, 255, 255)],  # Green range
        "blue": [(100, 150, 0), (140, 255, 255)],  # Blue range
    }

    image = np.array(image)

    # Convert RGB to BGR (OpenCV uses BGR format)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    # Convert the image to HSV color space for better color segmentation
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # compute the pixel coordinates of the markers
    masks = {color: compute_mask(hsv_image, crange) for color, crange in color_ranges.items()}
    pos = {color: compute_position_from_mask(mask, min_area=30) for color, mask in masks.items()}

    return pos


if __name__ == "__main__":
    distance = 70
    brightness = 1.3
    contrast = 1.3

    validation_color = "blue"

    robot = RobotActions()
    _, axes = plt.subplots(3)

    # move to clearing position
    robot.clearing_position()

    # compute anchor coordinates
    image = robot.take_image(brightness, contrast)
    image_anchors = find_marker_positions(image)
    world_anchor = np.asarray(robot.get_position()[:2])

    # plot anchor image and detected coordinates
    axes[0].imshow(image)
    for color, pos in image_anchors.items():
        axes[0].scatter(*pos, marker="x", color=color)

    # move to point A
    robot.move_to(world_anchor[0] + distance, world_anchor[1])

    # compute point A coordinates
    image = robot.take_image(brightness, contrast)
    image_a = find_marker_positions(image)
    world_a = np.asarray(robot.get_position()[:2])

    # plot points A image and detected coordinates
    axes[1].imshow(image)
    for color, pos in image_a.items():
        axes[1].scatter(*pos, marker="x", color=color)

    # move to point B
    robot.move_to(world_anchor[0], world_anchor[1] + distance)

    # compute point B coordinates
    image = robot.take_image(brightness, contrast)
    image_b = find_marker_positions(image)
    world_b = np.asarray(robot.get_position()[:2])

    # plot points B image and detected coordinates
    axes[2].imshow(image)
    for color, pos in image_b.items():
        axes[2].scatter(*pos, marker="x", color=color)

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
    image = robot.take_image(brightness, contrast)
    target = find_marker_positions(image)[validation_color]

    # transform the validation position to world coordinates
    pos = transform.transform_pixel_to_world_coords(*target)

    # move to validation coordinates
    robot.move_cartesian(*pos, 65)

    # show the plots
    plt.show()
