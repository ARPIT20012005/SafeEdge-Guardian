import argparse
import sys
import cv2
import time
from collections import defaultdict

# Platform-specific audio support
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

from detectors.yolo_person_detector import YOLOPersonDetector
from features.feature_extractor import FeatureExtractor
from classifiers.role_classifier import RoleClassifier
from logic.danger_zone import DangerZone
from logic.supervision import SupervisionChecker
from utils.dataset_logger import DatasetLogger
from utils.firebase_uploader import FirebaseUploader
from utils.camera import ThreadedCamera


def parse_args():
	parser = argparse.ArgumentParser(
		description="SafeEdge Guardian – Real-time child/adult supervision"
	)
	parser.add_argument(
		"--source",
		type=str,
		default="0",
		help="Video source: camera index (e.g., 0), video path, or streaming URL",
	)
	parser.add_argument(
		"--no-display",
		action="store_true",
		help="Disable window display (headless mode)",
	)
	parser.add_argument(
		"--log-dataset",
		action="store_true",
		help="Append predicted samples to data/features/pose_features.csv",
	)
	parser.add_argument(
		"--confidence",
		type=float,
		default=0.4,
		help="YOLO confidence threshold (default: 0.4)",
	)
	parser.add_argument(
		"--skip-frames",
		type=int,
		default=5,
		help="Process detection every N frames for better FPS (default: 5)",
	)
	parser.add_argument(
		"--target-fps",
		type=int,
		default=10,
		help="Target display FPS for stable playback (default: 10)",
	)
	parser.add_argument(
		"--resolution",
		type=str,
		default="480x360",
		help="Video resolution WxH (default: 480x360 for stability)",
	)
	return parser.parse_args()


def center_of_bbox(bbox):
	x1, y1, x2, y2 = bbox
	return int((x1 + x2) / 2), int((y1 + y2) / 2)


def draw_person(frame, bbox, role, prob, color, extra_note=None, flash=False):
	x1, y1, x2, y2 = bbox
	thickness = 4 if flash else 2
	cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
	label = f"{role} {prob:.2f}"
	if extra_note:
		label = f"{label} | {extra_note}"
	cv2.putText(
		frame,
		label,
		(x1, max(20, y1 - 10)),
		cv2.FONT_HERSHEY_SIMPLEX,
		0.6,
		color,
		2,
	)


def trigger_alert(alert_type="danger"):
	"""Trigger audio alert (Windows only)"""
	if not HAS_WINSOUND:
		return  # Silent on non-Windows platforms (Raspberry Pi, etc.)
	
	try:
		if alert_type == "danger":
			# High-pitched beep for danger (frequency, duration in ms)
			winsound.Beep(2000, 300)
		elif alert_type == "warning":
			# Medium-pitched beep for warning
			winsound.Beep(1000, 200)
	except Exception as e:
		pass  # Silent fail if audio not available


