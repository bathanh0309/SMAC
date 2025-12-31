"""
Detection System Module
Hệ thống phát hiện người sử dụng YOLO11 + Flask + Telegram
"""
import cv2
import time
import os
from datetime import datetime
from ultralytics import YOLO
from flask import Flask, Response
import threading
from telegram_helper import telegram_bot
from database import db


class PersonDetectionSystem:
    def __init__(self):
        """Khởi tạo hệ thống"""
        print("🔄 Đang khởi tạo hệ thống phát hiện...")
        
        # Load YOLO model
        print("🔄 Đang load model Ba Thanh...")
        # Đường dẫn model train xong
        custom_model_path = r"runs\detect\bathanh_model\weights\best.pt"
        
        if os.path.exists(custom_model_path):
            self.model = YOLO(custom_model_path)
            print(f"✅ Đã load model: {custom_model_path}")
            self.is_custom_model = True
        elif os.path.exists("bathanh.pt"):
             self.model = YOLO("bathanh.pt")
             print("✅ Đã load bathanh.pt")
             self.is_custom_model = True
        else:
            self.model = YOLO('yolo11n.pt')
            print("⚠️ Không tìm thấy model custom, dùng tạm yolo11n.pt")
            self.is_custom_model = False
        
        # Cấu hình
        self.CONFIDENCE_THRESHOLD = 0.5
        self.PERSON_CLASS_ID = 0  # Class ID của 'person' trong COCO
        self.RESET_TIME = 5  # Thời gian reset (giây)
        self.SAVE_DIR = "data_images"
        
        # Tạo thư mục lưu ảnh
        if not os.path.exists(self.SAVE_DIR):
            os.makedirs(self.SAVE_DIR)
            print(f"✅ Đã tạo thư mục: {self.SAVE_DIR}")
        
        # Biến trạng thái
        self.person_detected = False
        self.last_detection_time = 0
        self.frame = None
        self.latest_frame_lock = threading.Lock()
        
        # Flask app
        self.app = Flask(__name__)
        self.setup_flask_routes()

    # ... (setup_flask_routes giữ nguyên) ...

    def process_frame(self, frame):
        """Xử lý frame: detect + draw boxes"""
        results = self.model(frame, verbose=False)
        
        person_count = 0
        max_confidence = 0
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                # Class 0 là person (hoặc Ba Thanh trong custom model)
                if class_id == 0 and confidence >= self.CONFIDENCE_THRESHOLD:
                    person_count += 1
                    max_confidence = max(max_confidence, confidence)
                    
                    # Vẽ bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Vẽ label
                    label_name = "Ba Thanh" if self.is_custom_model else "Person"
                    label = f"{label_name} {confidence:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Vẽ thông tin trên frame
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        cv2.putText(frame, f"Time: {current_time}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        target_name = "Ba Thanh" if self.is_custom_model else "person"
        cv2.putText(frame, f"Detected: {person_count} {target_name}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame, person_count, max_confidence

    # ... (server methods) ...

                if person_count > 0:
                    if not self.person_detected:
                        # Phát hiện lần đầu
                        self.person_detected = True
                        self.last_detection_time = current_time
                        
                        target_name = "BÁ THÀNH" if self.is_custom_model else "NGƯỜI"
                        print(f"🚨 PHÁT HIỆN {target_name}! (Confidence: {confidence:.2f})")
                        self.save_detection_image(processed_frame, person_count, confidence)
                    
                    elif current_time - self.last_detection_time >= self.RESET_TIME:
                        # Đã qua RESET_TIME, lưu lại
                        self.last_detection_time = current_time
                        target_name = "BÁ THÀNH" if self.is_custom_model else "NGƯỜI"
                        print(f"🚨 PHÁT HIỆN {target_name}! (Confidence: {confidence:.2f})")
                        self.save_detection_image(processed_frame, person_count, confidence)
                else:
                    # Reset nếu không còn người
                    if self.person_detected:
                        self.person_detected = False
                        print("✅ Không còn phát hiện")
        
    def setup_flask_routes(self):
        """Thiết lập Flask routes"""
        @self.app.route('/')
        def index():
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>🎥 Person Detection System</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                        margin: 0;
                    }
                    .container {
                        background: white;
                        border-radius: 20px;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                        padding: 30px;
                        text-align: center;
                        max-width: 900px;
                    }
                    h1 {
                        color: #667eea;
                        margin-bottom: 20px;
                    }
                    img {
                        width: 100%;
                        border-radius: 10px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                    }
                    .info {
                        margin-top: 20px;
                        padding: 15px;
                        background: #f0f4ff;
                        border-radius: 10px;
                        color: #333;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎥 Person Detection System</h1>
                    <img src="/video" alt="Live Stream">
                    <div class="info">
                        <p>✅ YOLO11 Real-time Detection</p>
                        <p>📱 Telegram: @bathanh0309_bot</p>
                        <p>🔄 Auto-save images every 5 seconds</p>
                    </div>
                </div>
            </body>
            </html>
            """
        
        @self.app.route('/video')
        def video():
            return Response(
                self.generate_frames(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
    
    def generate_frames(self):
        """Generator để stream frames qua Flask"""
        while True:
            with self.latest_frame_lock:
                if self.frame is None:
                    continue
                frame_copy = self.frame.copy()
            
            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame_copy)
            if ret:
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            time.sleep(0.03)  # ~30 FPS
    
    def save_detection_image(self, frame, num_people, confidence):
        """Lưu ảnh phát hiện với timestamp và lưu vào database"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"person_{timestamp}.jpg"
        filepath = os.path.join(self.SAVE_DIR, filename)
        
        cv2.imwrite(filepath, frame)
        print(f"💾 Đã lưu: {filename}")
        
        # Lưu vào database
        try:
            db.add_detection(num_people, confidence, filepath)
            print(f"💾 Đã lưu vào database")
        except Exception as e:
            print(f"⚠️  Lỗi lưu database: {e}")
        
        # Gửi Telegram
        if telegram_bot.chat_id:
            # Custom message
            target_name = "BÁ THÀNH" if getattr(self, 'is_custom_model', False) else "NGƯỜI"
            msg = f"🚨 PHÁT HIỆN {target_name}! ({confidence:.2f})"
            
            # Gửi ảnh kèm caption custom
            success = telegram_bot.send_detection_alert(filepath, num_people, confidence, custom_msg=msg)
            
            if success:
                print("✅ Đã gửi Telegram")
            else:
                print("⚠️  Không gửi được Telegram")
        
        return filepath
    
    def process_frame(self, frame):
        """Xử lý frame: detect + draw boxes"""
        results = self.model(frame, verbose=False)
        
        person_count = 0
        max_confidence = 0
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                
                if class_id == self.PERSON_CLASS_ID and confidence >= self.CONFIDENCE_THRESHOLD:
                    person_count += 1
                    max_confidence = max(max_confidence, confidence)
                    
                    # Vẽ bounding box
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Vẽ label
                    label = f"Person {confidence:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Vẽ thông tin trên frame
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        cv2.putText(frame, f"Time: {current_time}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Detected: {person_count} person(s)", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame, person_count, max_confidence
    
    def run_flask_server(self):
        """Chạy Flask server trong thread riêng"""
        self.app.run(host='0.0.0.0', port=8000, debug=False, threaded=True, use_reloader=False)
    
    def run_detection(self, show_window=True):
        """Chạy vòng lặp detection chính"""
        print("🚀 Bắt đầu phát hiện...")
        
        # Khởi động Flask server
        flask_thread = threading.Thread(target=self.run_flask_server, daemon=True)
        flask_thread.start()
        print("✅ Flask server đang chạy trên port 8000")
        
        # Mở camera
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 640)  # Width
        self.cap.set(4, 480)  # Height
        
        if not self.cap.isOpened():
            print("❌ Không thể mở camera!")
            return
        
        print("✅ Camera đã sẵn sàng")
        print("="*50)
        print("⚠️  Nhấn 'q' để dừng")
        print("="*50)
        
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("⚠️  Không đọc được frame, đang thử lại...")
                    time.sleep(0.1)
                    continue
                
                # Xử lý frame
                processed_frame, person_count, confidence = self.process_frame(frame)
                
                # Cập nhật frame cho Flask stream
                with self.latest_frame_lock:
                    self.frame = processed_frame.copy()
                
                # Xử lý phát hiện người
                current_time = time.time()
                
                if person_count > 0:
                    if not self.person_detected:
                        # Phát hiện lần đầu
                        self.person_detected = True
                        self.last_detection_time = current_time
                        print(f"🚨 PHÁT HIỆN {person_count} NGƯỜI! (Confidence: {confidence:.2f})")
                        self.save_detection_image(processed_frame, person_count, confidence)
                    
                    elif current_time - self.last_detection_time >= self.RESET_TIME:
                        # Đã qua RESET_TIME, lưu lại
                        self.last_detection_time = current_time
                        print(f"🚨 PHÁT HIỆN {person_count} NGƯỜI! (Confidence: {confidence:.2f})")
                        self.save_detection_image(processed_frame, person_count, confidence)
                else:
                    # Reset nếu không còn người
                    if self.person_detected:
                        self.person_detected = False
                        print("✅ Không còn phát hiện người")
                
                # Hiển thị cửa sổ OpenCV
                if show_window:
                    cv2.imshow('Person Detection', processed_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("\n🛑 Dừng hệ thống...")
                        break
                
        except KeyboardInterrupt:
            print("\n🛑 Dừng bởi người dùng...")
        
        finally:
            self.cap.release()
            cv2.destroyAllWindows()
            print("✅ Đã dừng hệ thống")


def run_detection_system(show_window=True):
    """
    Hàm chính để chạy hệ thống phát hiện
    
    Args:
        show_window (bool): Hiển thị cửa sổ OpenCV hay không
    """
    system = PersonDetectionSystem()
    system.run_detection(show_window=show_window)


if __name__ == "__main__":
    run_detection_system(show_window=True)
