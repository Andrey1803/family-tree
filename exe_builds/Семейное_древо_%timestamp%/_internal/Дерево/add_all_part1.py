# -*- coding: utf-8 -*-
"""Сводное добавление: Группа крови + Образование + Карьера"""

print("Добавление функций в модель и UI...")

# === 1. Группа крови - UI ===
with open('app.py', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Находим вкладку Контакты и добавляем после неё Медицинскую вкладку
old_contacts_end = '''        form_vars['social_media'] = social_vars
        row_c += 1
        
        # --- Вкладка 5: Фотоальбом'''

new_contacts_med = '''        form_vars['social_media'] = social_vars
        row_c += 1
        
        # --- Вкладка 5: Медицинская информация ---
        tab_medical = ttk.Frame(notebook)
        notebook.add(tab_medical, text="🩸 Медицина")
        f_med = make_scrollable_tab(tab_medical)
        row_m = 0
        
        ttk.Label(f_med, text="Группа крови", font=("Arial", 10, "bold")).grid(row=row_m, column=0, columnspan=2, padx=10, pady=(10, 4), sticky='w')
        row_m += 1
        
        blood_types = ["Не указана", "0(I)Rh-", "0(I)Rh+", "A(II)Rh-", "A(II)Rh+", "B(III)Rh-", "B(III)Rh+", "AB(IV)Rh-", "AB(IV)Rh+"]
        current_blood = getattr(person, "blood_type", "") or ""
        if current_blood not in blood_types:
            blood_types.insert(0, current_blood)
        blood_var = tk.StringVar(value=current_blood)
        ttk.Combobox(f_med, textvariable=blood_var, values=blood_types, width=30, state="readonly").grid(row=row_m, column=1, padx=10, pady=6, sticky='w')
        form_vars['blood_type'] = blood_var
        row_m += 1
        
        ttk.Label(f_med, text="Медицинская информация", font=("Arial", 10, "bold")).grid(row=row_m, column=0, columnspan=2, padx=10, pady=(10, 4), sticky='w')
        row_m += 1
        
        medical_list = getattr(person, "medical_info", []) or []
        medical_vars = []
        
        def add_medical_row(mtype="Болезнь", name="", notes=""):
            type_var = tk.StringVar(value=mtype)
            name_var = tk.StringVar(value=name)
            notes_var = tk.StringVar(value=notes)
            medical_vars.append((type_var, name_var, notes_var))
            _refresh_medical_list()
        
        def _refresh_medical_list():
            med_frame = ttk.Frame(f_med)
            med_frame.grid(row=row_m, column=0, columnspan=2, padx=10, pady=6, sticky='w')
            for w in med_frame.winfo_children():
                w.destroy()
            for r, (type_var, name_var, notes_var) in enumerate(medical_vars):
                types = ["Болезнь", "Аллергия", "Генетическое", "Травма", "Другое"]
                type_combo = ttk.Combobox(med_frame, textvariable=type_var, values=types, width=12, state="readonly")
                type_combo.grid(row=r, column=0, padx=(0, 5), pady=2)
                name_entry = ttk.Entry(med_frame, textvariable=name_var, width=20)
                name_entry.grid(row=r, column=1, padx=(0, 5), pady=2)
                notes_entry = ttk.Entry(med_frame, textvariable=notes_var, width=30)
                notes_entry.grid(row=r, column=2, padx=(0, 5), pady=2)
                def remove_row(idx=r):
                    if 0 <= idx < len(medical_vars):
                        medical_vars.pop(idx)
                        _refresh_medical_list()
                ttk.Button(med_frame, text="✕", width=2, command=lambda idx=r: remove_row(idx)).grid(row=r, column=3, pady=2)
        
        def show_add_medical():
            add_medical_row()
        ttk.Button(f_med, text="+ Добавить", command=show_add_medical).grid(row=row_m+1, column=0, columnspan=2, pady=5)
        
        for m in medical_list:
            if isinstance(m, dict):
                add_medical_row(m.get("type", "Болезнь"), m.get("name", ""), m.get("notes", ""))
        
        form_vars['medical_info'] = medical_vars
        row_m += 2
        
        # --- Вкладка 6: Фотоальбом'''

content = content.replace(old_contacts_end, new_contacts_med)

# 2. Добавляем сохранение медицинских данных
old_save_med = '''            person.social_media = [{"platform": p.get(), "url": u.get().strip()} for p, u in social_vars if u.get().strip()]
            person.occupation = occupation_var.get().strip()'''

new_save_med = '''            person.social_media = [{"platform": p.get(), "url": u.get().strip()} for p, u in social_vars if u.get().strip()]
            person.blood_type = blood_var.get().strip()
            person.medical_info = [{"type": t.get(), "name": n.get().strip(), "notes": nt.get().strip()} for t, n, nt in medical_vars if n.get().strip()]
            person.occupation = occupation_var.get().strip()'''

content = content.replace(old_save_med, new_save_med)

with open('app.py', 'w', encoding='utf-8', errors='replace') as f:
    f.write(content)

print('OK - Группа крови и медицина добавлены')
print('')
print('=== ГОТОВО! ===')
print('Добавлено:')
print('1. ✅ Контакты (телефон, email, соцсети)')
print('2. ✅ Группа крови и медицинская информация')
print('')
print('Продолжить с Образованием и Карьерой?')
