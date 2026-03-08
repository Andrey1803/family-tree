# -*- coding: utf-8 -*-
"""Тест подключения к серверу синхронизации"""

import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import urllib.error
import json

SYNC_URL = "https://ravishing-caring-production-3656.up.railway.app"


def test_connection():
    """Проверяет подключение к серверу"""
    root = tk.Tk()
    root.title("🔌 Тест подключения к серверу")
    root.geometry("700x500")
    
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # Заголовок
    ttk.Label(main_frame, text="🔌 Тест подключения к серверу", 
              font=('Segoe UI', 16, 'bold')).pack(pady=(0, 20))
    
    # Текстовое поле для логов
    log_text = tk.Text(main_frame, wrap=tk.WORD, font=('Consolas', 10), height=20)
    log_text.pack(fill=tk.BOTH, expand=True, pady=10)
    
    def log(message, status="info"):
        colors = {
            "info": "#2c3e50",
            "success": "#27ae60",
            "error": "#e74c3c",
            "warning": "#e67e22"
        }
        log_text.insert(tk.END, message + "\n")
        log_text.tag_add(status, "end-2c", "end-1c")
        log_text.tag_config(status, foreground=colors.get(status, "#2c3e50"))
        log_text.see(tk.END)
    
    def run_tests():
        log_text.delete(1.0, tk.END)
        log("=== Начало тестирования ===", "info")
        
        # Тест 1: Доступность сервера
        log("\n1️⃣ Проверка доступности сервера...", "info")
        try:
            req = urllib.request.Request(SYNC_URL, method='GET')
            with urllib.request.urlopen(req, timeout=10) as response:
                log(f"   ✅ Сервер доступен: {SYNC_URL}", "success")
                log(f"   HTTP Status: {response.status}", "info")
        except urllib.error.URLError as e:
            log(f"   ❌ Сервер недоступен: {e.reason}", "error")
            return
        except Exception as e:
            log(f"   ❌ Ошибка: {type(e).__name__}: {e}", "error")
            return
        
        # Тест 2: API Health
        log("\n2️⃣ Проверка API /api/health...", "info")
        try:
            req = urllib.request.Request(f"{SYNC_URL}/api/health", method='GET')
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                log(f"   ✅ API Health работает", "success")
                log(f"   Ответ: {data}", "info")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                log(f"   ⚠️ Endpoint /api/health не найден (404)", "warning")
            else:
                log(f"   ❌ HTTP Error: {e.code}", "error")
        except Exception as e:
            log(f"   ❌ Ошибка: {type(e).__name__}: {e}", "error")
        
        # Тест 3: Авторизация
        log("\n3️⃣ Проверка авторизации...", "info")
        log("   Введите тестовые данные:", "info")
        
        # Диалог для ввода
        dialog = tk.Toplevel(root)
        dialog.title("Ввод данных")
        dialog.transient(root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Логин:").pack(pady=5)
        login_var = tk.StringVar(value="Андрей Емельянов")
        ttk.Entry(dialog, textvariable=login_var, width=30).pack(pady=5)
        
        ttk.Label(dialog, text="Пароль:").pack(pady=5)
        password_var = tk.StringVar()
        ttk.Entry(dialog, textvariable=password_var, show="•", width=30).pack(pady=5)
        
        test_result = {"done": False}
        
        def do_test_auth():
            login = login_var.get()
            password = password_var.get()
            
            if not login or not password:
                messagebox.showwarning("Внимание", "Введите логин и пароль")
                return
            
            log(f"\n   Тест авторизации для: {login}", "info")
            
            try:
                req = urllib.request.Request(
                    f"{SYNC_URL}/api/auth/login",
                    data=json.dumps({"login": login, "password": password}).encode(),
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    
                    if data.get('token'):
                        log(f"   ✅ Авторизация успешна!", "success")
                        log(f"   Token: {data['token'][:20]}...", "info")
                        
                        # Тест 4: Получение данных пользователя
                        log("\n4️⃣ Получение данных пользователя...", "info")
                        headers = {'Authorization': f'Bearer {data["token"]}'}
                        
                        try:
                            req = urllib.request.Request(
                                f"{SYNC_URL}/api/user/stats",
                                headers=headers,
                                method='GET'
                            )
                            with urllib.request.urlopen(req, timeout=10) as resp:
                                user_data = json.loads(resp.read().decode())
                                log(f"   ✅ Данные получены", "success")
                                log(f"   {json.dumps(user_data, indent=2, ensure_ascii=False)}", "info")
                        except Exception as e:
                            log(f"   ⚠️ Не удалось получить данные: {e}", "warning")
                    else:
                        log(f"   ⚠️ Token не получен", "warning")
                        
            except urllib.error.HTTPError as e:
                error_msg = f"HTTP {e.code}"
                try:
                    error_data = json.loads(e.read().decode())
                    error_msg += f": {error_data.get('error', 'Unknown')}"
                except:
                    pass
                log(f"   ❌ Ошибка авторизации: {error_msg}", "error")
            except Exception as e:
                log(f"   ❌ Ошибка: {type(e).__name__}: {e}", "error")
            
            test_result["done"] = True
            dialog.destroy()
        
        ttk.Button(dialog, text="Тестировать", command=do_test_auth).pack(pady=10)
        ttk.Button(dialog, text="Отмена", command=dialog.destroy).pack(pady=5)
        
        root.wait_window(dialog)
        
        if test_result["done"]:
            log("\n=== Тестирование завершено ===", "info")
    
    # Кнопки
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill=tk.X)
    
    ttk.Button(btn_frame, text="🔄 Запустить тесты", command=run_tests).pack(side=tk.LEFT)
    ttk.Button(btn_frame, text="❌ Закрыть", command=root.destroy).pack(side=tk.RIGHT)
    
    # Автозапуск
    root.after(500, run_tests)
    
    root.mainloop()


if __name__ == "__main__":
    test_connection()
