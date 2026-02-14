"""
Stream Stability Test
Tests IP camera stream for stability, lag, and reconnection behavior
"""
import argparse
import cv2
import time
from utils.camera import ThreadedCamera

def test_stream_stability(source, duration=300, show_video=True):
    """
    Test stream stability for specified duration
    
    Args:
        source: Video source URL
        duration: Test duration in seconds
        show_video: Whether to display video window
    """
    print("🎥 Stream Stability Test")
    print("=" * 60)
    print(f"Source: {source}")
    print(f"Duration: {duration} seconds ({duration/60:.1f} minutes)")
    print("=" * 60)
    
    # Initialize camera
    print("\n📡 Connecting to stream...")
    cap = ThreadedCamera(source, buffer_size=1, timeout=30, 
                        target_width=480, target_height=360).start()
    
    time.sleep(3)  # Wait for initialization
    
    if not cap.isOpened():
        print("❌ Failed to connect to stream!")
        return
    
    print("✅ Connected successfully\n")
    
    # Test metrics
    start_time = time.time()
    end_time = start_time + duration
    
    frame_count = 0
    failed_reads = 0
    fps_samples = []
    last_fps_time = time.time()
    fps_frame_count = 0
    
    health_checks = []
    
    print("⏱️  Starting stability test...")
    print("   Press 'q' to stop early\n")
    
    try:
        while time.time() < end_time:
            current_time = time.time()
            elapsed = current_time - start_time
            remaining = duration - elapsed
            
            # Read frame
            ret, frame = cap.read()
            
            if ret and frame is not None:
                frame_count += 1
                fps_frame_count += 1
                
                # Calculate FPS every second
                if current_time - last_fps_time >= 1.0:
                    fps = fps_frame_count / (current_time - last_fps_time)
                    fps_samples.append(fps)
                    last_fps_time = current_time
                    fps_frame_count = 0
                
                # Get stream health every 10 seconds
                if frame_count % 100 == 0:
                    health = cap.get_stream_health()
                    health_checks.append(health)
                    
                    # Progress update
                    avg_fps = sum(fps_samples[-10:]) / len(fps_samples[-10:]) if fps_samples else 0
                    print(f"[{elapsed:.0f}s / {duration}s] "
                          f"Frames: {frame_count}, "
                          f"FPS: {avg_fps:.1f}, "
                          f"Reconnects: {health['reconnect_attempts']}, "
                          f"Health: {'✅' if health['is_healthy'] else '⚠️'}")
                
                # Display video if requested
                if show_video:
                    # Add metrics overlay
                    cv2.putText(frame, f"Test Time: {elapsed:.0f}s / {duration}s", 
                              (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.putText(frame, f"Frames: {frame_count}", 
                              (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    cv2.putText(frame, f"Failed: {failed_reads}", 
                              (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    cv2.imshow('Stream Stability Test', frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("\n⏹️  Test stopped by user")
                        break
            else:
                failed_reads += 1
                if failed_reads % 10 == 0:
                    print(f"⚠️  Failed reads: {failed_reads}")
            
            # Small delay
            time.sleep(0.03)
    
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    
    finally:
        actual_duration = time.time() - start_time
        cap.release()
        cv2.destroyAllWindows()
        
        # Print results
        print("\n" + "=" * 60)
        print("📊 Test Results")
        print("=" * 60)
        print(f"Duration: {actual_duration:.1f} seconds")
        print(f"Total Frames: {frame_count}")
        print(f"Failed Reads: {failed_reads}")
        print(f"Success Rate: {(frame_count/(frame_count+failed_reads)*100) if frame_count+failed_reads > 0 else 0:.1f}%")
        
        if fps_samples:
            avg_fps = sum(fps_samples) / len(fps_samples)
            min_fps = min(fps_samples)
            max_fps = max(fps_samples)
            print(f"\nFPS Statistics:")
            print(f"  Average: {avg_fps:.1f}")
            print(f"  Min: {min_fps:.1f}")
            print(f"  Max: {max_fps:.1f}")
            print(f"  Stability: {(1 - (max_fps - min_fps) / max_fps) * 100 if max_fps > 0 else 0:.1f}%")
        
        if health_checks:
            unhealthy_count = sum(1 for h in health_checks if not h['is_healthy'])
            max_reconnects = max(h['reconnect_attempts'] for h in health_checks)
            print(f"\nHealth Checks:")
            print(f"  Total Checks: {len(health_checks)}")
            print(f"  Unhealthy: {unhealthy_count}")
            print(f"  Max Reconnect Attempts: {max_reconnects}")
        
        # Verdict
        print("\n" + "=" * 60)
        if failed_reads < frame_count * 0.05 and fps_samples and avg_fps > 8:
            print("✅ VERDICT: Stream is STABLE")
            print("   Ready for production use")
        elif failed_reads < frame_count * 0.15 and fps_samples and avg_fps > 5:
            print("⚠️  VERDICT: Stream is ACCEPTABLE")
            print("   May have occasional issues")
        else:
            print("❌ VERDICT: Stream is UNSTABLE")
            print("   Check network connection and camera settings")
        print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test IP camera stream stability")
    parser.add_argument("--source", type=str, required=True,
                       help="Stream URL (e.g., http://192.168.1.100:8080/video)")
    parser.add_argument("--duration", type=int, default=300,
                       help="Test duration in seconds (default: 300 = 5 minutes)")
    parser.add_argument("--no-display", action="store_true",
                       help="Disable video display")
    
    args = parser.parse_args()
    
    test_stream_stability(args.source, args.duration, not args.no_display)
