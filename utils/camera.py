import cv2
import threading
import time


class ThreadedCamera:
    """
    Threaded camera capture for stable FPS with automatic reconnection.
    Optimized for long-running IP camera streams.
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
        self.target_width = target_width
        self.target_height = target_height
        self.timeout = timeout
        
        # Stream health monitoring (MUST be set BEFORE _init_capture)
        self.is_stream = isinstance(src, str) and src.startswith('http')
        self.refresh_interval = 300  # Refresh stream every 5 minutes for IP cameras
        self.last_refresh = time.time()
        
        # Initialize capture
        self.cap = self._init_capture()
        
        self.frame = None
        self.grabbed = False
        self.lock = threading.Lock()
        self.stopped = False
        self.last_frame_time = time.time()
        self.last_successful_read = time.time()
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.frame_count = 0
        self.stale_frame_threshold = 5.0  # Seconds before considering stream stale
    
    def _init_capture(self):
        """Initialize video capture with optimal settings."""
        cap = cv2.VideoCapture(self.src)
        
        # Aggressive optimization for network streams
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, self.timeout * 1000)
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, self.timeout * 1000)
        
        # Request lower resolution and FPS from source
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
        cap.set(cv2.CAP_PROP_FPS, 10)
        
        # For IP cameras, use FFMPEG backend if available for better streaming
        if self.is_stream:
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        
        return cap

    def start(self):
        """Start the background frame reading thread."""
        threading.Thread(target=self._update, daemon=True).start()
        return self
    
    def _refresh_stream(self):
        """Refresh the stream connection to prevent long-term degradation."""
        print("🔄 Refreshing stream connection...")
        self.cap.release()
        time.sleep(0.5)
        self.cap = self._init_capture()
        self.last_refresh = time.time()
        self.reconnect_attempts = 0
        print("✅ Stream refreshed")
    
    def _reconnect(self):
        """Attempt to reconnect to the stream."""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            print("❌ Max reconnection attempts reached. Stopping.")
            self.stopped = True
            return False
        
        print(f"🔄 Reconnecting to stream... (attempt {self.reconnect_attempts + 1}/{self.max_reconnect_attempts})")
        self.cap.release()
        time.sleep(2)  # Wait before reconnecting
        self.cap = self._init_capture()
        self.reconnect_attempts += 1
        
        if self.cap.isOpened():
            print("✅ Reconnection successful")
            return True
        return False

    def _update(self):
        """Background thread that continuously reads frames with health monitoring."""
        consecutive_failures = 0
        max_consecutive_failures = 30
        
        while not self.stopped:
            # Periodic stream refresh for IP cameras (prevent long-term degradation)
            if self.is_stream and (time.time() - self.last_refresh) > self.refresh_interval:
                self._refresh_stream()
            
            # Check if stream is opened
            if not self.cap.isOpened():
                if not self._reconnect():
                    break
                continue

            # Try to read frame
            try:
                grabbed, frame = self.cap.read()
            except Exception as e:
                print(f"⚠️ Frame capture error: {e}")
                grabbed = False
                frame = None
            
            if grabbed and frame is not None and frame.size > 0:
                try:
                    # Resize frame to target resolution
                    if frame.shape[1] != self.target_width or frame.shape[0] != self.target_height:
                        frame = cv2.resize(frame, (self.target_width, self.target_height), 
                                         interpolation=cv2.INTER_LINEAR)
                    
                    # Update frame with lock
                    with self.lock:
                        # Free old frame memory
                        if self.frame is not None:
                            del self.frame
                        self.frame = frame
                        self.grabbed = True
                        self.last_frame_time = time.time()
                        self.last_successful_read = time.time()
                        self.frame_count += 1
                    
                    # Reset counters on success
                    self.reconnect_attempts = 0
                    consecutive_failures = 0
                    
                    # Small delay to prevent CPU overload
                    time.sleep(0.03)  # ~30 FPS max
                    
                    # Clear any buffered frames for IP cameras (reduce lag)
                    if self.is_stream and self.frame_count % 10 == 0:
                        # Grab and discard pending frames to clear buffer
                        for _ in range(3):
                            self.cap.grab()
                    
                except Exception as e:
                    print(f"⚠️ Frame processing error: {e}")
                    consecutive_failures += 1
                    time.sleep(0.05)
            else:
                # Frame read failed
                consecutive_failures += 1
                
                # Check for stale stream
                time_since_success = time.time() - self.last_successful_read
                if time_since_success > self.stale_frame_threshold:
                    print(f"⚠️ Stream stale ({time_since_success:.1f}s since last frame)")
                    if not self._reconnect():
                        break
                
                # Too many consecutive failures - try reconnect
                if consecutive_failures >= max_consecutive_failures:
                    print(f"⚠️ Too many frame failures ({consecutive_failures})")
                    consecutive_failures = 0
                    if not self._reconnect():
                        break
                
                time.sleep(0.1)  # Longer delay on failure

    def read(self):
        """Read the latest frame (non-blocking, thread-safe)."""
        with self.lock:
            if self.frame is None or self.frame.size == 0:
                return False, None
            try:
                # Return a copy to prevent external modifications
                return self.grabbed, self.frame.copy()
            except Exception as e:
                print(f"⚠️ Frame read error: {e}")
                return False, None

    def isOpened(self):
        """Check if camera is opened and receiving frames."""
        if not self.cap.isOpened():
            return False
        # Also check if we're receiving recent frames
        time_since_frame = time.time() - self.last_successful_read
        return time_since_frame < self.stale_frame_threshold

    def release(self):
        """Stop the thread and release the camera."""
        print("🛑 Releasing camera...")
        self.stopped = True
        time.sleep(0.2)  # Allow thread to finish
        if self.cap is not None:
            self.cap.release()
        # Clear frame memory
        with self.lock:
            if self.frame is not None:
                del self.frame
                self.frame = None

    def get_fps(self):
        """Get estimated FPS based on frame read timing."""
        current_time = time.time()
        time_diff = current_time - self.last_frame_time
        if time_diff > 0:
            return 1.0 / time_diff
        return 0.0
    
    def get_stream_health(self):
        """Get stream health metrics."""
        time_since_frame = time.time() - self.last_successful_read
        return {
            "is_healthy": time_since_frame < self.stale_frame_threshold,
            "seconds_since_frame": round(time_since_frame, 2),
            "frame_count": self.frame_count,
            "reconnect_attempts": self.reconnect_attempts
        }