def main():
	args = parse_args()

	# Resolve capture source (camera index vs path)
	src = args.source
	if src.isdigit():
		src = int(src)

	# Parse resolution
	try:
		res_width, res_height = map(int, args.resolution.split('x'))
	except:
		res_width, res_height = 480, 360
		print(f"Invalid resolution format, using default: {res_width}x{res_height}")

	print(f"Connecting to video source: {src}")
	print(f"Target resolution: {res_width}x{res_height}")
	print(f"Target FPS: {args.target_fps}")
	
	# Use longer timeout for network streams
	timeout = 30 if isinstance(src, str) and src.startswith('http') else 10
	print(f"Using timeout: {timeout} seconds")
	
	cap = ThreadedCamera(src, buffer_size=1, timeout=timeout, 
	                     target_width=res_width, target_height=res_height).start()
	
	# Give the thread time to start and grab first frame
	print("Waiting for camera to initialize...")
	time.sleep(3)
	
	if not cap.isOpened():
		print("❌ ERROR: Failed to open video stream!")
		print(f"   Source: {src}")
		if isinstance(src, str) and src.startswith('http'):
			print("   Troubleshooting tips for IP camera:")
			print("   1. Check if the IP address is correct and reachable")
			print("   2. Verify the camera app is running (e.g., IP Webcam)")
			print("   3. Try accessing the stream URL in a web browser first")
			print(f"   4. Try: {src}/video")
		else:
			print("   Troubleshooting tips for local camera:")
			print("   1. Check if camera is connected and not in use by another program")
			print("   2. Try running: python test_camera_simple.py")
			print("   3. Check camera permissions in Windows Settings")
		sys.exit(1)
	
	print("✅ Camera connected successfully!")

	print("✅ Camera connected successfully!")
	print("Stream opened successfully - using threaded capture for stable FPS")
	print(f"Processing detection every {args.skip_frames} frames")

	print("\n🔄 Loading AI models...")
	detector = YOLOPersonDetector(conf_thresh=args.confidence)
	extractor = FeatureExtractor()
	classifier = RoleClassifier()
	supervisor = SupervisionChecker()
	logger = DatasetLogger() if args.log_dataset else None
	firebase = FirebaseUploader()
	print("✅ All models loaded!")
	
	# Track status changes and frame counter
	prev_status = None
	frame_counter = 0
	upload_interval = 30  # Upload every 30 frames
	
	# Child tracking for line crossing detection
	child_zone_status = defaultdict(lambda: False)  # Track if child was in zone
	alert_cooldown = {}  # Track last alert time per child
	ALERT_COOLDOWN_SECONDS = 3  # Minimum seconds between alerts for same child
	
	# Performance optimization: skip frames for detection
	process_every_n_frames = args.skip_frames  # Process detection every Nth frame
	frame_skip_counter = 0
	
	# FPS tracking and frame timing
	fps_start_time = time.time()
	fps_frame_count = 0
	fps_display = 0
	frame_time = 1.0 / args.target_fps  # Target time per frame
	last_frame_time = time.time()
	
	# Frame timeout tracking
	last_valid_frame = None
	frame_timeout_counter = 0
	
	# Stream health monitoring
	last_health_check = time.time()
	health_check_interval = 30  # Check stream health every 30 seconds
	
	# Cache last detection results
	last_persons = []
	last_children = []
	last_adults = []
	last_global_status = "safe"

	# Get first frame to determine dimensions
	danger_zone = None

	print("\n🚀 Starting SafeEdge Guardian surveillance...")
	print("PHASE 7: ADULT SUPERVISION ACTIVE")
	print("Firebase Integration: Enabled")
	if not args.no_display:
		print("📹 Video window will open shortly - Press 'q' to quit")
	else:
		print("Running in headless mode (no display)")
	print("-" * 50)

	frame_received = False
	while True:
		# Maintain consistent frame timing
		current_time = time.time()
		elapsed = current_time - last_frame_time
		
		# Skip if too soon (enforce target FPS)
		if elapsed < frame_time:
			time.sleep(frame_time - elapsed)
			current_time = time.time()
		
		last_frame_time = current_time
		
		ret, frame = cap.read()
		if not ret or frame is None:
			# Use last valid frame to maintain display
			frame_timeout_counter += 1
			if last_valid_frame is not None and frame_timeout_counter < 100:
				# Reuse last frame for up to 10 seconds
				frame = last_valid_frame.copy()
			else:
				if not frame_received:
					print("❌ ERROR: No frames received from camera!")
					print("   The stream may be unavailable or the wrong URL/device.")
				else:
					print("Stream lost - no frames available")
				break
		else:
			# Got a valid frame
			if not frame_received:
				print("✅ First frame received! Processing...")
				frame_received = True
			last_valid_frame = frame.copy()
			frame_timeout_counter = 0

		# Skip invalid frames
		if frame is None or frame.size == 0:
			continue
		
		# Periodic stream health check
		current_time_check = time.time()
		if current_time_check - last_health_check > health_check_interval:
			health = cap.get_stream_health()
			if not health["is_healthy"]:
				print(f"⚠️ Stream health warning: {health['seconds_since_frame']:.1f}s since last frame")
			last_health_check = current_time_check

		# Initialize danger zone on first frame
		h, w = frame.shape[:2]
		if danger_zone is None:
			danger_zone = DangerZone(w, h)

		# Draw danger zone area
		zx1, zy1, zx2, zy2 = danger_zone.get_zone()
		cv2.rectangle(frame, (zx1, zy1), (zx2, zy2), (0, 0, 255), 3)
		cv2.putText(
			frame,
			"DANGER ZONE",
			(zx1 + 5, 30),
			cv2.FONT_HERSHEY_SIMPLEX,
			0.8,
			(0, 0, 255),
			2,
		)

		# Process detection only every Nth frame for better performance
		frame_skip_counter += 1
		if frame_skip_counter >= process_every_n_frames:
			frame_skip_counter = 0
			try:
				persons = detector.detect(frame)
				last_persons = persons
			except Exception as e:
				print(f"Detection error: {e}")
				persons = last_persons
		else:
			# Reuse last detection results
			persons = last_persons

		children = []  # list of tuples (id, center)
		adults = []  # list of tuples (id, center)

		# Per-person processing
		for p in persons:
			bbox = p["bbox"]
			kps = p.get("keypoints", [])
			if not kps or len(kps) < 13:
				# Not enough keypoints for our feature set
				continue

			feats = extractor.extract(kps)
			role, prob = classifier.classify(feats)

			cx, cy = center_of_bbox(bbox)

			# Log predicted sample if requested
			if logger is not None:
				logger.log(p["id"], feats, role)

			# Who is where
			if role == "ADULT":
				adults.append((p["id"], (cx, cy)))
				draw_person(frame, bbox, role, prob, (0, 165, 255))
			else:  # CHILD
				children.append((p["id"], (cx, cy)))
				in_zone = danger_zone.is_inside(cx, cy)
				
				# Detect line crossing (child entering danger zone)
				child_id = p["id"]
				was_in_zone = child_zone_status[child_id]
				
				# Check if this is a new crossing event
				if in_zone and not was_in_zone:
					# Child just crossed INTO danger zone!
					current_time = time.time()
					last_alert_time = alert_cooldown.get(child_id, 0)
					
					if current_time - last_alert_time > ALERT_COOLDOWN_SECONDS:
						print(f"⚠️ ALERT: Child ID {child_id} crossed into DANGER ZONE!")
						trigger_alert("danger")
						firebase.send_alert(child_id, "danger_zone_entry", current_time)
						alert_cooldown[child_id] = current_time
				
				# Update tracking status
				child_zone_status[child_id] = in_zone
				
				note = "⚠️ DANGER" if in_zone else None
				color = (0, 0, 255) if in_zone else (0, 255, 0)  # Red if in zone
				flash = in_zone  # Flash border if in danger zone
				draw_person(frame, bbox, role, prob, color, note, flash)

		# Evaluate supervision relative to children
		global_status = "safe"
		children_in_danger = []
		
		for cid, cpos in children:
			in_zone = danger_zone.is_inside(*cpos)
			if not in_zone:
				continue

			# Find nearest adult
			nearest_adult = None
			nearest_dist = float("inf")
			for aid, apos in adults:
				dx = apos[0] - cpos[0]
				dy = apos[1] - cpos[1]
				d2 = dx * dx + dy * dy
				if d2 < nearest_dist:
					nearest_dist = d2
					nearest_adult = (aid, apos)

			attentive = False
			if nearest_adult is not None:
				aid, apos = nearest_adult
				attentive = supervisor.is_attentive(aid, apos, cpos)

			if not attentive:
				if nearest_adult is None:
					global_status = "danger"
					children_in_danger.append(cid)
				else:
					if global_status != "danger":  # Only set warning if not already danger
						global_status = "warning"
				# Break early if danger detected
				if global_status == "danger":
					break
			# If attentive, child is supervised - keep status safe unless already escalated
	
		# Cache status for next frames
		last_global_status = global_status
		last_children = children
		last_adults = adults
	
		# Calculate and display FPS
		fps_frame_count += 1
		if fps_frame_count >= 30:
			fps_end_time = time.time()
			fps_display = fps_frame_count / (fps_end_time - fps_start_time)
			fps_start_time = fps_end_time
			fps_frame_count = 0

		# Upload to Firebase on status change or every N frames
		frame_counter += 1
		if global_status != prev_status or frame_counter >= upload_interval:
			# Send detailed status with child count and danger info
			status_data = {
				"status": global_status,
				"timestamp": time.time(),
				"children_count": len(children),
				"adults_count": len(adults),
				"children_in_danger": len(children_in_danger)
			}
			firebase.update_status(global_status, status_data)
			prev_status = global_status
			frame_counter = 0

		# Show global status banner with flashing effect for danger
		if global_status == "safe":
			banner_color = (0, 200, 0)
			status_text = "✓ SAFE"
		elif global_status == "warning":
			banner_color = (0, 255, 255)
			status_text = "⚠ WARNING"
		else:
			# Flashing red banner for danger
			flash_on = (frame_counter % 10) < 5
			banner_color = (0, 0, 255) if flash_on else (0, 0, 150)
			status_text = "🚨 DANGER ALERT"

		cv2.rectangle(frame, (0, 0), (w, 40), (0, 0, 0), -1)
		cv2.putText(
			frame,
			status_text,
			(10, 28),
			cv2.FONT_HERSHEY_SIMPLEX,
			0.9,
			banner_color,
			2,
		)

		# Show child count in zone
		if len(children) > 0:
			child_info = f"Children: {len(children)}"
			if children_in_danger:
				child_info += f" | IN DANGER: {len(children_in_danger)}"
			cv2.putText(
				frame,
				child_info,
				(10, h - 15),
				cv2.FONT_HERSHEY_SIMPLEX,
				0.5,
				(255, 255, 255),
				1,
			)

		# Display FPS
		if fps_display > 0:
			cv2.putText(
				frame,
				f"FPS: {fps_display:.1f}",
				(w - 120, 28),
				cv2.FONT_HERSHEY_SIMPLEX,
				0.6,
				(255, 255, 255),
				2,
			)

		if not args.no_display:
			cv2.imshow("SafeEdge Guardian", frame)
			key = cv2.waitKey(1) & 0xFF
			if key == ord("q"):
				break

	cap.release()
	cv2.destroyAllWindows()
	print("\nSafeEdge Guardian stopped.")


if __name__ == "__main__":
	main()
