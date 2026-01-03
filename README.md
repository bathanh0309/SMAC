# SMAC - Security Monitoring Access Control

SMAC (Security Monitoring Access Control) là hệ thống giám sát an ninh tự động kiểm soát cổng ra vào dựa trên việc phát hiện người sử dụng trí tuệ nhân tạo (YOLO11)

Đối với dự án SMAC trong **môn Công nghệ Phần mềm**, tôi đề xuất sử dụng:

## 🎯 **Hybrid Approach: Waterfall + Agile Elements**

### Lý do:

| Yếu tố | Giải pháp |
|--------|-----------|
| **Yêu cầu môn học** | Waterfall phases cho documentation |
| **Thực tế phát triển** | Agile iterations cho coding |
| **Team size nhỏ** | Không cần full Scrum ceremonies |
| **Thời gian giới hạn** | Timeboxed phases |

## Mục tiêu
- Tự động hóa việc điều khiển cổng ra vào
- Phát hiện người theo thời gian thực
- Ghi log và cảnh báo kịp thời
- Cung cấp giao diện giám sát web

## Stakeholders
| Vai trò | Mô tả |
|---------|-------|
| **Người quản lý** | Giám sát, điều khiển hệ thống |
| **Người sử dụng** | Đi qua cổng |
| **Quản trị viên hệ thống** | Cấu hình, bảo trì |

https://github.com/user-attachments/assets/0690f03e-9104-4892-8d91-02bf9c63523b


## Cấu trúc

```
SMAC/
├── AI_model/               # YOLO model (yolo11n.pt)
├── backend/                # Node.js server
├── frontend/               # Web dashboard
├── src/                    # Python detection system
│   ├── detection_system.py # Xử lý webcam realtime, YOLO11 person detection, Flask API streaming
│   ├── gate_controller.py  # Điều khiển cổng (CLOSED/OPEN). OPEN sau 10s phát hiện người liên tục (conf ≥ 0.7)
│   ├── database.py         # SQLite Database - Lưu trữ log phát hiện người, hỗ trợ thống kê và truy vấn
│   └── telegram_helper.py  # Telegram Bot - Gửi thông báo và ảnh cảnh báo khi phát hiện người. 
├── database/               # SQLite databases
├── data_images/            # Detection images
├── run.bat                 # One-click launch
└── requirements.txt
```


## Database Analytics

![SMAC Analytics](database/smac_analytics.png)

## Tính năng

- 📹 **Webcam realtime** - Stream video với bounding box
- 🎯 **Person detection** - YOLO11n phát hiện người
- 🚪 **Auto gate control** - Mở cổng sau 5s phát hiện người, đóng sau 2s không có người  
- 📊 **Database logging** - Lưu log sự kiện vào SQLite
- 📱 **Telegram alerts** - Gửi thông báo khi mở cổng (tùy chọn)
- 🌐 **Web dashboard** - Giao diện web điều khiển

```
Python Detection Server: http://localhost:8000
Web Dashboard: http://localhost:3000
```

## Cấu hình Telegram (tùy chọn)

Set environment variables:

```bash
set TELEGRAM_BOT_TOKEN=your_bot_token
set TELEGRAM_CHAT_ID=your_chat_id
```

Hoặc sửa trực tiếp trong `src/telegram_helper.py`.

## Logic cổng

- **OPEN**: Phát hiện người liên tục >= 5 giây
- **CLOSE**: Không có người >= 2 giây (debounce)

## 2. Yêu cầu chức năng (Functional Requirements)

### 2.1 Bảng tổng hợp yêu cầu chức năng

| ID | Yêu cầu | Mô tả | Độ ưu tiên |
|----|---------|-------|------------|
| **FR-01** | Phát hiện người | Hệ thống phải phát hiện người trong khung hình camera với độ chính xác ≥ 70% | Cao |
| **FR-02** | Điều khiển cổng tự động | Mở cổng sau 10s phát hiện người liên tục, đóng sau 0.5s không có người | Cao |
| **FR-03** | Stream video | Cung cấp video stream realtime qua web browser | Cao |
| **FR-04** | Điều khiển thủ công | Cho phép mở/đóng cổng thủ công qua giao diện web | Trung bình |
| **FR-05** | Gửi cảnh báo Telegram | Gửi thông báo và ảnh khi phát hiện người | Trung bình |
| **FR-06** | Lưu log phát hiện | Lưu thông tin phát hiện vào database | Cao |
| **FR-07** | Xem lịch sử | Hiển thị lịch sử các lần phát hiện | Trung bình |
| **FR-08** | Hiển thị trạng thái | Hiển thị trạng thái cổng, số người, độ tin cậy | Cao |
| **FR-09** | Lưu ảnh phát hiện | Lưu ảnh khi phát hiện người (mỗi 10s) | Thấp |
| **FR-10** | Countdown timer | Hiển thị thời gian đếm ngược trước khi mở cổng | Thấp |

