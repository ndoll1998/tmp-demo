import cv2
from PIL import Image, ImageEnhance


class VisionActions:
    def __init__(self, device_id: int = 0) -> None:
        self.device_id = device_id
        self.cap = cv2.VideoCapture(self.device_id)
        if not self.cap.isOpened():
            raise ConnectionError(f"Could not connect to webcam with device_id={device_id}")

    def capture_image(self) -> Image.Image | None:
        """
        Captures an image from the webcam and returns the image as a Pillow Image object.

        Returns:
            Image.Image | None: The image if capture is successful,
            or None if the image capture failed.
        """
        ret, frame = self.cap.read()
        if not ret:
            return None
        # Convert the OpenCV frame (BGR) to RGB format (Pillow expects RGB)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert the frame to a PIL image
        pil_image = Image.fromarray(frame_rgb)
        # Brighten the image by increasing the brightness
        enhancer = ImageEnhance.Brightness(pil_image)
        bright_image = enhancer.enhance(1.5)  # 1.5 is the factor to brighten, try different values
        # adjust contrast
        contrast_enhancer = ImageEnhance.Contrast(bright_image)
        bright_contrast_image = contrast_enhancer.enhance(1.18)  # Adjust contrast

        return bright_contrast_image
