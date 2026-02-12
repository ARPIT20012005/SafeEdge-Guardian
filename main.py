import argparse
import sys
import cv2
import time

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
		default="http://172.18.132.254:8080",
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


def draw_person(frame, bbox, role, prob, color, extra_note=None):
	x1, y1, x2, y2 = bbox
	cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
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
	cap = ThreadedCamera(src, buffer_size=1, timeout=5, 
	                     target_width=res_width, target_height=res_height).start()
	
	# Give the thread time to start and grab first frame
	time.sleep(2)
	
	if not cap.isOpened():
		print("Failed to open stream")
		sys.exit(1)

	print("Stream opened successfully - using threaded capture for stable FPS")
	print(f"Processing detection every {args.skip_frames} frames")

	detector = YOLOPersonDetector(conf_thresh=args.confidence)
	extractor = FeatureExtractor()
	classifier = RoleClassifier()
	supervisor = SupervisionChecker()
	logger = DatasetLogger() if args.log_dataset else None
	firebase = FirebaseUploader()
	
	# Track status changes and frame counter
	prev_status = None
	frame_counter = 0
	upload_interval = 30  # Upload every 30 frames
	
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
	
	# Cache last detection results
	last_persons = []
	last_children = []
	last_adults = []
	last_global_status = "safe"

	# Get first frame to determine dimensions
	danger_zone = None

	print("PHASE 7: ADULT SUPERVISION ACTIVE")
	print("Firebase Integration: Enabled")
	print("Press 'q' to quit")

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
				print("Stream lost - no frames available")
				break
		else:
			# Got a valid frame
			last_valid_frame = frame.copy()
			frame_timeout_counter = 0

		# Skip invalid frames
		if frame is None or frame.size == 0:
			continue

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
			else:
				children.append((p["id"], (cx, cy)))
				in_zone = danger_zone.is_inside(cx, cy)
				note = "IN-ZONE" if in_zone else None
				color = (255, 215, 0) if in_zone else (0, 255, 0)
				draw_person(frame, bbox, role, prob, color, note)

		# Evaluate supervision relative to children
		global_status = "safe"
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
				else:
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
			firebase.update_status(global_status)
			prev_status = global_status
			frame_counter = 0

		# Show global status banner
		if global_status == "safe":
			banner_color = (0, 200, 0)
		elif global_status == "warning":
			banner_color = (0, 255, 255)
		else:
			banner_color = (0, 0, 255)
		
		cv2.rectangle(frame, (0, 0), (w, 40), (0, 0, 0), -1)
		cv2.putText(
			frame,
			global_status.upper(),
			(10, 28),
			cv2.FONT_HERSHEY_SIMPLEX,
			0.9,
			banner_color,
			2,
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
	if not args.no_display:
		cv2.destroyAllWindows()


if __name__ == "__main__":
	main()
