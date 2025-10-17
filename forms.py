from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from models import User
import re
import html

class SafeStringField(StringField):
    """XSS korumalı string field"""
    def process_formdata(self, valuelist):
        if valuelist:
            # HTML escape ve temizlik
            self.data = html.escape(valuelist[0].strip()) if valuelist[0] else ''
        else:
            self.data = ''

class SafeTextAreaField(TextAreaField):
    """XSS korumalı textarea field"""  
    def process_formdata(self, valuelist):
        if valuelist:
            # HTML escape ve temizlik
            self.data = html.escape(valuelist[0].strip()) if valuelist[0] else ''
        else:
            self.data = ''

class LoginForm(FlaskForm):
    """Güvenli giriş formu"""
    email_or_username = SafeStringField('Email veya Kullanıcı Adı', validators=[
        DataRequired(), 
        Length(min=3, max=120),
        Regexp(r'^[a-zA-Z0-9@._-]+$', message='Geçersiz karakterler kullanıldı')
    ])
    password = PasswordField('Şifre', validators=[DataRequired(), Length(max=200)])
    remember_me = BooleanField('Beni Hatırla')

class RegisterForm(FlaskForm):
    """Güvenli kayıt formu"""
    username = SafeStringField('Kullanıcı Adı', validators=[
        DataRequired(), 
        Length(min=3, max=20),
        Regexp(r'^[a-zA-Z0-9_-]+$', message='Kullanıcı adında sadece harf, rakam, _ ve - kullanılabilir')
    ])
    email = SafeStringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    first_name = SafeStringField('Ad', validators=[
        DataRequired(), 
        Length(min=2, max=50),
        Regexp(r'^[a-zA-ZçğıöşüÇĞIİÖŞÜ\s]+$', message='Adda sadece harf kullanılabilir')
    ])
    last_name = SafeStringField('Soyad', validators=[
        DataRequired(), 
        Length(min=2, max=50),
        Regexp(r'^[a-zA-ZçğıöşüÇĞIİÖŞÜ\s]+$', message='Soyadda sadece harf kullanılabilir')
    ])
    phone = SafeStringField('Telefon', validators=[
        DataRequired(), 
        Length(min=10, max=20),
        Regexp(r'^[0-9+\s()-]+$', message='Geçersiz telefon formatı')
    ])
    password = PasswordField('Şifre', validators=[
        DataRequired(), 
        Length(min=8, max=200),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', message='Şifre en az 1 küçük harf, 1 büyük harf ve 1 rakam içermeli')
    ])
    password2 = PasswordField('Şifre Tekrar', validators=[DataRequired(), EqualTo('password', message='Şifreler eşleşmiyor')])
    
    # Sözleşme onayları
    agreement_terms = BooleanField('Üyelik Sözleşmesi', validators=[DataRequired(message='Üyelik sözleşmesini kabul etmelisiniz')])
    agreement_distance = BooleanField('Mesafeli Satış Sözleşmesi', validators=[DataRequired(message='Mesafeli satış sözleşmesini kabul etmelisiniz')])
    agreement_privacy = BooleanField('Gizlilik ve Çerez Politikası', validators=[DataRequired(message='Gizlilik ve çerez politikasını kabul etmelisiniz')])
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Bu kullanıcı adı zaten kullanılıyor.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Bu email adresi zaten kayıtlı.')

class ProfileForm(FlaskForm):
    """Profil güncelleme formu"""
    first_name = StringField('Ad', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Soyad', validators=[DataRequired(), Length(min=2, max=50)])
    phone = StringField('Telefon', validators=[Length(max=20)])

class PasswordChangeForm(FlaskForm):
    """Şifre değiştirme formu"""
    current_password = PasswordField('Mevcut Şifre', validators=[DataRequired()])
    new_password = PasswordField('Yeni Şifre', validators=[DataRequired(), Length(min=6)])
    new_password2 = PasswordField('Yeni Şifre Tekrar', validators=[DataRequired(), EqualTo('new_password', message='Şifreler eşleşmiyor')])

class PasswordResetRequestForm(FlaskForm):
    """Şifre sıfırlama talep formu"""
    email = StringField('Email Adresiniz', validators=[DataRequired(), Email()])
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('Bu email adresi ile kayıtlı kullanıcı bulunamadı.')

class PasswordResetForm(FlaskForm):
    """Şifre sıfırlama formu"""
    password = PasswordField('Yeni Şifre', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Yeni Şifre Tekrar', validators=[DataRequired(), EqualTo('password', message='Şifreler eşleşmiyor')])

class AdminUserForm(FlaskForm):
    """Admin kullanıcı yönetim formu"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Kullanıcı Adı', validators=[DataRequired(), Length(min=3, max=20)])
    first_name = StringField('Ad', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Soyad', validators=[DataRequired(), Length(min=2, max=50)])
    phone = StringField('Telefon', validators=[Length(max=20)])
    is_premium = BooleanField('Premium Üye')
    is_admin = BooleanField('Admin')
    is_active = BooleanField('Aktif')
    premium_days = IntegerField('Premium Gün Sayısı', default=30)

class SystemSettingForm(FlaskForm):
    """Sistem ayarları formu"""
    key = StringField('Ayar Anahtarı', validators=[DataRequired(), Length(max=100)])
    value = TextAreaField('Değer')
    description = StringField('Açıklama', validators=[Length(max=200)])

class UserMessageForm(FlaskForm):
    """Kullanıcı mesaj formu"""
    subject = StringField('Konu', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Mesaj', validators=[DataRequired(), Length(max=1000)])
    package_type = SelectField('Paket Seçimi', 
                              choices=[
                                  ('1hafta', '1 Hafta Premium (150₺)'),
                                  ('1ay', '1 Ay Premium (500₺)'), 
                                  ('3ay', '3 Ay Premium (1400₺)'),
                                  ('6ay', '6 Ay Premium (2400₺)')
                              ],
                              validators=[DataRequired()])

class ConversationForm(FlaskForm):
    """Yeni konuşma başlatma formu"""
    subject = StringField('Konu', validators=[DataRequired(), Length(min=5, max=200)])
    message = TextAreaField('Mesaj', validators=[DataRequired(), Length(max=1000)])

class ConversationMessageForm(FlaskForm):
    """Konuşma mesajı gönderme formu"""
    message = TextAreaField('Mesaj', validators=[DataRequired(), Length(max=1000)])