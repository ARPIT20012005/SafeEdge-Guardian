class DangerZone:
    def __init__(self, frame_width, frame_height):
        self.frame_width = frame_width
        self.frame_height = frame_height

        # Right-side danger strip (last 25% of width - moved left)
        self.x1 = int(frame_width * 0.75)
        self.y1 = 0
        self.x2 = frame_width
        self.y2 = frame_height

    def is_inside(self, x, y):
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def get_zone(self):
        return (self.x1, self.y1, self.x2, self.y2)