### 2.2 Chi tiết từng yêu cầu chức năng

#### FR-01: Phát hiện người (Person Detection)
```
Mô tả: Sử dụng YOLO11n để phát hiện người trong khung hình
Input: Frame từ webcam (640x480, 30 FPS)
Output: Bounding boxes, confidence scores
Điều kiện: Confidence ≥ 0.7 (70%) mới được tính là phát hiện hợp lệ
```

#### FR-02: Điều khiển cổng tự động (Auto Gate Control)
```
Mô tả: State machine điều khiển cổng
States: CLOSED, OPEN
Transitions:
  - CLOSED → OPEN: Phát hiện người liên tục ≥ 10 giây
  - OPEN → CLOSED: Không có người ≥ 0.5 giây (debounce)
```

#### FR-03: Stream video (Video Streaming)
```
Mô tả: MJPEG streaming qua Flask
Protocol: HTTP
Endpoint: /video_feed hoặc /video
Format: multipart/x-mixed-replace
Quality: JPEG 80%
```

#### FR-04: Điều khiển thủ công (Manual Control)
```
Mô tả: API endpoints điều khiển cổng
Endpoints:
  - POST /api/gate/open - Mở cổng ngay lập tức
  - POST /api/gate/close - Đóng cổng ngay lập tức
```

#### FR-05: Cảnh báo Telegram (Telegram Alert)
```
Mô tả: Gửi thông báo khi phát hiện người
Content: Ảnh + số người + confidence + timestamp
Cooldown: 30 giây giữa các tin nhắn
```

#### FR-06: Lưu log database (Database Logging)
```
Mô tả: Lưu thông tin phát hiện vào SQLite
Fields: id, person_count, datetime, confidence, image_path
```


## 3. Yêu cầu phi chức năng (Non-functional Requirements)

### 3.1 Bảng tổng hợp yêu cầu phi chức năng

| ID | Loại | Yêu cầu | Mô tả | Metric |
|----|------|---------|-------|--------|
| **NFR-01** | Performance | Độ trễ xử lý | Thời gian từ capture đến hiển thị | ≤ 100ms |
| **NFR-02** | Performance | Frame rate | Tốc độ xử lý video | ≥ 25 FPS |
| **NFR-03** | Performance | Độ chính xác | Accuracy của person detection | ≥ 70% confidence |
| **NFR-04** | Reliability | Uptime | Thời gian hoạt động liên tục | 99% |
| **NFR-05** | Reliability | Fault tolerance | Khả năng phục hồi lỗi | Tự khởi động lại |
| **NFR-06** | Usability | Giao diện | Responsive, dễ sử dụng | Mobile-friendly |
| **NFR-07** | Usability | Thời gian học | Thời gian làm quen | ≤ 30 phút |
| **NFR-08** | Security | Authentication | Bảo vệ API | Token-based (tùy chọn) |
| **NFR-09** | Security | Data protection | Bảo vệ dữ liệu | Mã hóa credentials |
| **NFR-10** | Scalability | Concurrent users | Số người dùng đồng thời | ≥ 10 clients |
| **NFR-11** | Portability | Cross-platform | Hỗ trợ đa nền tảng | Windows, Linux |
| **NFR-12** | Maintainability | Modular design | Kiến trúc module hóa | Separation of concerns |

### 3.2 Chi tiết từng loại yêu cầu phi chức năng

#### 3.2.1 Performance (Hiệu suất)
```
- Xử lý realtime: ≤ 100ms latency
- Video streaming: 25-30 FPS
- YOLO inference: ≤ 50ms/frame trên GPU, ≤ 200ms trên CPU
- Database query: ≤ 50ms cho các truy vấn thông thường
- Memory usage: ≤ 2GB RAM
```

#### 3.2.2 Reliability (Độ tin cậy)
```
- Hệ thống hoạt động 24/7
- Tự động reconnect camera khi mất kết nối
- Graceful degradation khi Telegram không khả dụng
- Database backup định kỳ
```

#### 3.2.3 Usability (Khả năng sử dụng)
```
- Giao diện web responsive (desktop + mobile)
- Hiển thị trạng thái rõ ràng (màu sắc, icon)
- Feedback tức thì khi tương tác
- Hỗ trợ tiếng Việt
```

