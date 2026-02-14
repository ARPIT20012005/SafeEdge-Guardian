# IP Camera Streaming Optimization Guide

## Common Issues and Solutions

### Issue 1: Stream Stops After Some Time

**Cause:** Network timeout, buffer overflow, or connection degradation

**Solutions Implemented:**

- ✅ Automatic stream reconnection (up to 5 attempts)
- ✅ Periodic stream refresh every 5 minutes
- ✅ Stream health monitoring
- ✅ Aggressive frame buffer clearing

### Issue 2: Lag and Delayed Frames

**Cause:** Frame buffering in OpenCV or network

**Solutions Implemented:**

- ✅ Buffer size set to 1 (minimal buffering)
- ✅ Periodic buffer clearing (every 10 frames)
- ✅ Target resolution reduced to 480x360
- ✅ FPS limited to 10-30 range

### Issue 3: Memory Leaks

**Cause:** Old frames not being released

**Solutions Implemented:**

- ✅ Explicit frame deletion after use
- ✅ Thread-safe frame copying
- ✅ Proper cleanup on exit

## How the Optimizations Work

### 1. Threaded Frame Capture

```python
ThreadedCamera(src, buffer_size=1, timeout=30,
               target_width=480, target_height=360)
```

- Reads frames in background thread
- Non-blocking access to latest frame
- Automatic frame resizing

### 2. Automatic Reconnection

- Detects stream failures
- Attempts reconnection (max 5 tries)
- 2-second delay between attempts
- Resets counter on successful read

### 3. Stream Refresh

- Every 5 minutes, closes and reopens stream
- Prevents long-term connection degradation
- Clears any accumulated issues

### 4. Health Monitoring

- Tracks time since last successful frame
- Warns if no frames received for 5+ seconds
- Reports stream health every 30 seconds

### 5. Buffer Management

- Buffer size: 1 (minimal lag)
- Periodic buffer clearing (grabs pending frames)
- Prevents frame accumulation

## Recommended IP Camera Settings

### In IP Webcam App (Android):

1. **Video Preferences**
   - Resolution: 640x480 or lower
   - Quality: 50-70%
   - FPS Limit: 10-15
2. **Network**
   - Video Streaming Port: 8080
   - Enable VLC Support: OFF (use MJPEG)
3. **Advanced**
   - MJPEG Format: Recommended
   - Quality: Medium
   - Disable audio if not needed

### For Best Performance:

- Use the same WiFi network (no router hops)
- Close other apps using camera on phone
- Keep phone plugged in (prevents sleep/throttling)
- Use MJPEG stream format: `http://IP:8080/video`

## Troubleshooting Commands

### Test Stream Stability

```powershell
python test_stream_stability.py --source http://192.168.1.100:8080/video --duration 300
```

### Monitor Stream Health

```powershell
python main.py --source http://192.168.1.100:8080/video
```

Watch for messages:

- ✅ Reconnection successful
- 🔄 Refreshing stream connection
- ⚠️ Stream health warning

### Check Network Latency

```powershell
ping 192.168.1.100
```

Should be < 50ms for smooth streaming

## Performance Metrics

### Expected Behavior:

- **FPS:** 8-12 FPS displayed
- **Latency:** 0.5-2 seconds
- **CPU Usage:** 20-40% on modern systems
- **Memory:** Stable (not increasing over time)
- **Reconnections:** < 1 per hour (on stable network)

### Warning Signs:

- ⚠️ FPS drops below 5
- ⚠️ Multiple reconnections per minute
- ⚠️ "Stream stale" messages
- ⚠️ Increasing memory usage

## Advanced Optimization

### For Very Stable Networks:

Increase refresh interval in `utils/camera.py`:

```python
self.refresh_interval = 600  # Refresh every 10 minutes
```

### For Unstable Networks:

Decrease stale threshold:

```python
self.stale_frame_threshold = 3.0  # More aggressive reconnection
```

### For Lower Latency (but less stability):

```python
self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 0)  # Zero buffer
```

## Network Requirements

- **Minimum:** 500 kbps upload (from camera phone)
- **Recommended:** 2+ Mbps
- **Optimal:** 5+ Mbps

Test your network speed between devices:

```powershell
# From PC, test download from camera IP
curl http://192.168.1.100:8080/video --output test.mjpeg --max-time 10
```

## Common Error Messages

### "Stream stale (X.Xs since last frame)"

- **Cause:** No frames received recently
- **Action:** Automatic reconnection will trigger
- **Fix:** Check camera app is running, WiFi stable

### "Max reconnection attempts reached"

- **Cause:** Stream completely unavailable
- **Action:** Program will exit
- **Fix:** Verify camera URL, restart camera app

### "Frame capture error"

- **Cause:** Temporary read failure
- **Action:** Will retry automatically
- **Fix:** Usually self-resolving

### "Reconnecting to stream (attempt X/5)"

- **Cause:** Connection lost
- **Action:** Attempting automatic recovery
- **Fix:** Wait for reconnection, check network

## Tips for 24/7 Operation

1. **Use Wired Connection** - More stable than WiFi
2. **Dedicated Device** - Don't use phone for other tasks
3. **Power Management** - Keep camera device plugged in
4. **Monitor Logs** - Check for recurring issues
5. **Regular Restarts** - Restart system every 24-48 hours
6. **Backup Stream** - Have secondary camera ready

## Testing Your Setup

Run this for 5 minutes to verify stability:

```powershell
python main.py --source http://YOUR_IP:8080/video --skip-frames 5 --target-fps 10
```

Watch for:

- ✅ Steady FPS (variation < 3)
- ✅ No reconnections
- ✅ No memory increase
- ✅ Smooth video display

Good luck! 🚀
