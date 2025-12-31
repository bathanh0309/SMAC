"""
Telegram Helper Module
Gửi thông báo và ảnh đến Telegram Bot
"""
import requests
from datetime import datetime


class TelegramBot:
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_id = None
    
    def get_chat_id_from_updates(self):
        """Lấy Chat ID từ tin nhắn gần nhất"""
        try:
            url = f"{self.base_url}/getUpdates"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data.get('ok') and data.get('result'):
                # Lấy chat_id từ tin nhắn mới nhất
                for update in reversed(data['result']):
                    if 'message' in update:
                        chat_id = update['message']['chat']['id']
                        return chat_id
            return None
        except Exception as e:
            print(f"⚠️  Lỗi lấy Chat ID: {e}")
            return None
    
    def send_message(self, message, chat_id=None):
        """Gửi tin nhắn text"""
        if chat_id is None:
            chat_id = self.chat_id
        
        if chat_id is None:
            print("❌ Chưa có Chat ID! Gửi /start cho bot trước.")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=5)
            return response.json().get('ok', False)
        except Exception as e:
            print(f"⚠️  Lỗi gửi tin nhắn: {e}")
            return False
    
    def send_photo(self, image_path, caption="", chat_id=None):
        """Gửi ảnh với caption"""
        if chat_id is None:
            chat_id = self.chat_id
        
        if chat_id is None:
            print("❌ Chưa có Chat ID! Gửi /start cho bot trước.")
            return False
        
        try:
            url = f"{self.base_url}/sendPhoto"
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, data=data, files=files, timeout=10)
            return response.json().get('ok', False)
        except Exception as e:
            print(f"⚠️  Lỗi gửi ảnh: {e}")
            return False
    
    def send_detection_alert(self, image_path, num_people, confidence, custom_msg=None):
        """Gửi thông báo phát hiện người kèm ảnh"""
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        if custom_msg:
            caption = (
                f"{custom_msg}\n"
                f"🕒 {now}\n"
                f"📊 Confidence: {confidence:.2f}"
            )
        else:
            caption = (
                f"🚨 <b>Phát hiện {num_people} người!</b>\n"
                f"🕒 {now}\n"
                f"📊 Confidence: {confidence:.2f}"
            )
        
        return self.send_photo(image_path, caption)


# Khởi tạo bot với token
TELEGRAM_TOKEN = "8383210571:AAEfg3IIBtTVI_PcmfJ4w5uYgeM8thWqTPs"
telegram_bot = TelegramBot(TELEGRAM_TOKEN)

# Tự động lấy Chat ID
auto_chat_id = telegram_bot.get_chat_id_from_updates()
if auto_chat_id:
    telegram_bot.chat_id = auto_chat_id
    print(f"✅ Đã tìm thấy Chat ID: {auto_chat_id}")
else:
    print("⚠️  Chưa tìm thấy Chat ID. Vui lòng gửi /start cho @bathanh0309_bot")
