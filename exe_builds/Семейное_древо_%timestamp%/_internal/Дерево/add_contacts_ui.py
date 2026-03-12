# -*- coding: utf-8 -*-
"""Добавление вкладки Контакты в диалог редактирования"""

with open('app.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Находим где создаётся вкладка "Дополнительно" и добавляем перед ней "Контакты"
old_tabs = '''        # --- Вкладка 4: Фотоальбом (доп. фото) — показываем превью фотографии ---
        tab_photos = ttk.Frame(notebook)
        notebook.add(tab_photos, text="Фотоальбом")'''

new_tabs = '''        # --- Вкладка 4: Контакты ---
        tab_contacts = ttk.Frame(notebook)
        notebook.add(tab_contacts, text="📞 Контакты")
        f_cont = make_scrollable_tab(tab_contacts)
        row_c = 0
        
        ttk.Label(f_cont, text="Контактная информация (для живых персон)", font=("Arial", 10, "bold")).grid(row=row_c, column=0, columnspan=2, padx=10, pady=(10, 4), sticky='w')
        row_c += 1
        
        ttk.Label(f_cont, text="Телефон").grid(row=row_c, column=0, padx=10, pady=6, sticky='e')
        phone_var = tk.StringVar(value=getattr(person, "phone", "") or "")
        ttk.Entry(f_cont, textvariable=phone_var, width=32).grid(row=row_c, column=1, padx=10, pady=6, sticky='w')
        form_vars['phone'] = phone_var
        row_c += 1
        
        ttk.Label(f_cont, text="Email").grid(row=row_c, column=0, padx=10, pady=6, sticky='e')
        email_var = tk.StringVar(value=getattr(person, "email", "") or "")
        ttk.Entry(f_cont, textvariable=email_var, width=32).grid(row=row_c, column=1, padx=10, pady=6, sticky='w')
        form_vars['email'] = email_var
        row_c += 1
        
        ttk.Label(f_cont, text="Соцсети").grid(row=row_c, column=0, padx=10, pady=6, sticky='e')
        social_frame = ttk.Frame(f_cont)
        social_frame.grid(row=row_c, column=1, padx=10, pady=6, sticky='w')
        
        # Список соцсетей
        social_list = getattr(person, "social_media", []) or []
        social_vars = []
        
        def add_social_row(platform="", url=""):
            plat_var = tk.StringVar(value=platform)
            url_var = tk.StringVar(value=url)
            social_vars.append((plat_var, url_var))
            _refresh_social_list()
        
        def _refresh_social_list():
            for w in social_frame.winfo_children():
                w.destroy()
            for r, (plat_var, url_var) in enumerate(social_vars):
                platforms = ["VK", "Telegram", "WhatsApp", "Viber", "Instagram", "Facebook", "Другое"]
                plat_combo = ttk.Combobox(social_frame, textvariable=plat_var, values=platforms, width=12, state="readonly")
                plat_combo.grid(row=r, column=0, padx=(0, 5), pady=2)
                url_entry = ttk.Entry(social_frame, textvariable=url_var, width=30)
                url_entry.grid(row=r, column=1, padx=(0, 5), pady=2)
                def remove_row(idx=r):
                    if 0 <= idx < len(social_vars):
                        social_vars.pop(idx)
                        _refresh_social_list()
                ttk.Button(social_frame, text="✕", width=2, command=lambda idx=r: remove_row(idx)).grid(row=r, column=2, pady=2)
        
        # Кнопка добавления
        def show_add_social():
            add_social_row()
        ttk.Button(social_frame, text="+ Добавить", command=show_add_social).grid(row=len(social_vars), column=0, columnspan=3, pady=5)
        
        # Загружаем существующие
        for s in social_list:
            if isinstance(s, dict):
                add_social_row(s.get("platform", ""), s.get("url", ""))
        
        form_vars['social_media'] = social_vars
        row_c += 1
        
        # --- Вкладка 5: Фотоальбом (доп. фото) — показываем превью фотографии ---
        tab_photos = ttk.Frame(notebook)
        notebook.add(tab_photos, text="Фотоальбом")'''

content = content.replace(old_tabs, new_tabs)

# 2. Добавляем сохранение контактов в submit_edit
old_save = '''            person.photo_album = [v.get().strip() for v in album_vars if v.get().strip()]
            person.links = [{"title": t.get().strip(), "url": u.get().strip()} for t, u in links_vars if u.get().strip()]
            person.occupation = occupation_var.get().strip()'''

new_save = '''            person.photo_album = [v.get().strip() for v in album_vars if v.get().strip()]
            person.links = [{"title": t.get().strip(), "url": u.get().strip()} for t, u in links_vars if u.get().strip()]
            person.phone = phone_var.get().strip()
            person.email = email_var.get().strip()
            person.social_media = [{"platform": p.get(), "url": u.get().strip()} for p, u in social_vars if u.get().strip()]
            person.occupation = occupation_var.get().strip()'''

content = content.replace(old_save, new_save)

with open('app.py', 'w', encoding='utf-8', errors='replace') as f:
    f.write(content)

print('OK - Вкладка Контакты добавлена')
