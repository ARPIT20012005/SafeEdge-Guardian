import cv2
import threading
import time


class ThreadedCamera:
    """
    Threaded camera capture for stable FPS.
    Continuously reads frames in background thread to prevent blocking.
    """

    def __init__(self, src, buffer_size=1, timeout=10, target_width=480, target_height=360):
        """
        Args:
            src: Video source (int for camera, str for video/stream)
            buffer_size: OpenCV buffer size (1 for minimal lag)
            timeout: Stream timeout in seconds
            target_width: Resize width for lower resolution
            target_height: Resize height for lower resolution
        """
        self.src = src
        self.cap = cv2.VideoCapture(src)
        self.target_width = target_width
        self.target_height = target_height
        
        # Aggressive stream optimization for stability
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, buffer_size)
        self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, timeout * 1000)
        self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, timeout * 1000)
        
        # Request lower resolution from stream source
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)
        self.cap.set(cv2.CAP_PROP_FPS, 10)  # Limit to 10 FPS at source
        
        self.frame = None
        self.grabbed = False
        self.lock = threading.Lock()
        self.stopped = False
        self.last_frame_time = time.time()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5

    def start(self):
        """Start the background frame reading thread."""
        threading.Thread(target=self._update, daemon=True).start()
        return self

    def _update(self):
        """Background thread that continuously reads frames."""
        while not self.stopped:
            if not self.cap.isOpened():
                # Try to reconnect
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    print(f"Reconnecting to stream... (attempt {self.reconnect_attempts + 1})")
                    self.cap.release()
                    time.sleep(2)  # Wait before reconnecting
                    self.cap = cv2.VideoCapture(self.src)
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self.reconnect_attempts += 1
                    continue
                else:
                    print("Max reconnection attempts reached. Stopping.")
                    self.stopped = True
                    break

            grabbed, frame = self.cap.read()
            
            if grabbed and frame is not None and frame.size > 0:
                try:
                    # Resize frame to target resolution for performance
                    if frame.shape[1] != self.target_width or frame.shape[0] != self.target_height:
                        frame = cv2.resize(frame, (self.target_width, self.target_height))
                    
                    with self.lock:
                        self.frame = frame
                        self.grabbed = True
                        self.last_frame_time = time.time()
                    self.reconnect_attempts = 0  # Reset on successful read
                    
                    # Add small delay to prevent overwhelming CPU
                    time.sleep(0.03)  # ~30 FPS max
                except Exception as e:
                    print(f"Frame processing error: {e}")
                    time.sleep(0.05)
            else:
                # Frame read failed, keep using last frame
                time.sleep(0.05)  # Longer delay before retry

    def read(self):
        """Read the latest frame (non-blocking)."""
        with self.lock:
            if self.frame is None or self.frame.size == 0:
                return False, None
            try:
                return self.grabbed, self.frame.copy()
            except:
                return False, None

    def isOpened(self):
        """Check if camera is opened."""
        return self.cap.isOpened()

    def release(self):
        """Stop the thread and release the camera."""
        self.stopped = True
        time.sleep(0.1)  # Allow thread to finish
        self.cap.release()

    def get_fps(self):
        """Get estimated FPS based on frame read timing."""
        current_time = time.time()
        time_diff = current_time - self.last_frame_time
        if time_diff > 0:
            return 1.0 / time_diff
        return 0.0
