from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid
import secrets
from sqlalchemy import text

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Kullanıcı modeli"""
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Premium özellikler
    is_premium = db.Column(db.Boolean, default=False)
    premium_start_date = db.Column(db.DateTime)
    premium_end_date = db.Column(db.DateTime)
    
    # Kullanıcı bilgileri
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    
    # Sistem bilgileri
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Analiz limiti
    daily_analysis_count = db.Column(db.Integer, default=0)
    last_analysis_date = db.Column(db.Date)
    
    # Şifre sıfırlama
    reset_token = db.Column(db.String(100))
    reset_token_expiry = db.Column(db.DateTime)
    
    # İlişkiler
    analysis_history = db.relationship('AnalysisHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    user_messages = db.relationship('UserMessage', backref='user', lazy=True, cascade='all, delete-orphan')
    user_notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')
    user_conversations = db.relationship('Conversation', backref='user', lazy=True, cascade='all, delete-orphan')
    user_sent_messages = db.relationship('ConversationMessage', foreign_keys='ConversationMessage.sender_id', backref='sender', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Güvenli şifre hashleme - bcrypt kullanarak"""
        if not password or len(password) < 8:
            raise ValueError("Şifre en az 8 karakter olmalıdır")
        # Güçlü hash algoritması kullan (bcrypt, cost factor 12)  
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256:100000')
    
    def check_password(self, password):
        """Güvenli şifre kontrolü"""
        if not password or not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def generate_reset_token(self):
        """Güvenli reset token oluştur"""
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)  # 1 saat geçerli
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Reset token'ı doğrula"""
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        return secrets.compare_digest(self.reset_token, token)
    
    def activate_premium(self, days=30):
        """Premium üyelik aktifleştir"""
        self.is_premium = True
        self.premium_start_date = datetime.utcnow()
        self.premium_end_date = datetime.utcnow() + timedelta(days=days)
        
        # Kullanıcıya bildirim gönder
        from models import Notification
        notification = Notification(
            user_id=self.id,
            title='Premium Üyelik Aktif!',
            message=f'Premium üyeliğiniz başarıyla aktifleştirildi. {days} gün boyunca premium özelliklerden yararlanabilirsiniz.',
            type='success'
        )
        db.session.add(notification)
        db.session.commit()
    
    def deactivate_premium(self):
        """Premium üyelik deaktifleştir"""
        self.is_premium = False
        self.premium_start_date = None
        self.premium_end_date = None
        db.session.commit()
    
    def is_premium_active(self):
        """Premium üyelik aktif mi?"""
        if not self.is_premium:
            return False
        if self.premium_end_date and datetime.utcnow() > self.premium_end_date:
            # Süresi dolmuşsa otomatik deaktive et
            self.deactivate_premium()
            return False
        return True
    
    def get_premium_days_left(self):
        """Kalan premium gün sayısı"""
        if not self.is_premium_active():
            return 0
        if self.premium_end_date:
            delta = self.premium_end_date - datetime.utcnow()
            return max(0, delta.days)
        return 999  # Unlimited
    
    def generate_reset_token(self):
        """Şifre sıfırlama token'ı oluştur"""
        import secrets
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)  # 1 saat geçerli
        db.session.commit()
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Şifre sıfırlama token'ını doğrula"""
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if self.reset_token != token:
            return False
        if datetime.utcnow() > self.reset_token_expiry:
            return False
        return True
    
    def clear_reset_token(self):
        """Şifre sıfırlama token'ını temizle"""
        self.reset_token = None
        self.reset_token_expiry = None
        db.session.commit()
    
    def can_make_analysis(self):
        """Kullanıcı analiz yapabilir mi?"""
        from datetime import date
        today = date.today()
        
        # Premium kullanıcılar için günlük limit kontrolü
        if self.is_premium_active():
            # Eğer bugün hiç analiz yapmadıysa sıfırla
            if self.last_analysis_date != today:
                self.daily_analysis_count = 0
                self.last_analysis_date = today
                db.session.commit()
            
            # Premium kullanıcılar günde 10 analiz yapabilir
            if self.daily_analysis_count < 10:
                return True, f"Premium kullanıcı - Bugün {10 - self.daily_analysis_count} analiz hakkınız kaldı"
            else:
                return False, "Günlük premium analiz limitiniz doldu (10/10). Yarın tekrar deneyebilirsiniz."
        
        # Normal kullanıcılar için toplam 2 analiz hakkı (yenilenmeyen)
        total_analysis_count = self.daily_analysis_count or 0
        if total_analysis_count < 2:
            return True, f"Toplam {2 - total_analysis_count} analiz hakkınız kaldı"
        
        return False, "Ücretsiz analiz hakkınız doldu (2/2). Premium üyelikle günde 10 analiz yapabilirsiniz."
    
    def increment_analysis_count(self):
        """Analiz sayacını artır"""
        from datetime import date
        today = date.today()
        
        if self.is_premium_active():
            # Premium kullanıcılar için günlük sayaç
            if self.last_analysis_date != today:
                self.daily_analysis_count = 1
                self.last_analysis_date = today
            else:
                self.daily_analysis_count += 1
        else:
            # Normal kullanıcılar için toplam sayaç (tarihe bağlı değil)
            self.daily_analysis_count = (self.daily_analysis_count or 0) + 1
        
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'

