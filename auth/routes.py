from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from models import User, db, AnalysisHistory, UserMessage, Notification, Conversation, ConversationMessage
from forms import LoginForm, RegisterForm, ProfileForm, PasswordChangeForm, UserMessageForm, PasswordResetRequestForm, PasswordResetForm
from datetime import datetime
import json

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Kullanıcı giriş sayfası"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Email veya username ile giriş
        email_or_username = form.email_or_username.data
        user = User.query.filter(
            (User.email == email_or_username) | (User.username == email_or_username)
        ).first()
        
        if user and user.check_password(form.password.data):
            if user.is_active:
                login_user(user, remember=form.remember_me.data)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                flash(f'Hoş geldiniz {user.first_name}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Hesabınız deaktif durumda. Lütfen destek ile iletişime geçin.', 'error')
        else:
            flash('Geçersiz kullanıcı adı/email veya şifre!', 'error')
    
    return render_template('auth/login.html', title='Giriş Yap', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Kullanıcı kayıt sayfası"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Kayıt işlemi başarılı! Hoş geldiniz {user.first_name}!', 'success')
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('auth/register.html', title='Kayıt Ol', form=form)

@auth.route('/logout')
@login_required
def logout():
    """Kullanıcı çıkış"""
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('index'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Kullanıcı profil sayfası"""
    form = ProfileForm()
    password_form = PasswordChangeForm()
    
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        db.session.commit()
        
        flash('Profil bilgileriniz güncellendi.', 'success')
        return redirect(url_for('auth.profile'))
    
    # Form verilerini doldur
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    form.phone.data = current_user.phone
    
    return render_template('auth/profile.html', title='Profil', form=form, password_form=password_form)

@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Şifre değiştirme sayfası"""
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        # Mevcut şifre kontrolü
        if not current_user.check_password(form.current_password.data):
            flash('Asıl şifreniz yanlış! Lütfen doğru şifrenizi girin.', 'error')
            return render_template('auth/change_password.html', title='Şifre Değiştir', form=form)
            
        # Yeni şifre aynı olmamalı
        if current_user.check_password(form.new_password.data):
            flash('Yeni şifreniz mevcut şifrenizle aynı olamaz!', 'error')
            return render_template('auth/change_password.html', title='Şifre Değiştir', form=form)
        
        # Şifreyi değiştir
        try:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Şifreniz başarıyla değiştirildi.', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Şifre değiştirme sırasında bir hata oluştu. Lütfen tekrar deneyin.', 'error')
    
    return render_template('auth/change_password.html', title='Şifre Değiştir', form=form)

@auth.route('/premium')
@login_required
def premium():
    """Premium üyelik sayfası"""
    return render_template('auth/premium.html', title='Premium Üyelik')

@auth.route('/contact-admin', methods=['GET', 'POST'])
@auth.route('/contact-admin/<package>', methods=['GET', 'POST'])
@login_required
def contact_admin(package=None):
    """Admin'e mesaj gönderme sayfası"""
    form = UserMessageForm()
    
    # Paket seçilmişse form alanlarını doldur
    if package:
        if request.method == 'GET':
            form.subject.data = f"Premium Paket Satın Alma Talebi - {package}"
            form.package_type.data = package
        elif request.method == 'POST':
            # POST'ta da package bilgisini koru
            if not form.subject.data:
                form.subject.data = f"Premium Paket Satın Alma Talebi - {package}"
            if not form.package_type.data:
                form.package_type.data = package
    
    # Kullanıcının önceki mesajlarını getir
    user_messages = UserMessage.query.filter_by(user_id=current_user.id).order_by(UserMessage.created_at.desc()).all()
    
    if request.method == 'POST':
        # Hidden field'dan package bilgisini al
        package_from_form = request.form.get('package')
        if package_from_form:
            package = package_from_form
        
        print(f"DEBUG: POST request alındı, package: {package}")
        print(f"DEBUG: Form validate: {form.validate_on_submit()}")
        print(f"DEBUG: Form errors: {form.errors}")
        print(f"DEBUG: Form data - subject: {form.subject.data}, package_type: {form.package_type.data}, message: {form.message.data}")
        
        # POST'ta form verilerini yeniden ayarla
        if package:
            if not form.subject.data:
                form.subject.data = f"Premium Paket Satın Alma Talebi - {package}"
            if not form.package_type.data:
                form.package_type.data = package
        
        if form.validate_on_submit():
            try:
                # Yeni mesaj oluştur
                message = UserMessage()
                message.user_id = current_user.id
                message.subject = form.subject.data or f"Premium Paket Satın Alma Talebi - {package}"
                message.message = form.message.data
                message.package_type = form.package_type.data or package
                message.status = 'pending'
                
                db.session.add(message)
                db.session.flush()  # ID'yi al
                
                # Premium paket mesajlarını Conversation sistemine de ekle
                from models import Conversation, ConversationMessage
                
                # Yeni konuşma oluştur
                conversation = Conversation()
                conversation.user_id = current_user.id
                conversation.subject = f"Premium Paket Talebi - {message.package_type}"
                conversation.status = 'active'
                
                db.session.add(conversation)
                db.session.flush()  # Conversation ID'sini al
                
                # İlk mesajı konuşmaya ekle
                conv_message = ConversationMessage()
                conv_message.conversation_id = conversation.id
                conv_message.sender_id = current_user.id
                conv_message.message = f"Paket: {message.package_type}\n\n{message.message}"
                conv_message.is_admin = False
                
                db.session.add(conv_message)
                
                # Conversation güncelleme zamanını ayarla
                conversation.updated_at = datetime.utcnow()
                
                # Admin'e bildirim gönder
                admin_notification = Notification()
                admin_notification.user_id = None  # Admin bildirimi
                admin_notification.title = 'Yeni Premium Paket Talebi'
                admin_notification.message = f'{current_user.first_name} {current_user.last_name} yeni bir premium paket talebi gönderdi: {message.package_type}'
                admin_notification.type = 'info'
                admin_notification.related_message_id = conversation.id
                
                db.session.add(admin_notification)
                db.session.commit()
                
                print(f"DEBUG: Mesaj başarıyla kaydedildi, ID: {message.id}")
                flash('Mesajınız başarıyla gönderildi! En kısa sürede yanıtlanacaktır.', 'success')
                return redirect(url_for('auth.contact_admin'))
                
            except Exception as e:
                print(f"DEBUG: Mesaj kaydetme hatası: {e}")
                db.session.rollback()
                flash('Mesaj gönderilirken bir hata oluştu. Lütfen tekrar deneyin.', 'error')
        else:
            print(f"DEBUG: Form validation başarısız: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f'{field}: {error}', 'error')
    
    return render_template('auth/contact_admin.html', 
                         title='Admin\'e Mesaj Gönder', 
                         form=form, 
                         package=package,
                         user_messages=user_messages)

@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Şifremi unuttum sayfası"""
    form = PasswordResetRequestForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Reset token oluştur
            token = user.generate_reset_token()
            
            # Şifre sıfırlama linki (şimdilik basit yaklaşım - email gönderme olmadan)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            flash(f'Şifre sıfırlama bağlantınız: {reset_url}', 'info')
            flash('Not: Bu bağlantıyı 1 saat içinde kullanmanız gerekmektedir.', 'warning')
            
            # Bildirim oluştur
            notification = Notification(
                user_id=user.id,
                title='Şifre Sıfırlama Talebi',
                message='Şifre sıfırlama talebiniz alınmıştır. Güvenlik nedeniyle bağlantı 1 saat geçerlidir.',
                type='warning'
            )
            db.session.add(notification)
            db.session.commit()
            
        else:
            flash('Bu email adresi ile kayıtlı kullanıcı bulunamadı.', 'error')
    
    return render_template('auth/forgot_password.html', title='Şifremi Unuttum', form=form)

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Şifre sıfırlama sayfası"""
    # Token ile kullanıcıyı bul
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash('Geçersiz veya süresi dolmuş bağlantı!', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    form = PasswordResetForm()
    
    if form.validate_on_submit():
        # Yeni şifreyi ayarla
        user.set_password(form.password.data)
        user.clear_reset_token()
        
        flash('Şifreniz başarıyla sıfırlandı. Yeni şifrenizle giriş yapabilirsiniz.', 'success')
        
        # Bildirim oluştur
        notification = Notification(
            user_id=user.id,
            title='Şifre Başarıyla Sıfırlandı',
            message='Şifreniz başarıyla değiştirildi. Hesabınızın güvenliği için düzenli olarak şifrenizi değiştirin.',
            type='success'
        )
        db.session.add(notification)
        db.session.commit()
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', title='Şifre Sıfırla', form=form, token=token)