#### 3.2.4 Security (Bảo mật)
```
- Telegram credentials được bảo vệ
- CORS enabled cho web security
- Logging các truy cập bất thường
- Không lưu video dài hạn (chỉ ảnh)
```

#### 3.2.5 Scalability (Khả năng mở rộng)
```
- Hỗ trợ nhiều camera (tương lai)
- Database có thể migrate sang PostgreSQL
- Microservices architecture ready
```

#### 3.2.6 Maintainability (Khả năng bảo trì)
```
- Code được chia thành các module riêng biệt
- Documentation đầy đủ (README, docstrings)
- Logging chi tiết để debug
- Unit testable design
```

---


### So sánh Waterfall vs Scrum

| Tiêu chí | Waterfall | Scrum | SMAC phù hợp? |
|----------|-----------|-------|---------------|
| **Yêu cầu** | Cố định, rõ ràng từ đầu | Thay đổi liên tục | Waterfall ✓ |
| **Quy mô team** | Lớn, phân công rõ | Nhỏ, linh hoạt | Scrum ✓ |
| **Thời gian** | Dài, sequential | Ngắn, iterative | Phụ thuộc deadline |
| **Tài liệu** | Đầy đủ, formal | Tối thiểu | Waterfall ✓ (môn học) |
| **Testing** | Cuối dự án | Liên tục | Scrum ✓ |
| **Rủi ro** | Phát hiện muộn | Phát hiện sớm | Scrum ✓ |
| **Khách hàng** | Ít tham gia | Tham gia thường xuyên | Waterfall ✓ |
| **Thay đổi** | Khó, tốn kém | Dễ, linh hoạt | Scrum ✓ |

### Phân tích Waterfall cho SMAC

#### Ưu điểm:
```
✅ Yêu cầu rõ ràng: Dự án có scope cố định (detect person → control gate)
✅ Phù hợp môn học: Cần documentation đầy đủ (SRS, diagrams)
✅ Dễ quản lý tiến độ: Các phase rõ ràng
✅ Dễ đánh giá: Có deliverables cụ thể mỗi giai đoạn
```

#### Nhược điểm:
```
❌ Khó thay đổi: Nếu cần thêm tính năng giữa chừng
❌ Testing muộn: Lỗi có thể phát hiện muộn
❌ Rủi ro cao: Nếu yêu cầu ban đầu sai
```

#### Các phase Waterfall cho SMAC:
```
1. Requirements (1 tuần)
   - Thu thập yêu cầu
   - Tạo SRS document
   
2. Design (1 tuần)
   - Class diagram, Use case diagram
   - State diagram, Activity diagram
   - Sequence diagram
   
3. Implementation (2-3 tuần)
   - Backend: Python (detection, gate control)
   - Frontend: HTML/CSS/JS
   - Integration: Flask, Node.js
   
4. Testing (1 tuần)
   - Unit testing
   - Integration testing
   - User acceptance testing
   
5. Deployment (3 ngày)
   - Documentation
   - run.bat script
   - Demo
```

### 4.3 Phân tích Scrum cho SMAC

#### Ưu điểm:
```
✅ Linh hoạt: Dễ thêm/bớt tính năng
✅ Feedback sớm: Demo sau mỗi sprint
✅ Team nhỏ: Phù hợp dự án cá nhân/nhóm nhỏ
✅ Iterative: Cải tiến liên tục
```

#### Nhược điểm:
```
❌ Ít tài liệu: Không phù hợp yêu cầu môn học
❌ Cần team đầy đủ: Product Owner, Scrum Master
❌ Khó ước lượng: Tổng thời gian không rõ
```

#### Sprint plan cho SMAC:
```
Sprint 0: Setup (3 ngày)
- Cài đặt môi trường
- Tạo repository
- Setup CI/CD (nếu có)

Sprint 1: Core Detection (1 tuần)
- Webcam capture
- YOLO integration
- Basic bounding box

Sprint 2: Gate Control (1 tuần)
- State machine
- Timer logic
- Manual control API

Sprint 3: Notifications (1 tuần)
- Telegram integration
- Database logging
- Alert system

Sprint 4: Frontend (1 tuần)
- Web dashboard
- Video streaming
- Status display

Sprint 5: Polish (3 ngày)
- Bug fixes
- Documentation
- Demo preparation
```

---

## 📚 Tài liệu tham khảo

1. Sommerville, I. (2016). Software Engineering (10th Edition)
2. Pressman, R. S. (2014). Software Engineering: A Practitioner's Approach
3. Schwaber, K., & Sutherland, J. (2020). The Scrum Guide
4. YOLO Documentation: https://docs.ultralytics.com/

---

