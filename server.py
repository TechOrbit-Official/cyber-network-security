from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_it_123!@#'

# --- ملف JSON لتخزين البيانات ---
CONFIG_FILE = 'site_config.json'

# بيانات افتراضية مع إعدادات التصميم المتطورة
DEFAULT_CONFIG = {
    "site_name": "شبكتي الذكية",
    "site_title": "مرحبا بكم في شبكة المنزل",
    "site_language": "ar",
    "network_name": "MyHomeWiFi",
    "network_password": "P@ssw0rd123",
    "network_security": "WPA2-PSK",
    "network_hidden": False,
    
    # إعدادات التصميم المتطورة
    "theme": {
        "primary_color": "#00ff88",
        "secondary_color": "#ff3366",
        "bg_color": "#0a0a0a",
        "card_bg": "#1a1a1a",
        "text_color": "#ffffff",
        "accent_color": "#00ccff",
        "font_family": "'Cairo', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        "border_radius": "12px",
        "animation_speed": "0.3s",
        "glow_effect": True,
        "glass_morphism": False,
        "cyberpunk_mode": False,
        "particles_effect": True,
        "font_size": "16px",
        "card_opacity": "1",
        "border_width": "2px",
        "shadow_intensity": "20px"
    },
    
    "devices": []
}

def load_config():
    """تحميل الإعدادات من ملف JSON"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # التأكد من وجود كل إعدادات التصميم
                if "theme" not in config:
                    config["theme"] = DEFAULT_CONFIG["theme"]
                else:
                    # إضافة أي إعدادات جديدة للموضوع
                    for key, value in DEFAULT_CONFIG["theme"].items():
                        if key not in config["theme"]:
                            config["theme"][key] = value
                return config
        except Exception as e:
            print(f"خطأ في تحميل الملف: {e}")
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """حفظ الإعدادات في ملف JSON"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"خطأ في حفظ الملف: {e}")
        return False

