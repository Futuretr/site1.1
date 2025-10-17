from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from . import admin
from models import User, db, AnalysisHistory, SystemSettings, UserMessage, Notification, Conversation, ConversationMessage
from forms import AdminUserForm, SystemSettingForm, ConversationMessageForm
from datetime import datetime, timedelta

def admin_required(f):
    """Admin yetkisi kontrolü decorator'ı"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Bu sayfaya erişim yetkiniz yok!', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # İstatistikler
    total_users = User.query.count()
    premium_users = User.query.filter_by(is_premium=True).count()
    active_users = User.query.filter_by(is_active=True).count()
    total_analyses = AnalysisHistory.query.count()
    
    # Son kayıtlar
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_analyses = AnalysisHistory.query.order_by(AnalysisHistory.analysis_date.desc()).limit(10).all()
    
    stats = {
        'total_users': total_users,
        'premium_users': premium_users,
        'active_users': active_users,
        'total_analyses': total_analyses,
        'premium_rate': round((premium_users / total_users * 100) if total_users > 0 else 0, 1)
    }
    
    return render_template('admin/dashboard.html', 
                         title='Admin Panel', 
                         stats=stats,
                         recent_users=recent_users,
                         recent_analyses=recent_analyses)

@admin.route('/users')
@login_required
@admin_required
def users():
    """Kullanıcı listesi"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.username.contains(search)) |
            (User.email.contains(search)) |
            (User.first_name.contains(search)) |
            (User.last_name.contains(search))
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', title='Kullanıcı Yönetimi', users=users, search=search)

@admin.route('/user/<int:user_id>')
@login_required
@admin_required
def user_detail(user_id):
    """Kullanıcı detay sayfası"""
    user = User.query.get_or_404(user_id)
    analyses = AnalysisHistory.query.filter_by(user_id=user.id).order_by(AnalysisHistory.analysis_date.desc()).limit(20).all()
    
    # Şehir istatistiklerini hesapla
    city_counts = {}
    for analysis in analyses:
        city = analysis.city
        city_counts[city] = city_counts.get(city, 0) + 1
    
    # Şehirleri kullanım sayısına göre sırala
    city_counts = dict(sorted(city_counts.items(), key=lambda x: x[1], reverse=True))
    
    return render_template('admin/user_detail.html', title=f'Kullanıcı: {user.username}', user=user, analyses=analyses, city_counts=city_counts)

@admin.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """Kullanıcı düzenleme"""
    user = User.query.get_or_404(user_id)
    form = AdminUserForm()
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.is_admin = form.is_admin.data
        user.is_active = form.is_active.data
        
        # Premium durumu
        was_premium = user.is_premium
        new_premium = form.is_premium.data
        premium_days = form.premium_days.data or 30
        
        if new_premium:
            if not was_premium:
                # Premium aktifleştir
                user.activate_premium(premium_days)
                flash(f'{user.username} için {premium_days} günlük premium aktifleştirildi.', 'success')
            else:
                # Mevcut premium süresine ekleme yap
                if premium_days > 0:
                    from datetime import datetime, timedelta
                    if user.premium_end_date:
                        # Mevcut bitiş tarihine ekle
                        user.premium_end_date = user.premium_end_date + timedelta(days=premium_days)
                    else:
                        # Eğer bitiş tarihi yoksa bugünden başlat
                        user.premium_end_date = datetime.utcnow() + timedelta(days=premium_days)
                    flash(f'{user.username} premium süresine {premium_days} gün eklendi.', 'success')
        elif was_premium and not new_premium:
            # Premium deaktifleştir
            user.deactivate_premium()
            flash(f'{user.username} premium üyeliği iptal edildi.', 'info')
        
        db.session.commit()
        flash('Kullanıcı bilgileri güncellendi.', 'success')
        return redirect(url_for('admin.user_detail', user_id=user.id))
    
    # Form verilerini doldur
    form.username.data = user.username
    form.email.data = user.email
    form.first_name.data = user.first_name
    form.last_name.data = user.last_name
    form.phone.data = user.phone
    form.is_premium.data = user.is_premium
    form.is_admin.data = user.is_admin
    form.is_active.data = user.is_active
    
    return render_template('admin/edit_user.html', title=f'Düzenle: {user.username}', user=user, form=form)

