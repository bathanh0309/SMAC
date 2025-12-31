"""
Detection System Module
Person detection using YOLO11 + Flask streaming + Gate Control
"""
import cv2
import time
import os
import sys
from datetime import datetime
from flask import Flask, Response, jsonify
from flask_cors import CORS
import threading
import logging

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ultralytics import YOLO
from gate_controller import gate_controller
from telegram_helper import telegram_bot
from database import db


class PersonDetectionSystem:
    """Main detection system with webcam, YOLO, Flask streaming, and gate control"""
    
    def __init__(self):
        """Initialize the detection system"""
        print("[INIT] Dang khoi tao he thong phat hien nguoi...")
        
        # Model path configuration
        self.MODEL_PATH = self._find_model()
        
        # Load YOLO model
        print(f"[INIT] Dang load model: {self.MODEL_PATH}")
        self.model = YOLO(self.MODEL_PATH)
        print(f"[INIT] Da load model YOLO11n")
        
        # Detection configuration
        self.CONFIDENCE_THRESHOLD = 0.7  # Confidence >= 0.7 to light up
        self.PERSON_CLASS_ID = 0  # Class 0 = person in COCO
        self.SAVE_DIR = os.path.join(os.path.dirname(__file__), '..', 'database', 'data_images')
        
        # Create save directory if not exists
        if not os.path.exists(self.SAVE_DIR):
            os.makedirs(self.SAVE_DIR)
            print(f"[INIT] Đã tạo thư mục: {self.SAVE_DIR}")
        
        # Frame state
        self.frame = None
        self.frame_lock = threading.Lock()
        self.running = False
        
        # Detection state
        self.last_save_time = 0
        self.SAVE_INTERVAL = 10  # Save image every 10 seconds when person detected
        self.gate_opened_notified = False  # Track if we've sent Telegram for this OPEN
        
        # Realtime detection state for API
        self.current_person_detected = False
        self.current_person_count = 0
        self.current_confidence = 0.0
        
        # Telegram spam prevention
        self.last_telegram_time = 0
        self.TELEGRAM_COOLDOWN = 30  # seconds between telegram messages
        self.telegram_sent_for_detection = False  # Track if telegram sent for current detection
        
        # Flask app with logging disabled and CORS enabled
        self.app = Flask(__name__)
        CORS(self.app)  # Allow cross-origin requests
        self.app.logger.disabled = True
        log = logging.getLogger('werkzeug')
        log.disabled = True
        self._setup_routes()
        
        # Gate controller reference
        self.gate = gate_controller
        
        print("[INIT] He thong da san sang")
    
    def _find_model(self) -> str:
        """Find YOLO model file"""
        # Priority order for model paths
        paths = [
            "AI_model/yolo11n.pt",
            "../AI_model/yolo11n.pt",
            "yolo11n.pt",
            os.path.join(os.path.dirname(__file__), "..", "AI_model", "yolo11n.pt"),
        ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        
        # Default - let ultralytics download it
        print("[WARN] Model khong tim thay, se tai tu dong...")
        return "yolo11n.pt"
    
    def _setup_routes(self):
        """Setup Flask routes - API endpoints only (frontend served by Node.js on port 3000)"""
        
        @self.app.route('/video')
        def video():
            return Response(
                self._generate_frames(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
        
        @self.app.route('/video_feed')
        def video_feed():
            """Alias for /video (compatibility with frontend)"""
            return Response(
                self._generate_frames(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
        
        @self.app.route('/api/status')
        def api_status():
            status = self.gate.get_status()
            return jsonify({
                "gate_state": status["state"],
                "person_detected": self.current_person_detected,
                "person_count": self.current_person_count,
                "confidence": round(self.current_confidence, 2),
                "person_duration": round(status["person_present_duration"], 1),
                "countdown": self._get_countdown_display(),
                "light_on": self.current_person_detected and self.current_confidence >= 0.7
            })
        
        @self.app.route('/api/gate/open', methods=['POST'])
        def api_gate_open():
            self.gate.force_open()
            return jsonify({"status": "success", "gate": "OPEN"})
        
        @self.app.route('/api/gate/close', methods=['POST'])
        def api_gate_close():
            self.gate.force_close()
            return jsonify({"status": "success", "gate": "CLOSED"})
    
    def _get_countdown_display(self):
        """Get countdown remaining time for frontend display"""
        if self.gate.person_present_start is not None:
            elapsed = time.time() - self.gate.person_present_start
            remaining = max(0, self.gate.OPEN_DELAY - elapsed)
            if remaining > 0 and self.gate.state == "CLOSED":
                return round(remaining, 1)
        return 0
    
    def _generate_frames(self):
        """Generate frames for MJPEG streaming"""
        while True:
            with self.frame_lock:
                if self.frame is None:
                    time.sleep(0.03)
                    continue
                frame_copy = self.frame.copy()
            
            ret, buffer = cv2.imencode('.jpg', frame_copy, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            time.sleep(0.033)  # ~30 FPS
    
    def process_frame(self, frame):
        """
        Process a single frame: detect persons and draw bounding boxes
        
        Returns:
            tuple: (processed_frame, person_count, max_confidence)
        """
        results = self.model(frame, verbose=False)
        
        person_count = 0
        max_confidence = 0
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                # Only detect person (class 0)
                if class_id == self.PERSON_CLASS_ID and confidence >= self.CONFIDENCE_THRESHOLD:
                    person_count += 1
                    max_confidence = max(max_confidence, confidence)
                    
                    # Draw bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Draw label
                    label = f"Person {confidence:.2f}"
                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                    cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                                  (x1 + label_size[0], y1), (0, 255, 0), -1)
                    cv2.putText(frame, label, (x1, y1 - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Draw overlay info
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        gate_state = self.gate.state
        
        # Status bar background
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 70), (0, 0, 0), -1)
        
        # Time
        cv2.putText(frame, f"Time: {current_time}", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Detection count
        cv2.putText(frame, f"Detected: {person_count} person(s)", (10, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Gate status
        gate_color = (0, 255, 0) if gate_state == "OPEN" else (0, 0, 255)
        cv2.putText(frame, f"Gate IN: {gate_state}", (frame.shape[1] - 180, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, gate_color, 2)
        
        return frame, person_count, max_confidence
    
    def save_detection(self, frame, person_count, confidence):
        """Save detection image and log to database"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"person_{timestamp}.png"
        filepath = os.path.join(self.SAVE_DIR, filename)
        
        # Save as PNG format
        cv2.imwrite(filepath, frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
        print(f"[SAVE] Đã lưu: {filename}")
        
        # Save to database
        try:
            db.add_detection(person_count, confidence, filepath)
            print(f"[DB] Đã lưu vào database")
        except Exception as e:
            print(f"[DB] Lỗi lưu database: {e}")
        
        return filepath
    
    def send_telegram_alert(self, filepath, person_count, confidence):
        """Send Telegram alert for gate opening"""
        try:
            success = telegram_bot.send_detection_alert(filepath, person_count, confidence)
            if success:
                print("[Telegram] Đã gửi thông báo")
            return success
        except Exception as e:
            print(f"[Telegram] Lỗi: {e}")
            return False
    
    def run_flask(self):
        """Run Flask server in background thread"""
        self.app.run(host='0.0.0.0', port=8000, debug=False, threaded=True, use_reloader=False)
    
    def run(self, show_window=True, camera_index=0):
        """
        Main detection loop
        
        Args:
            show_window: Show OpenCV window (True for local, False for headless)
            camera_index: Camera device index (0 = default webcam)
        """
        print("[START] Bat dau he thong phat hien...")
        
        # Start Flask server
        flask_thread = threading.Thread(target=self.run_flask, daemon=True)
        flask_thread.start()
        print("[Flask] Server dang chay: http://localhost:8000")
        
        # Open camera
        cap = cv2.VideoCapture(camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        if not cap.isOpened():
            print("[ERROR] Khong the mo camera!")
            return
        
        print("[Camera] Da san sang")
        print("=" * 50)
        print("[INFO] Nhan 'q' de dung (trong cua so OpenCV)")
        print("=" * 50)
        
        self.running = True
        
        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    print("[WARN] Khong doc duoc frame, dang thu lai...")
                    time.sleep(0.1)
                    continue
                
                # Process frame
                processed_frame, person_count, confidence = self.process_frame(frame)
                
                # Update realtime detection state for API
                self.current_person_detected = person_count > 0 and confidence >= self.CONFIDENCE_THRESHOLD
                self.current_person_count = person_count if self.current_person_detected else 0
                self.current_confidence = confidence if self.current_person_detected else 0.0
                
                # Update frame for Flask streaming
                with self.frame_lock:
                    self.frame = processed_frame.copy()
                
                # Update gate controller - only when confidence >= threshold
                person_detected = self.current_person_detected
                old_state = self.gate.state
                new_state = self.gate.update(person_detected)
                
                current_time = time.time()
                
                # Handle Telegram: send once when detection starts (with cooldown)
                if person_detected:
                    # Check if we should send telegram (first detection or after cooldown)
                    if not self.telegram_sent_for_detection:
                        if (current_time - self.last_telegram_time) >= self.TELEGRAM_COOLDOWN:
                            filepath = self.save_detection(processed_frame, person_count, confidence)
                            self.send_telegram_alert(filepath, person_count, confidence)
                            self.last_telegram_time = current_time
                            self.telegram_sent_for_detection = True
                else:
                    # Reset telegram flag when no detection
                    self.telegram_sent_for_detection = False
                
                # Handle gate state change logging
                if old_state != new_state:
                    if new_state == "OPEN":
                        self.gate_opened_notified = True
                    else:
                        self.gate_opened_notified = False
                
                # Periodic save when person detected (every SAVE_INTERVAL seconds)
                if person_detected and (current_time - self.last_save_time) >= self.SAVE_INTERVAL:
                    if self.gate.state == "OPEN":
                        self.save_detection(processed_frame, person_count, confidence)
                        self.last_save_time = current_time
                
                # Show OpenCV window
                if show_window:
                    cv2.imshow('Person Detection', processed_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("\n[STOP] Dung boi nguoi dung...")
                        break
        
        except KeyboardInterrupt:
            print("\n[STOP] Dung boi Ctrl+C...")
        
        finally:
            self.running = False
            cap.release()
            cv2.destroyAllWindows()
            self.gate.cleanup()
            print("[DONE] Da dung he thong")


def run_detection_system(show_window=True, camera_index=0):
    """
    Entry point to run the detection system
    
    Args:
        show_window: Show OpenCV preview window
        camera_index: Camera device index
    """
    system = PersonDetectionSystem()
    system.run(show_window=show_window, camera_index=camera_index)


if __name__ == "__main__":
    run_detection_system(show_window=True)
