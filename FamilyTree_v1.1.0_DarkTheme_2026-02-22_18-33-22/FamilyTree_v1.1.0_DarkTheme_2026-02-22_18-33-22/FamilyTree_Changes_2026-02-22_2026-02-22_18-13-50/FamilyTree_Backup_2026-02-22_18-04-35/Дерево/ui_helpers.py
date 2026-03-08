# -*- coding: utf-8 -*-
"""Вспомогательные функции для построения форм UI."""

import tkinter as tk
from tkinter import ttk


def create_form_fields(parent, fields_config):
    """
    Создаёт поля формы на основе конфигурации.
    fields_config: список кортежей (label, widget_type, default_value, widget_kwargs)
    Возвращает (entries, widgets, last_row).
    """
    entries = {}
    widgets = {}
    row = 0

    for label, widget_type, default_val, kwargs in fields_config:
        ttk.Label(parent, text=label).grid(row=row, column=0, padx=10, pady=8, sticky='e')

        if widget_type == "Entry":
            entry = ttk.Entry(parent, width=30, **kwargs)
            entry.grid(row=row, column=1, padx=10, pady=8, sticky='w')
            entry.insert(0, "" if default_val is None else str(default_val))
            entries[label] = entry

        elif widget_type == "Label":
            lbl = ttk.Label(parent, text=default_val, **kwargs)
            lbl.grid(row=row, column=1, padx=10, pady=8, sticky='w')
            widgets[label] = lbl

        elif widget_type == "Text":
            txt = tk.Text(parent, height=kwargs.get('height', 4), width=kwargs.get('width', 30))
            txt.grid(row=row, column=1, padx=10, pady=8, sticky='w')
            txt.insert("1.0", default_val or "")
            widgets[label] = txt

        elif widget_type == "Radiobutton":
            var = tk.StringVar(value=default_val)
            values = kwargs.get("values", [])
            rb_frame = ttk.Frame(parent)
            rb_frame.grid(row=row, column=1, padx=10, pady=8, sticky='w')
            for i, val in enumerate(values):
                rb = ttk.Radiobutton(rb_frame, text=val, variable=var, value=val)
                rb.grid(row=0, column=i, padx=5, sticky='w')
            widgets[label] = var

        elif widget_type == "Checkbutton":
            var = tk.BooleanVar(value=default_val)
            cb = ttk.Checkbutton(parent, variable=var, **kwargs)
            cb.grid(row=row, column=1, padx=10, pady=8, sticky='w')
            widgets[label] = var

        elif widget_type == "Combobox":
            var = tk.StringVar(value=default_val)
            combo = ttk.Combobox(parent, textvariable=var, values=kwargs.get("values", []),
                                state=kwargs.get("state", "normal"))
            combo.grid(row=row, column=1, padx=10, pady=8, sticky='w')
            if "postcommand" in kwargs:
                combo.bind("<<ComboboxSelected>>", kwargs["postcommand"])
            widgets[label] = var

        elif widget_type == "Spinbox":
            var = tk.StringVar(value=default_val)
            spin = ttk.Spinbox(parent, from_=kwargs.get("from_", 0), to=kwargs.get("to", 100), textvariable=var)
            spin.grid(row=row, column=1, padx=10, pady=8, sticky='w')
            widgets[label] = var

        row += 1

    return entries, widgets, row
