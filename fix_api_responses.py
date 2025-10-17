"""
API Response Fixer Script
app.py dosyasındaki API yanıtlarını düzeltir
"""

import re

def fix_api_responses():
    """API yanıtlarına success field'ı ekle"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Başarılı yanıtları düzelt (success: True ekle)
    # 'status': 'success' olan yerlere 'success': True ekle
    success_pattern = r"return jsonify\(\{\s*'status': 'success'"
    success_replacement = "return jsonify({\n                'success': True,\n                'status': 'success'"
    content = re.sub(success_pattern, success_replacement, content)
    
    # 2. Hata yanıtlarını düzelt (success: False ekle)
    # 'status': 'error' olan yerlere 'success': False ekle
    error_pattern = r"return jsonify\(\{\s*'status': 'error'"
    error_replacement = "return jsonify({\n                'success': False,\n                'status': 'error'"
    content = re.sub(error_pattern, error_replacement, content)
    
    # 3. Error field'ını da ekle
    # 'message': ile başlayanlara 'error': de ekle
    message_pattern = r"'message': f'([^']+)'"
    def add_error_field(match):
        message = match.group(1)
        return f"'error': f'{message}',\n                'message': f'{message}'"
    content = re.sub(message_pattern, add_error_field, content)
    
    # Backup oluştur
    with open('app_backup.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ API yanıtları düzeltildi!")
    print("📄 Backup dosyası: app_backup.py")
    print("🔧 Değişiklikler:")
    print("   • Başarılı yanıtlara 'success': True eklendi")
    print("   • Hata yanıtlarına 'success': False eklendi") 
    print("   • Hata yanıtlarına 'error' field'ı eklendi")

if __name__ == "__main__":
    fix_api_responses()