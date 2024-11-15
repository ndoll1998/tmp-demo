import cv2
import numpy as np
from PIL import Image


class ImageActions:
    def detect_objects(self, image: Image.Image) -> list[tuple[float, float, float, float]]:
        """Python function to detects objects in the given image using FRCNN.

        Args:
            image (PIL.Image.Image): The image to analyse.

        Returns:
            (list[tuple[float, float, float, float]]): A list of bounding boxes
            for the detected objects. Each bounding box is of shape (x0, y0, x1, y1)
            with coordinates in pixel-space.
        """

        # convert to numpy array
        image = np.array(image)

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Threshold the image to create a binary mask
        _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

        # Find contours of the objects
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Get bounding boxes
        bounding_boxes = [cv2.boundingRect(contour) for contour in contours]
        bounding_boxes = [
            (min(x, x + w), min(y, y + h), max(x, x + w), max(y, y + h))
            for (x, y, w, h) in bounding_boxes
        ]

        # Set thresholds
        upper_area_threshold = 1000 * 1000  # Define the max area for a bounding box
        lower_area_threshold = 100 * 100

        # Filter boxes by score and area
        filtered_boxes = []

        for box in bounding_boxes:
            # Only include boxes with an area less than the threshold
            if lower_area_threshold <= compute_area(box) <= upper_area_threshold:
                filtered_boxes.append(box)

        iou_threshold = 0.6
        # Remove overlapping boxes with IoU > iou_threshold, keeping only the larger one
        kept_boxes = []

        while len(filtered_boxes) > 0:
            current_box = filtered_boxes.pop(0)

            for i in range(len(kept_boxes)):
                ip = intersection_proportion(current_box, kept_boxes[i])

                if ip > iou_threshold:
                    # Keep the larger box by comparing areas
                    current_area = compute_area(current_box)
                    kept_area = compute_area(kept_boxes[i])

                    if current_area > kept_area:
                        # Replace the kept box with the larger current box
                        kept_boxes[i] = current_box
                    break

            else:
                kept_boxes.append(current_box)

        return kept_boxes

    def crop_image(self, image: Image.Image, bbox: tuple[int, int, int, int]) -> Image.Image:
        """Python function to crop an image to the specified bounding box.

        Args:
            image (Image.Image): The input image to crop.
            bbox (tuple[int, int, int, int]): The bounding box (x1, y1, x2, y2) in pixel-space.

        Returns:
            Image.Image: The cropped image.
        """
        return image.crop(bbox)


def compute_area(box):
    width = box[2] - box[0]
    height = box[3] - box[1]
    return width * height


def intersection_proportion(box1, box2):
    # Function to calculate the IoU between two boxes
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    # Compute intersection area
    intersection_area = max(0, x2 - x1) * max(0, y2 - y1)

    # Compute the area of both bounding boxes
    box1_area = compute_area(box1)
    box2_area = compute_area(box2)

    return intersection_area / min(box1_area, box2_area)


if __name__ == "__main__":
    actions = ImageActions()

    image = Image.open("data/example_image.jpeg")
    bboxes = actions.detect_objects(image)

    for bbox in bboxes:
        print(bbox)
