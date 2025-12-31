"""
Telegram Helper Module
Gui thong bao va anh den Telegram Bot
Handles empty credentials gracefully
"""
import os
import requests
from datetime import datetime


class TelegramBot:
    def __init__(self, token=None, chat_id=None):
        """
        Initialize Telegram bot
        
        Args:
            token: Bot token (or set TELEGRAM_BOT_TOKEN env var)
            chat_id: Chat ID (or set TELEGRAM_CHAT_ID env var)
        """
        # Get from env or params (env takes priority)
        self.token = os.environ.get('TELEGRAM_BOT_TOKEN', token or '')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID', chat_id or '')
        
        # Check if configured
        self.is_configured = bool(self.token and self.chat_id)
        
        if self.is_configured:
            self.base_url = f"https://api.telegram.org/bot{self.token}"
            print(f"[Telegram] Configured (Chat ID: {self.chat_id})")
        else:
            self.base_url = None
            if self.token and not self.chat_id:
                print("[Telegram] Token set, auto-detecting chat_id...")
            else:
                print("[Telegram] Not configured - notifications disabled")
    
    def _check_configured(self) -> bool:
        """Check if bot is configured"""
        if not self.is_configured:
            return False
        return True
    
    def get_chat_id_from_updates(self):
        """Lay Chat ID tu tin nhan gan nhat"""
        if not self.token:
            return None
        
        try:
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            if data.get('ok') and data.get('result'):
                for update in reversed(data['result']):
                    if 'message' in update:
                        chat_id = update['message']['chat']['id']
                        return str(chat_id)
            return None
        except Exception as e:
            print(f"[Telegram] Error getting Chat ID: {e}")
            return None
    
    def send_message(self, message, chat_id=None):
        """Gui tin nhan text"""
        if not self._check_configured():
            return False
        
        target_chat = chat_id or self.chat_id
        
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': target_chat,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=5)
            return response.json().get('ok', False)
        except Exception as e:
            print(f"[Telegram] Error sending message: {e}")
            return False
    
    def send_photo(self, image_path, caption="", chat_id=None):
        """Gui anh voi caption"""
        if not self._check_configured():
            return False
        
        target_chat = chat_id or self.chat_id
        
        if not os.path.exists(image_path):
            print(f"[Telegram] Image not found: {image_path}")
            return False
        
        try:
            url = f"{self.base_url}/sendPhoto"
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': target_chat,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, data=data, files=files, timeout=10)
            result = response.json()
            if result.get('ok'):
                print(f"[Telegram] Photo sent successfully")
                return True
            else:
                print(f"[Telegram] Failed: {result.get('description', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"[Telegram] Error sending photo: {e}")
            return False
    
    def send_detection_alert(self, image_path, num_people, confidence, custom_msg=None):
        """Gửi thông báo phát hiện người kèm ảnh"""
        if not self._check_configured():
            return False
        
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # Format with Vietnamese diacritics and warning icon
        caption = (
            f"⚠️ <b>Phát hiện {num_people} người (Conf: {confidence:.2f})</b>\n"
            f"🕐 Time: {now}"
        )
        
        return self.send_photo(image_path, caption)


# ============ CONFIGURATION ============
# Your Telegram Bot Token
TELEGRAM_TOKEN = "8383210571:AAEfg3IIBtTVI_PcmfJ4w5uYgeM8thWqTPs"

# Chat ID from Telegram API
TELEGRAM_CHAT_ID = "7827433045"

# Initialize bot
telegram_bot = TelegramBot(token=TELEGRAM_TOKEN, chat_id=TELEGRAM_CHAT_ID)

# Auto-detect chat_id if token is set but chat_id is empty
if telegram_bot.token and not telegram_bot.chat_id:
    auto_chat_id = telegram_bot.get_chat_id_from_updates()
    if auto_chat_id:
        telegram_bot.chat_id = auto_chat_id
        telegram_bot.is_configured = True
        print(f"[Telegram] Auto-detected Chat ID: {auto_chat_id}")
    else:
        print("[Telegram] Send /start to @bathanh0309_bot first, then restart")