class AnalysisHistory(db.Model):
    """Kullanıcı analiz geçmişi"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Analiz bilgileri
    city = db.Column(db.String(50), nullable=False)
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
    race_count = db.Column(db.Integer)
    analysis_type = db.Column(db.String(20), default='normal')  # normal, detailed, comparison
    
    # Sonuçlar
    success_rate = db.Column(db.Float)
    total_races = db.Column(db.Integer)
    successful_predictions = db.Column(db.Integer)
    
    # JSON verisi (detaylar)
    analysis_data = db.Column(db.Text)  # JSON string
    
    def __repr__(self):
        return f'<AnalysisHistory {self.city} - {self.analysis_date}>'

class SystemSettings(db.Model):
    """Sistem ayarları"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.String(200))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_setting(key, default_value=None):
        """Ayar değeri al"""
        setting = SystemSettings.query.filter_by(key=key).first()
        return setting.value if setting else default_value
    
    @staticmethod
    def set_setting(key, value, description=None):
        """Ayar değeri kaydet"""
        setting = SystemSettings.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
            if description:
                setting.description = description
        else:
            setting = SystemSettings(key=key, value=value, description=description)
            db.session.add(setting)
        db.session.commit()
        return setting

class UserMessage(db.Model):
    """Kullanıcı mesajları modeli"""
    __tablename__ = 'user_message'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    package_type = db.Column(db.String(50))  # 1hafta, 1ay, 3ay, 6ay
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_response = db.Column(db.Text)
    responded_at = db.Column(db.DateTime)
    
    # İlişki - User modelinde tanımlandı
    
    def __repr__(self):
        return f'<UserMessage {self.id}: {self.subject}>'

class Notification(db.Model):
    """Bildirim modeli"""
    __tablename__ = 'notification'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # null ise admin bildirimi
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # info, success, warning, error
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    related_message_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=True)
    
    # İlişki - User modelinde tanımlandı
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.title}>'

class Conversation(db.Model):
    """Konuşma modeli - Kullanıcı ve admin arasında sürekli mesajlaşma"""
    __tablename__ = 'conversation'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='active')  # active, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # İlişki - User modelinde tanımlandı
    
    def __repr__(self):
        return f'<Conversation {self.id}: {self.subject}>'

class ConversationMessage(db.Model):
    """Konuşma mesajları modeli"""
    __tablename__ = 'conversation_message'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # null ise admin göndermiş
    message = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    # İlişki
    conversation = db.relationship('Conversation', backref=db.backref('messages', lazy=True, order_by='ConversationMessage.created_at', cascade='all, delete-orphan'))
    # sender relationship User modelinde tanımlandı
    
    def __repr__(self):
        return f'<ConversationMessage {self.id}: {self.conversation_id}>'