@admin.route('/user/<int:user_id>/toggle_premium', methods=['POST'])
@login_required
@admin_required
def toggle_premium(user_id):
    """Premium durumu değiştir (AJAX)"""
    user = User.query.get_or_404(user_id)
    days = request.json.get('days', 30) if request.is_json else 30
    
    if user.is_premium:
        user.deactivate_premium()
        message = f'{user.username} premium üyeliği iptal edildi.'
        status = 'deactivated'
    else:
        user.activate_premium(days)
        message = f'{user.username} için {days} günlük premium aktifleştirildi.'
        status = 'activated'
    
    return jsonify({
        'success': True,
        'message': message,
        'status': status,
        'is_premium': user.is_premium,
        'premium_days_left': user.get_premium_days_left()
    })

@admin.route('/analyses')
@login_required
@admin_required
def analyses():
    """Analiz geçmişi"""
    page = request.args.get('page', 1, type=int)
    city_filter = request.args.get('city', '', type=str)
    
    query = AnalysisHistory.query.join(User)
    
    if city_filter:
        query = query.filter(AnalysisHistory.city == city_filter)
    
    analyses = query.order_by(AnalysisHistory.analysis_date.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Şehir listesi
    cities = db.session.query(AnalysisHistory.city).distinct().all()
    cities = [c[0] for c in cities]
    
    return render_template('admin/analyses.html', 
                         title='Analiz Geçmişi', 
                         analyses=analyses,
                         cities=cities,
                         city_filter=city_filter)

@admin.route('/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def settings():
    """Sistem ayarları"""
    form = SystemSettingForm()
    
    if form.validate_on_submit():
        SystemSettings.set_setting(
            form.key.data,
            form.value.data,
            form.description.data
        )
        flash('Ayar kaydedildi.', 'success')
        return redirect(url_for('admin.settings'))
    
    # Mevcut ayarlar
    settings = SystemSettings.query.all()
    
    return render_template('admin/settings.html', 
                         title='Sistem Ayarları', 
                         form=form,
                         settings=settings)

@admin.route('/setting/<int:setting_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_setting(setting_id):
    """Ayar silme"""
    setting = SystemSettings.query.get_or_404(setting_id)
    key = setting.key
    db.session.delete(setting)
    db.session.commit()
    
    flash(f'Ayar "{key}" silindi.', 'info')
    return redirect(url_for('admin.settings'))

@admin.route('/data_management')
@login_required
@admin_required
def data_management():
    """Veri yönetimi sayfası"""
    import os
    from datetime import datetime
    
    # Mevcut veri dosyalarını kontrol et
    data_folder = 'data'
    data_files = []
    
    if os.path.exists(data_folder):
        for file in os.listdir(data_folder):
            if file.endswith('.json'):
                file_path = os.path.join(data_folder, file)
                file_stat = os.stat(file_path)
                file_info = {
                    'name': file,
                    'size': round(file_stat.st_size / 1024, 2),  # KB cinsinden
                    'modified': datetime.fromtimestamp(file_stat.st_mtime),
                    'city': file.split('_')[0] if '_' in file else 'Unknown'
                }
                data_files.append(file_info)
    
    # Şehir listesi
    cities = ['istanbul', 'ankara', 'izmir', 'bursa', 'adana', 'kocaeli', 'sanliurfa', 'diyarbakir', 'elazig']
    
    # Son veri çekme zamanlarını kontrol et
    last_fetch_times = {}
    for city in cities:
        city_files = [f for f in data_files if f['city'] == city]
        if city_files:
            last_fetch_times[city] = max(city_files, key=lambda x: x['modified'])['modified']
        else:
            last_fetch_times[city] = None
    
    return render_template('admin/data_management.html', 
                         title='Veri Yönetimi',
                         data_files=data_files,
                         cities=cities,
                         last_fetch_times=last_fetch_times)

@admin.route('/fetch_city_data/<city>')
@login_required
@admin_required
def fetch_city_data(city):
    """Tek şehir için veri çek"""
    try:
        # Horse scraper modülünü import et
        import horse_scraper
        
        # Şehir fonksiyonları
        city_functions = {
            'istanbul': horse_scraper.get_istanbul_races_and_horse_last_race,
            'ankara': horse_scraper.get_ankara_races_and_horse_last_race,
            'izmir': horse_scraper.get_izmir_races_and_horse_last_race,
            'bursa': horse_scraper.get_bursa_races_and_horse_last_race,
            'adana': horse_scraper.get_adana_races_and_horse_last_race,
            'kocaeli': horse_scraper.get_kocaeli_races_and_horse_last_race,
            'sanliurfa': horse_scraper.get_sanliurfa_races_and_horse_last_race,
            'diyarbakir': horse_scraper.get_diyarbakir_races_and_horse_last_race,
            'elazig': horse_scraper.get_elazig_races_and_horse_last_race
        }
        
        if city not in city_functions:
            return jsonify({'success': False, 'error': 'Geçersiz şehir'})
        
        # Veriyi çek
        horses = city_functions[city]()
        
        if horses and isinstance(horses, list) and len(horses) > 0:
            # Verileri kaydet
            from datetime import datetime
            import pandas as pd
            import json
            import os
            
            # CSV dosyası oluştur
            df = pd.DataFrame(horses)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{city}_atlari_{timestamp}.csv"
            filepath = os.path.join('static', 'downloads', filename)
            
            # Downloads klasörü yoksa oluştur
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            # JSON dosyası da kaydet (analiz için gerekli)
            today = datetime.now().strftime('%Y%m%d')
            json_filename = f"{city}_atlari_{today}.json"
            json_filepath = os.path.join('data', json_filename)
            
            # Data klasörü yoksa oluştur
            os.makedirs('data', exist_ok=True)
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(horses, f, ensure_ascii=False, indent=2)
            
            flash(f'{city.title()} şehri için veri başarıyla çekildi ve kaydedildi.', 'success')
            return jsonify({
                'success': True, 
                'message': f'{city.title()} verisi güncellendi ({len(horses)} at)',
                'data': {
                    'city': city.title(),
                    'total_horses': len(horses),
                    'csv_file': filename,
                    'json_file': json_filename
                }
            })
        else:
            error_msg = 'Veri çekilemedi veya boş'
            flash(f'{city.title()} için veri çekilemedi', 'error')
            return jsonify({'success': False, 'error': error_msg})
            
    except Exception as e:
        flash(f'{city.title()} veri çekme hatası: {str(e)}', 'error')
        return jsonify({'success': False, 'error': str(e)})

@admin.route('/fetch_all_data')
@login_required
@admin_required
def fetch_all_data():
    """Tüm şehirler için veri çek"""
    try:
        import horse_scraper
        
        cities = ['istanbul', 'ankara', 'izmir', 'bursa', 'adana', 'kocaeli', 'sanliurfa', 'diyarbakir', 'elazig']
        results = {}
        success_count = 0
        
        for city in cities:
            try:
                city_functions = {
                    'istanbul': horse_scraper.get_istanbul_races_and_horse_last_race,
                    'ankara': horse_scraper.get_ankara_races_and_horse_last_race,
                    'izmir': horse_scraper.get_izmir_races_and_horse_last_race,
                    'bursa': horse_scraper.get_bursa_races_and_horse_last_race,
                    'adana': horse_scraper.get_adana_races_and_horse_last_race,
                    'kocaeli': horse_scraper.get_kocaeli_races_and_horse_last_race,
                    'sanliurfa': horse_scraper.get_sanliurfa_races_and_horse_last_race,
                    'diyarbakir': horse_scraper.get_diyarbakir_races_and_horse_last_race,
                    'elazig': horse_scraper.get_elazig_races_and_horse_last_race
                }
                
                horses = city_functions[city]()
                if horses and isinstance(horses, list) and len(horses) > 0:
                    # Verileri kaydet (fetch_city_data ile aynı mantık)
                    from datetime import datetime
                    import pandas as pd
                    import json
                    import os
                    
                    # CSV dosyası oluştur
                    df = pd.DataFrame(horses)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{city}_atlari_{timestamp}.csv"
                    filepath = os.path.join('static', 'downloads', filename)
                    
                    # Downloads klasörü yoksa oluştur
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    df.to_csv(filepath, index=False, encoding='utf-8-sig')
                    
                    # JSON dosyası da kaydet (analiz için gerekli)
                    today = datetime.now().strftime('%Y%m%d')
                    json_filename = f"{city}_atlari_{today}.json"
                    json_filepath = os.path.join('data', json_filename)
                    
                    # Data klasörü yoksa oluştur
                    os.makedirs('data', exist_ok=True)
                    with open(json_filepath, 'w', encoding='utf-8') as f:
                        json.dump(horses, f, ensure_ascii=False, indent=2)
                    
                    results[city] = {'success': True, 'data': {'total_horses': len(horses), 'files': [filename, json_filename]}}
                    success_count += 1
                else:
                    results[city] = {'success': False, 'error': 'Veri çekilemedi veya boş'}
                    
            except Exception as e:
                results[city] = {'success': False, 'error': str(e)}
        
        flash(f'Toplu veri çekme tamamlandı. {success_count}/{len(cities)} şehir başarılı.', 
              'success' if success_count > 0 else 'warning')
        
        return jsonify({
            'success': True,
            'results': results,
            'success_count': success_count,
            'total_count': len(cities)
        })
        
    except Exception as e:
        flash(f'Toplu veri çekme hatası: {str(e)}', 'error')
        return jsonify({'success': False, 'error': str(e)})

@admin.route('/schedule_auto_fetch', methods=['POST'])
@login_required
@admin_required
def schedule_auto_fetch():
    """Otomatik veri çekme zamanlaması"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        time_str = data.get('time', '08:00')  # Varsayılan saat 08:00
        
        # Sistem ayarlarına kaydet
        SystemSettings.set_setting('auto_fetch_enabled', str(enabled))
        SystemSettings.set_setting('auto_fetch_time', time_str)
        
        if enabled:
            # Burada cron job veya scheduler kurulumu yapılabilir
            # Şimdilik sistem ayarlarına kaydediyoruz
            flash(f'Otomatik veri çekme {time_str} saatinde aktifleştirildi.', 'success')
        else:
            flash('Otomatik veri çekme devre dışı bırakıldı.', 'info')
        
        return jsonify({'success': True})
        
    except Exception as e:
        flash(f'Zamanlama ayarı hatası: {str(e)}', 'error')
        return jsonify({'success': False, 'error': str(e)})

@admin.route('/clear_old_data', methods=['POST'])
@login_required
@admin_required
def clear_old_data():
    """Eski veri dosyalarını temizle"""
    try:
        import os
        from datetime import datetime, timedelta
        
        data = request.get_json()
        days = int(data.get('days', 7))  # Varsayılan 7 gün
        
        data_folder = 'data'
        if not os.path.exists(data_folder):
            return jsonify({'success': False, 'error': 'Veri klasörü bulunamadı'})
        
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_files = []
        
        for file in os.listdir(data_folder):
            if file.endswith('.json'):
                file_path = os.path.join(data_folder, file)
                file_stat = os.stat(file_path)
                file_date = datetime.fromtimestamp(file_stat.st_mtime)
                
                if file_date < cutoff_date:
                    os.remove(file_path)
                    deleted_files.append(file)
        
        flash(f'{len(deleted_files)} adet eski veri dosyası temizlendi.', 'success')
        return jsonify({
            'success': True,
            'deleted_count': len(deleted_files),
            'deleted_files': deleted_files
        })
        
    except Exception as e:
        flash(f'Veri temizleme hatası: {str(e)}', 'error')
        return jsonify({'success': False, 'error': str(e)})

@admin.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Kullanıcıyı sil"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Admin kendini silemez
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': 'Kendinizi silemezsiniz.'})
        
        # Kullanıcı adını kaydet (silmeden önce)
        username = user.username
        
        # Manuel olarak ilişkili verileri sil (güvenlik için)
        try:
            # Kullanıcının mesajlarını sil
            UserMessage.query.filter_by(user_id=user_id).delete()
            
            # Kullanıcının konuşma mesajlarını sil
            ConversationMessage.query.filter_by(sender_id=user_id).delete()
            
            # Kullanıcının konuşmalarını sil
            Conversation.query.filter_by(user_id=user_id).delete()
            
            # Kullanıcının bildirimlerini sil
            Notification.query.filter_by(user_id=user_id).delete()
            
            # Kullanıcının analiz geçmişini sil
            AnalysisHistory.query.filter_by(user_id=user_id).delete()
            
            # Son olarak kullanıcıyı sil
            db.session.delete(user)
            db.session.commit()
            
            return jsonify({'success': True, 'message': f'Kullanıcı "{username}" başarıyla silindi.'})
            
        except Exception as inner_e:
            db.session.rollback()
            current_app.logger.error(f'Kullanıcı silme hatası (inner): {str(inner_e)}')
            return jsonify({'success': False, 'message': f'Veri silme hatası: {str(inner_e)}'})
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Kullanıcı silme hatası: {str(e)}')
        return jsonify({'success': False, 'message': f'Kullanıcı silinirken hata oluştu: {str(e)}'})

@admin.route('/messages')
@login_required
@admin_required
def messages():
    """Kullanıcı mesajları listesi"""
    messages = UserMessage.query.join(User).order_by(UserMessage.created_at.desc()).all()
    return render_template('admin/messages.html', title='Kullanıcı Mesajları', messages=messages)

@admin.route('/reply_message/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def reply_message(message_id):
    """Kullanıcı mesajına yanıt ver"""
    message = UserMessage.query.get_or_404(message_id)
    response = request.form.get('response')
    
    if response:
        message.admin_response = response
        message.responded_at = datetime.utcnow()
        message.status = 'replied'
        
        db.session.commit()
        flash('Mesaj başarıyla yanıtlandı.', 'success')
    else:
        flash('Yanıt boş olamaz.', 'error')
    
    return redirect(url_for('admin.messages'))

def create_admin_notification(title, message, notification_type='info', related_message_id=None):
    """Admin bildirimi oluştur"""
    notification = Notification(
        user_id=None,  # Admin bildirimi
        title=title,
        message=message,
        type=notification_type,
        related_message_id=related_message_id
    )
    db.session.add(notification)
    db.session.commit()
    return notification

def create_user_notification(user_id, title, message, notification_type='info', related_message_id=None):
    """Kullanıcı bildirimi oluştur"""
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        type=notification_type,
        related_message_id=related_message_id
    )
    db.session.add(notification)
    db.session.commit()
    return notification

@admin.route('/conversations')
@admin.route('/conversations/<int:conversation_id>')
@login_required
@admin_required
def conversations(conversation_id=None):
    """Admin konuşmaları sayfası"""
    # Tüm konuşmalar
    all_conversations = Conversation.query.order_by(Conversation.updated_at.desc()).all()
    
    # Her konuşma için okunmamış mesaj sayısı (kullanıcı mesajları)
    for conv in all_conversations:
        conv.unread_count = ConversationMessage.query.filter_by(
            conversation_id=conv.id, 
            is_admin=False, 
            is_read=False
        ).count()
    
    # Seçili konuşma
    selected_conversation = None
    if conversation_id:
        selected_conversation = Conversation.query.get_or_404(conversation_id)
        # Kullanıcı mesajlarını okundu işaretle
        ConversationMessage.query.filter_by(
            conversation_id=conversation_id, 
            is_admin=False, 
            is_read=False
        ).update({'is_read': True})
        db.session.commit()
    
    # Form
    message_form = ConversationMessageForm()
    
    return render_template('admin/conversations.html',
                         conversations=all_conversations,
                         selected_conversation=selected_conversation,
                         selected_conversation_id=conversation_id,
                         message_form=message_form)

@admin.route('/conversations/<int:conversation_id>/send', methods=['POST'])
@login_required
@admin_required
def send_message(conversation_id):
    """Admin mesajı gönder"""
    conversation = Conversation.query.get_or_404(conversation_id)
    
    form = ConversationMessageForm()
    if form.validate_on_submit():
        # Yeni admin mesajı ekle
        message = ConversationMessage(
            conversation_id=conversation_id,
            sender_id=None,  # Admin mesajı
            message=form.message.data,
            is_admin=True
        )
        db.session.add(message)
        
        # Conversation güncelleme zamanını ayarla
        conversation.updated_at = datetime.utcnow()
        
        # Kullanıcıya bildirim gönder
        create_user_notification(
            user_id=conversation.user_id,
            title='Yeni Admin Yanıtı',
            message=f'"{conversation.subject}" konuşmasına yeni bir admin yanıtı geldi.',
            notification_type='info',
            related_message_id=conversation.id
        )
        
        db.session.commit()
        flash('Mesaj gönderildi!', 'success')
    
    return redirect(url_for('admin.conversations', conversation_id=conversation_id))

@admin.route('/conversations/<int:conversation_id>/close', methods=['POST'])
@login_required
@admin_required
def close_conversation(conversation_id):
    """Konuşmayı kapat"""
    conversation = Conversation.query.get_or_404(conversation_id)
    conversation.status = 'closed'
    conversation.updated_at = datetime.utcnow()
    
    # Kullanıcıya bildirim gönder
    create_user_notification(
        user_id=conversation.user_id,
        title='Konuşma Kapatıldı',
        message=f'"{conversation.subject}" konuşması admin tarafından kapatıldı.',
        notification_type='warning',
        related_message_id=conversation.id
    )
    
    db.session.commit()
    return jsonify({'success': True})

@admin.route('/conversations/<int:conversation_id>/reopen', methods=['POST'])
@login_required
@admin_required
def reopen_conversation(conversation_id):
    """Konuşmayı yeniden aç"""
    conversation = Conversation.query.get_or_404(conversation_id)
    conversation.status = 'active'
    conversation.updated_at = datetime.utcnow()
    
    # Kullanıcıya bildirim gönder
    create_user_notification(
        user_id=conversation.user_id,
        title='Konuşma Yeniden Açıldı',
        message=f'"{conversation.subject}" konuşması admin tarafından yeniden açıldı.',
        notification_type='success',
        related_message_id=conversation.id
    )
    
    db.session.commit()
    return jsonify({'success': True})

@admin.route('/api/notifications')
@login_required
@admin_required
def api_admin_notifications():
    """Admin bildirimleri API"""
    notifications = Notification.query.filter_by(user_id=None).order_by(Notification.created_at.desc()).limit(20).all()
    unread_count = Notification.query.filter_by(user_id=None, is_read=False).count()
    
    return jsonify({
        'success': True,
        'notifications': [{
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.type,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat()
        } for n in notifications],
        'unread_count': unread_count
    })

@admin.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
@admin_required
def mark_admin_notification_read(notification_id):
    """Admin bildirimini okundu işaretle"""
    notification = Notification.query.filter_by(id=notification_id, user_id=None).first()
    if notification:
        notification.is_read = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Bildirim bulunamadı'})

@admin.route('/api/notifications/mark-all-read', methods=['POST'])
@login_required
@admin_required
def mark_all_admin_notifications_read():
    """Tüm admin bildirimlerini okundu işaretle"""
    Notification.query.filter_by(user_id=None, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})

@admin.route('/api/conversations/unread-count')
@login_required
@admin_required
def api_admin_unread_message_count():
    """Admin için okunmamış mesaj sayısı API"""
    # Tüm konuşmalardaki okunmamış kullanıcı mesajları
    count = ConversationMessage.query.filter_by(is_admin=False, is_read=False).count()
    
    return jsonify({
        'success': True,
        'count': count
    })