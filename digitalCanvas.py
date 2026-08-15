import cv2
import numpy as np

class DigitalCanvas:
    def __init__(self, width=640, height=480):
        # 1. The Persistent Reality
        self.matrix = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 2. The Spatial Anchors (This replaces all your global variables)
        self.px = 0
        self.py = 0
        
        # 3. The Kinematic Anchors
        self.prev_x: float = 0
        self.prev_y: float = 0
        self.prev_scroll_y = None

    def draw_stroke(self, x, y, color=(255, 0, 255), thickness=5):
        """Executes a brush stroke and updates the temporal anchor."""
        if self.px == 0 and self.py == 0:
            self.px, self.py = x, y
            
        cv2.line(self.matrix, (self.px, self.py), (x, y), color, thickness)
        self.px, self.py = x, y

    def erase_stroke(self, x, y, thickness=50):
        """Acts as a localized digital void."""
        if self.px == 0 and self.py == 0:
            self.px, self.py = x, y
            
        cv2.line(self.matrix, (self.px, self.py), (x, y), (0, 0, 0), thickness)
        self.px, self.py = x, y

    def reset_anchors(self):
        """Severs the temporal anchor when the hand leaves the drawing state."""
        self.px = 0
        self.py = 0
        self.prev_scroll_y = None

    def render(self, frame):
        """Fuses the static canvas with the volatile webcam frame."""
        return cv2.bitwise_or(frame, self.matrix)

    
