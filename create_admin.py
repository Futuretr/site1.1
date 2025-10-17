#!/usr/bin/env python3
from app import app, db, User
from datetime import datetime
from werkzeug.security import generate_password_hash
import secrets

# --- Ayarlar: burayı değiştirebilirsin ---
admin_username = "emir"
admin_email = "emirarslan6116g@gmail.com"
admin_password = "4897Yakup!"   # istersen burayı değiştir
# ----------------------------------------

# Rastgele benzersiz public_id oluştur
public_id = "admin-" + secrets.token_hex(6)

with app.app_context():
    # Şifreyi hashle
    hashed_password = generate_password_hash(admin_password)

    # Eğer aynı email/username zaten varsa önce onu getir
    existing = User.query.filter((User.email == admin_email) | (User.username == admin_username)).first()
    if existing:
        print("Aynı email/username mevcut. Bilgileri güncelleyeceğim.")
        existing.email = admin_email
        existing.username = admin_username
        existing.password_hash = hashed_password
        existing.is_active = True
        existing.is_admin = True
        existing.last_login = datetime.now()
        db.session.commit()
        print(f"Güncellendi: {existing.username} / {existing.email}")
    else:
        # Yeni admin oluştur
        new_admin = User(
            public_id=public_id,
            username=admin_username,
            email=admin_email,
            password_hash=hashed_password,
            is_active=True,
            is_admin=True,
            created_at=datetime.now()
        )
        db.session.add(new_admin)
        db.session.commit()
        print(f"Yeni admin oluşturuldu: {admin_username} / {admin_email}")
        print(f"public_id: {public_id}  şifre: {admin_password}")
