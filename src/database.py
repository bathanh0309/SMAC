"""
Database Module - SQLite
Quản lý lưu trữ thông tin phát hiện người
"""
import sqlite3
from datetime import datetime
import os


class DetectionDatabase:
    def __init__(self, db_path=None):
        """Khởi tạo database"""
        # Use absolute path for database
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'detections.db')
        self.db_path = os.path.abspath(db_path)
        self.conn = None
        self.create_database()
    
    def create_database(self):
        """Tạo database và bảng nếu chưa tồn tại"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        # Tạo bảng detections (simple schema)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_count INTEGER DEFAULT 1,
                datetime TEXT NOT NULL,
                confidence REAL NOT NULL,
                image_path TEXT
            )
        ''')
        
        self.conn.commit()
        print(f"[DB] Database đã sẵn sàng: {self.db_path}")
    
    def add_detection(self, person_count, confidence, image_path=None):
        """
        Thêm một bản ghi phát hiện mới
        
        Args:
            person_count (int): Số người phát hiện được
            confidence (float): Độ tin cậy
            image_path (str): Đường dẫn ảnh (optional)
        
        Returns:
            int: ID của bản ghi vừa thêm
        """
        cursor = self.conn.cursor()
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO detections (person_count, datetime, confidence, image_path)
            VALUES (?, ?, ?, ?)
        ''', (person_count, now, confidence, image_path))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_all_detections(self):
        """Lay tat ca ban ghi phat hien"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT person_count, datetime, confidence, image_path
            FROM detections
            ORDER BY datetime DESC
        ''')
        return cursor.fetchall()
    
    def get_recent_detections(self, limit=10):
        """Lay N ban ghi gan nhat"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT person_count, datetime, confidence, image_path
            FROM detections
            ORDER BY datetime DESC
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def get_stats(self):
        """Lay thong ke"""
        cursor = self.conn.cursor()
        
        # Tong so lan phat hien
        cursor.execute('SELECT COUNT(*) FROM detections')
        total = cursor.fetchone()[0]
        
        # Confidence trung binh
        cursor.execute('SELECT AVG(confidence) FROM detections')
        avg_conf = cursor.fetchone()[0] or 0
        
        # So nguoi nhieu nhat
        cursor.execute('SELECT MAX(person_count) FROM detections')
        max_people = cursor.fetchone()[0] or 0
        
        return {
            'total_detections': total,
            'avg_confidence': avg_conf,
            'max_people': max_people
        }
    
    def clear_all(self):
        """Xoa tat ca du lieu"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM detections')
        self.conn.commit()
        print("[DB] Da xoa toan bo du lieu")
    
    def close(self):
        """Dong ket noi database"""
        if self.conn:
            self.conn.close()
            print("[DB] Da dong database")


# Khoi tao database instance
db = DetectionDatabase()


if __name__ == "__main__":
    # Test database
    print("Testing database...")
    
    # Them du lieu mau
    db.add_detection(2, 0.89, "test1.jpg")
    db.add_detection(1, 0.95, "test2.jpg")
    
    # Lay du lieu
    records = db.get_all_detections()
    print(f"\nTong so ban ghi: {len(records)}")
    
    for record in records:
        print(f"Person: {record[0]}, Time: {record[1]}, Conf: {record[2]:.2f}")
    
    # Thong ke
    stats = db.get_stats()
    print(f"\n[Stats]")
    print(f"  - Tong phat hien: {stats['total_detections']}")
    print(f"  - Confidence TB: {stats['avg_confidence']:.2f}")
    print(f"  - Nguoi nhieu nhat: {stats['max_people']}")
