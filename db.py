import sqlite3
import json
from datetime import datetime

def init_database():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    # جدول الإعدادات والخدمات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            service_name TEXT UNIQUE,
            access_token TEXT,
            refresh_token TEXT,
            status BOOLEAN DEFAULT 0,
            config TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول الصفحات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY,
            page_id TEXT UNIQUE,
            page_name TEXT,
            access_token TEXT,
            status BOOLEAN DEFAULT 1,
            welcome_message TEXT,
            welcome_buttons TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول المنشورات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            post_id TEXT UNIQUE,
            page_id TEXT,
            message TEXT,
            created_time TIMESTAMP,
            auto_reply TEXT,
            auto_buttons TEXT,
            dm_message TEXT,
            status BOOLEAN DEFAULT 1,
            FOREIGN KEY (page_id) REFERENCES pages (page_id)
        )
    ''')
    
    # جدول التعليقات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY,
            comment_id TEXT UNIQUE,
            post_id TEXT,
            user_id TEXT,
            user_name TEXT,
            message TEXT,
            reply_text TEXT,
            status TEXT DEFAULT 'pending',
            created_time TIMESTAMP,
            replied_at TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts (post_id)
        )
    ''')
    
    # جدول الرسائل
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inbox (
            id INTEGER PRIMARY KEY,
            message_id TEXT UNIQUE,
            user_id TEXT,
            user_name TEXT,
            page_id TEXT,
            message TEXT,
            reply_text TEXT,
            status TEXT DEFAULT 'pending',
            created_time TIMESTAMP,
            replied_at TIMESTAMP,
            FOREIGN KEY (page_id) REFERENCES pages (page_id)
        )
    ''')
    
    # جدول الطلبات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            order_id TEXT UNIQUE,
            customer_name TEXT,
            customer_phone TEXT,
            product TEXT,
            quantity INTEGER,
            status TEXT DEFAULT 'new',
            agent_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول المناديب
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY,
            agent_id TEXT UNIQUE,
            name TEXT,
            phone TEXT,
            email TEXT,
            password TEXT,
            status BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول السجلات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY,
            level TEXT,
            message TEXT,
            service TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول التقارير
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY,
            report_type TEXT,
            title TEXT,
            content TEXT,
            recipients TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            sent_at TIMESTAMP
        )
    ''')
    
    # جدول منتجات Shopify
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shopify_products (
            id INTEGER PRIMARY KEY,
            product_id TEXT UNIQUE,
            title TEXT,
            description TEXT,
            price TEXT,
            category TEXT,
            image_url TEXT,
            availability BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # إدخال الإعدادات الافتراضية
    default_settings = [
        ('facebook', '', '', 0, '{}'),
        ('whatsapp', '', '', 0, '{}'),
        ('googlesheet', '', '', 0, '{}'),
        ('openai', '', '', 0, '{}'),
        ('deepseek', '', '', 0, '{}')
    ]
    
    for service, token, refresh, status, config in default_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO settings (service_name, access_token, refresh_token, status, config)
            VALUES (?, ?, ?, ?, ?)
        ''', (service, token, refresh, status, config))
    
    conn.commit()
    conn.close()

def get_service_status(service_name):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT status FROM settings WHERE service_name = ?', (service_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else False

def update_service_status(service_name, status):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE settings SET status = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE service_name = ?
    ''', (status, service_name))
    conn.commit()
    conn.close()

def save_service_token(service_name, access_token, refresh_token=''):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE settings SET access_token = ?, refresh_token = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE service_name = ?
    ''', (access_token, refresh_token, service_name))
    conn.commit()
    conn.close()

def get_service_token(service_name):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT access_token FROM settings WHERE service_name = ?', (service_name,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def add_log(level, message, service='', details=''):
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs (level, message, service, details)
        VALUES (?, ?, ?, ?)
    ''', (level, message, service, details))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_database()
    print("Database initialized successfully!")