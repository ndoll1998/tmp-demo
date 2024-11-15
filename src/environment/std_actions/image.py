import torch
from PIL import Image
from torchvision.models.detection import fasterrcnn_mobilenet_v3_large_fpn as FRCNN  # noqa: N812
from torchvision.transforms import functional as F  # noqa: N812


class ImageActions:
    def __init__(self) -> None:
        self.model = FRCNN(pretrained=True).eval()

    @torch.inference_mode()
    def detect_objects(self, image: Image.Image) -> list[tuple[float, float, float, float]]:
        """Detects objects in the given image using FRCNN.

        Args:
            image (PIL.Image.Image): The image to analyse.

        Returns:
            (list[tuple[float, float, float, float]]): A list of bounding boxes
            for the detected objects. Each bounding box is of shape (x0, y0, x1, y1)
            with coordinates in pixel-space.
        """
        # Preprocess the image (convert to tensor and normalize)
        image_tensor = F.to_tensor(image)  # Convert to tensor
        image_tensor = image_tensor.unsqueeze(0)  # Add a batch dimension (1 image)

        predictions = self.model(image_tensor)

        # Access the prediction data
        boxes = predictions[0]["boxes"]  # Bounding boxes (x1, y1, x2, y2)
        labels = predictions[0]["labels"]  # Predicted labels for each box
        scores = predictions[0]["scores"]  # Confidence scores for each box

        """

        # Set thresholds
        score_threshold = 0.0
        upper_area_threshold = 100000  # Define the max area for a bounding box
        lower_area_threshold = 50000

        # Filter boxes by score and area
        filtered_boxes = []
        filtered_scores = []
        filtered_labels = []

        for box, score, label in zip(boxes, scores, labels):
            if score > score_threshold:
                # Only include boxes with an area less than the threshold
                if lower_area_threshold <= compute_area(box) <= upper_area_threshold:
                    filtered_boxes.append(box)
                    filtered_scores.append(score)
                    filtered_labels.append(label)

        """
        filtered_boxes = boxes.tolist()
        filtered_scores = scores.tolist()
        filtered_labels = labels.tolist()

        iou_threshold = 0.9
        # Remove overlapping boxes with IoU > iou_threshold, keeping only the larger one
        kept_boxes: list[torch.Tensor] = []
        kept_scores = []
        kept_labels = []

        while len(filtered_boxes) > 0:
            current_box = filtered_boxes.pop(0)
            current_score = filtered_scores.pop(0)
            current_label = filtered_labels.pop(0)

            for i in range(len(kept_boxes)):
                ip = intersection_proportion(current_box, kept_boxes[i])

                if ip > iou_threshold:
                    # Keep the larger box by comparing areas
                    current_area = compute_area(current_box)
                    kept_area = compute_area(kept_boxes[i])

                    if current_area > kept_area:
                        # Replace the kept box with the larger current box
                        kept_boxes[i] = current_box
                        kept_scores[i] = current_score
                        kept_labels[i] = current_label
                    break

            else:
                kept_boxes.append(current_box)
                kept_scores.append(current_score)
                kept_labels.append(current_label)

        return kept_boxes
        return [bbox.tolist() for bbox in kept_boxes]

    def crop_image(self, image: Image.Image, bbox: tuple[int, int, int, int]) -> Image.Image:
        """Crops the image to the specified bounding box.

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
