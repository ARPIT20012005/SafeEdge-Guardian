import math

class SupervisionChecker:
    def __init__(self):
        # Tunable thresholds
        self.MAX_DISTANCE = 120      # pixels
        self.MIN_MOTION = 3.0        # pixels per frame

        self.prev_positions = {}

    def distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

    def motion_speed(self, pid, pos):
        if pid not in self.prev_positions:
            self.prev_positions[pid] = pos
            return 0.0

        prev = self.prev_positions[pid]
        speed = self.distance(prev, pos)
        self.prev_positions[pid] = pos
        return speed

    def is_attentive(self, adult_id, adult_pos, child_pos):
        dist = self.distance(adult_pos, child_pos)
        speed = self.motion_speed(adult_id, adult_pos)

        if dist < self.MAX_DISTANCE and speed > self.MIN_MOTION:
            return True
        return False