# تحميل الإعدادات
site_config = load_config()

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    global site_config
    
    # تسجيل الجهاز الزائر
    visitor_ip = request.remote_addr
    visitor_name = request.headers.get('User-Agent', 'جهاز غير معروف')[:50]
    visitor_mac = str(uuid.uuid4()).replace('-', '')[:12].upper()  # MAC وهمي
    
    # تحديد نوع الجهاز بشكل أفضل
    ua = request.headers.get('User-Agent', '').lower()
    if 'android' in ua:
        visitor_name = '📱 جهاز أندرويد'
    elif 'iphone' in ua or 'ipad' in ua:
        visitor_name = '🍎 جهاز آيفون/آيباد'
    elif 'windows' in ua:
        visitor_name = '💻 جهاز ويندوز'
    elif 'linux' in ua:
        visitor_name = '🐧 جهاز لينكس'
    elif 'mac' in ua:
        visitor_name = '🍏 جهاز ماك'
    else:
        visitor_name = '🌐 جهاز غير معروف'
    
    # التحقق من وجود الجهاز
    device_found = False
    for device in site_config['devices']:
        if device['ip'] == visitor_ip and device['name'] == visitor_name:
            device_found = True
            device['last_seen'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            device['status'] = 'active'
            save_config(site_config)
            break
    
    if not device_found:
        new_device = {
            "id": str(uuid.uuid4())[:8],
            "name": visitor_name,
            "ip": visitor_ip,
            "mac": visitor_mac,
            "status": "active",
            "first_seen": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "last_seen": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "visits": 1
        }
        site_config['devices'].append(new_device)
        save_config(site_config)
    
    return render_template('index.html', config=site_config, now=datetime.now)

@app.route('/dashboard')
def dashboard():
    """لوحة التحكم الرئيسية"""
    return render_template('dashboard.html', config=site_config, now=datetime.now)

@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    """API إحصائيات Dashboard"""
    total_devices = len(site_config['devices'])
    active_devices = sum(1 for d in site_config['devices'] if d.get('status') == 'active')
    today_visits = sum(1 for d in site_config['devices'] if d.get('last_seen', '').startswith(datetime.now().strftime('%Y-%m-%d')))
    
    return jsonify({
        'success': True,
        'stats': {
            'total_devices': total_devices,
            'active_devices': active_devices,
            'today_visits': today_visits,
            'network_name': site_config['network_name'],
            'security_type': site_config['network_security']
        }
    })

@app.route('/api/dashboard/devices')
def api_dashboard_devices():
    """API قائمة الأجهزة"""
    return jsonify({
        'success': True,
        'devices': site_config['devices']
    })

@app.route('/api/dashboard/theme')
def api_dashboard_theme():
    """API إعدادات التصميم"""
    return jsonify({
        'success': True,
        'theme': site_config['theme']
    })

@app.route('/update_settings', methods=['POST'])
def update_settings():
    """تحديث الإعدادات"""
    global site_config
    try:
        # التحقق من وجود البيانات المطلوبة
        required_fields = ['site_name', 'site_title', 'site_language', 'network_name', 
                          'network_password', 'network_security']
        
        for field in required_fields:
            if field not in request.form:
                flash(f'الحقل {field} مطلوب!', 'error')
                return redirect(url_for('dashboard'))
        
        # تحديث الإعدادات الأساسية
        site_config["site_name"] = request.form['site_name']
        site_config["site_title"] = request.form['site_title']
        site_config["site_language"] = request.form['site_language']
        site_config["network_name"] = request.form['network_name']
        site_config["network_password"] = request.form['network_password']
        site_config["network_security"] = request.form['network_security']
        site_config["network_hidden"] = 'network_hidden' in request.form
        
        # تحديث إعدادات التصميم إذا وجدت
        theme_fields = ['primary_color', 'secondary_color', 'bg_color', 'card_bg', 
                       'text_color', 'accent_color', 'border_radius', 'animation_speed',
                       'font_size', 'border_width', 'shadow_intensity']
        
        for field in theme_fields:
            if field in request.form:
                site_config["theme"][field] = request.form[field]
        
        # تحديث الـ checkboxes
        site_config["theme"]["glow_effect"] = 'glow_effect' in request.form
        site_config["theme"]["glass_morphism"] = 'glass_morphism' in request.form
        site_config["theme"]["cyberpunk_mode"] = 'cyberpunk_mode' in request.form
        site_config["theme"]["particles_effect"] = 'particles_effect' in request.form
        
        # حفظ التغييرات
        if save_config(site_config):
            flash('✅ تم تحديث جميع الإعدادات بنجاح!', 'success')
        else:
            flash('❌ حدث خطأ أثناء حفظ الإعدادات', 'error')
            
    except Exception as e:
        flash(f'❌ حدث خطأ: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/add_device', methods=['POST'])
def add_device():
    """إضافة جهاز جديد"""
    global site_config
    
    try:
        device_name = request.form['device_name']
        device_ip = request.form['device_ip']
        device_mac = request.form['device_mac']
        device_status = request.form['device_status']
        
        # التحقق من البيانات
        if not all([device_name, device_ip, device_mac]):
            flash('❌ جميع الحقول مطلوبة!', 'error')
            return redirect(url_for('dashboard'))
        
        # التحقق من عدم التكرار
        device_exists = False
        for device in site_config['devices']:
            if device['ip'] == device_ip:
                device_exists = True
                flash('⚠️ جهاز بنفس IP موجود بالفعل!', 'error')
                break
        
        if not device_exists:
            new_device = {
                "id": str(uuid.uuid4())[:8],
                "name": device_name,
                "ip": device_ip,
                "mac": device_mac.upper(),
                "status": device_status,
                "added_manually": True,
                "added_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "first_seen": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "last_seen": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            site_config["devices"].append(new_device)
            save_config(site_config)
            flash('✅ تم إضافة الجهاز بنجاح!', 'success')
        
    except Exception as e:
        flash(f'❌ خطأ: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/delete_device/<device_id>')
def delete_device(device_id):
    """حذف جهاز"""
    global site_config
    try:
        for i, device in enumerate(site_config['devices']):
            if device.get('id') == device_id:
                device_name = device['name']
                del site_config['devices'][i]
                save_config(site_config)
                flash(f'✅ تم حذف {device_name} بنجاح!', 'success')
                break
        else:
            flash('❌ الجهاز غير موجود!', 'error')
            
    except Exception as e:
        flash(f'❌ خطأ: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/api/device/<device_id>/toggle', methods=['POST'])
def toggle_device(device_id):
    """تغيير حالة الجهاز"""
    global site_config
    try:
        for device in site_config['devices']:
            if device.get('id') == device_id:
                device['status'] = 'inactive' if device['status'] == 'active' else 'active'
                save_config(site_config)
                return jsonify({'success': True, 'status': device['status']})
        
        return jsonify({'success': False, 'error': 'Device not found'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.template_filter('now')
def now_filter(format_string):
    """فلتر لعرض الوقت الحالي"""
    return datetime.now().strftime(format_string)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)