import customtkinter as ctk
from tkinter import messagebox, INSERT, END, font
import re  # Добавлено для более надежной проверки

# Установка внешнего вида CTk
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("dark-blue")

# --- Таблицы лексем (статические) ---
TW = {
    'program': 1, 'int': 2, 'float': 3, 'bool': 4, 'begin': 5, 'end': 6,
    'if': 7, 'else': 8, 'for': 9, 'to': 10, 'step': 11, 'next': 12,
    'while': 13, 'readln': 14, 'writeln': 15, 'true': 16, 'false': 17,
}

# Обновлены ограничители и операции
TL = {
    '{': 1, '}': 2, '!': 3, ',': 4, ';': 5, '==': 6, ':=': 7,
    '&&': 8, '(': 9, ')': 10, '+': 11, '-': 12, '*': 13, '/': 14,
    '||': 15, '!=': 16, '>': 17, '<': 18, '<=': 19, '>=': 20
}

class Scanner:
    def __init__(self):
        self.TW = TW
        # Разделяем TL на одно- и многосимвольные лексемы для конечного автомата
        self.TL_single = {k: v for k, v in TL.items() if
                          len(k) == 1 and k not in ['/', ':', '!', '=', '<', '>', '&', '|']}
        self.TL_multi_prefix = {k: v for k, v in TL.items() if
                                len(k) > 1 or k in ['/', ':', '!', '=', '<', '>', '&', '|']}
        self.TI, self.TN = {}, {}
        self.source_code, self.ptr, self.ch, self.s = "", -1, '', ''
        self.tokens, self.errors = [], []
        # Добавляем таблицу имен для хранения лексем и их кодов
        self.token_names = {1: self.TW, 2: TL, 3: self.TN, 4: self.TI}

    def gc(self):
        self.ptr += 1
        self.ch = self.source_code[self.ptr] if self.ptr < len(self.source_code) else ''

    def peek(self):
        return self.source_code[self.ptr + 1] if self.ptr + 1 < len(self.source_code) else ''

    @staticmethod
    def let(char):
        return char.isalpha() or char == '_'

    @staticmethod
    def digit(char):
        return char.isdigit()

    @staticmethod
    def is_hex_digit(char):
        return char.isdigit() or char.lower() in 'abcdef'

    def nill(self):
        self.s = ''

    def add(self):
        self.s += self.ch

    def look(self, table):
        return table.get(self.s, 0)

    def put(self, table, custom_key=None):
        key = custom_key if custom_key is not None else self.s
        # В TI и TN храним лексему (ключ) и ее порядковый номер (значение)
        if key not in table:
            table[key] = len(table) + 1
        return table[key]

    def out(self, token_class, token_code, lexeme=''):
        """token_class: 1-TW, 2-TL, 3-TN, 4-TI"""
        self.tokens.append({
            'class': token_class,
            'code': token_code,
            'lexeme': lexeme if lexeme else self.s
        })

    def error(self, message):
        # Сохраняем номер позиции, где обнаружена ошибка
        error_pos = self.ptr if self.ch else len(self.source_code)
        error_message = f"Ошибка в позиции {error_pos}: {message}"
        self.errors.append(error_message)
        return 'ER'

    def finalize_with_suffix(self, suffix, base):
        raw_num = self.s[:-len(suffix)]
        full_lexeme = self.s
        try:
            val = int(raw_num, base)
            display_str = f"{full_lexeme} (= {val})"
        except ValueError:
            display_str = f"{full_lexeme} (= ???)"

        z = self.put(self.TN, display_str)
        self.out(3, z, full_lexeme)
        return 'H'

    def finalize_simple_number(self):
        # Десятичное целое без суффикса
        try:
            val = int(self.s)
            display_str = f"{self.s} (= {val})"
        except ValueError:
            display_str = f"{self.s} (= ???)"

        z = self.put(self.TN, display_str)
        self.out(3, z, self.s)
        return 'H'

    def finalize_float(self, cs):
        # Обработка вещественных чисел и чисел с экспонентой
        full_lexeme = self.s
        # Определяем, было ли это число экспоненциальным или дробным
        # Используем eval для корректной обработки экспоненты
        try:
            val = float(full_lexeme.replace('e', 'E'))
            display_str = f"{full_lexeme} (= {val})"
        except ValueError:
            display_str = f"{full_lexeme} (= ???)"

        z = self.put(self.TN, display_str)
        self.out(3, z, full_lexeme)
        return 'H'

    def scan(self, source_code):
        self.source_code = source_code.strip() + ' '  # Добавляем пробел для корректного завершения
        self.ptr, self.s, self.tokens, self.TI, self.TN, self.errors = -1, '', [], {}, {}, []
        self.gc()
        cs = 'H'

        while cs not in ['V', 'ER']:
            if cs == 'H':
                while self.ch.isspace(): self.gc()
                if not self.ch: cs = 'V'; continue
                self.nill()

                if self.let(self.ch):
                    self.add();
                    self.gc();
                    cs = 'I'

                # --- ОБРАБОТКА ЧИСЕЛ ---
                elif self.digit(self.ch):
                    self.add()
                    if self.ch == '0':
                        cs = 'Z'  # Начало с нуля
                    else:
                        cs = 'D'  # Начало с ненулевой цифры
                    self.gc()

                # --- ОБРАБОТКА ДРОБНОЙ ЧАСТИ (.5) ---
                elif self.ch == '.':
                    if self.digit(self.peek()):
                        self.s = '0';
                        self.add();
                        self.gc();
                        cs = 'F'
                    else:
                        self.add();
                        self.out(2, TL['.']);
                        self.gc()

                # --- ОБРАБОТКА ОПЕРАТОРОВ И КОММЕНТАРИЕВ ---
                elif self.ch in self.TL_multi_prefix:
                    # Обработка односимвольных префиксов
                    prefix = self.ch
                    self.add()
                    self.gc()

                    if prefix == '/' and self.ch == '*':  # Комментарий /*
                        self.nill()  # Сбрасываем '/'
                        self.gc();
                        cs = 'C_START'
                    elif prefix == ':' and self.ch == '=':  # :=
                        self.add();
                        self.gc();
                        self.out(2, TL[':=']);
                        cs = 'H'
                    elif prefix == '!' and self.ch == '=':  # !=
                        self.add();
                        self.gc();
                        self.out(2, TL['!=']);
                        cs = 'H'
                    elif prefix == '=' and self.ch == '=':  # ==
                        self.add();
                        self.gc();
                        self.out(2, TL['==']);
                        cs = 'H'
                    elif prefix == '<' and self.ch == '=':  # <=
                        self.add();
                        self.gc();
                        self.out(2, TL['<=']);
                        cs = 'H'
                    elif prefix == '>' and self.ch == '=':  # >=
                        self.add();
                        self.gc();
                        self.out(2, TL['>=']);
                        cs = 'H'
                    elif prefix == '&' and self.ch == '&':  # &&
                        self.add();
                        self.gc();
                        self.out(2, TL['&&']);
                        cs = 'H'
                    elif prefix == '|' and self.ch == '|':  # ||
                        self.add();
                        self.gc();
                        self.out(2, TL['||']);
                        cs = 'H'

                    # Если второй символ не совпал, или это простой оператор
                    elif prefix in ['!', '/', '<', '>']:  # Простые операторы
                        self.out(2, TL[prefix]);
                        cs = 'H'
                    else:
                        # Неизвестный оператор или неполный префикс
                        cs = self.error(f"Неизвестный символ или неполный оператор: '{self.s}'")

                # --- ОБРАБОТКА ОДНОСИМВОЛЬНЫХ ОПЕРАТОРОВ/ОГРАНИЧИТЕЛЕЙ ---
                elif self.ch in self.TL_single:
                    self.add();
                    self.out(2, self.TL_single[self.ch]);
                    self.gc()
                else:
                    cs = self.error(f"Неизвестный символ '{self.ch}'")

            # --- ИДЕНТИФИКАТОРЫ И СЛУЖЕБНЫЕ СЛОВА ---
            elif cs == 'I':
                while self.let(self.ch) or self.digit(self.ch):
                    self.add();
                    self.gc()
                z = self.look(self.TW)
                if z != 0:
                    self.out(1, z, self.s)
                else:
                    z = self.put(self.TI);
                    self.out(4, z, self.s)
                cs = 'H'

            # --- ЦЕЛЫЕ ЧИСЛА И ОСНОВАНИЯ ---
            elif cs == 'Z':  # Число началось с '0'
                if self.ch.lower() == 'x' and self.is_hex_digit(self.peek()):
                    self.add();
                    self.gc();
                    cs = 'H1'  # 0x...
                elif self.ch.lower() == 'b':
                    self.add();
                    self.gc();
                    cs = 'N2'  # 0b...
                elif self.ch.lower() == 'o':
                    self.add();
                    self.gc();
                    cs = 'N8'  # 0o...
                elif self.ch == '.':
                    self.add();
                    self.gc();
                    cs = 'F'
                elif self.digit(self.ch) and self.ch != '0':
                    self.add();
                    self.gc();
                    cs = 'D'
                elif self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E'
                else:
                    cs = self.finalize_simple_number()  # Просто '0'

            elif cs == 'D':  # Число началось с ненулевой цифры
                while self.digit(self.ch): self.add(); self.gc()
                if self.ch == '.':
                    self.add();
                    self.gc();
                    cs = 'F'
                elif self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E'
                elif self.ch.lower() == 'd':
                    self.add();
                    self.gc();
                    cs = 'N10'
                else:
                    cs = self.finalize_simple_number()

            elif cs == 'H1':  # Hex: 0x...
                while self.is_hex_digit(self.ch): self.add(); self.gc()
                cs = self.finalize_with_suffix('h', 16)

            # --- Явное основание (суффиксы b, o, d, h)
            elif cs == 'N2':  # Binary
                while self.ch in '01': self.add(); self.gc()
                cs = self.finalize_with_suffix('b', 2)
            elif cs == 'N8':  # Octal
                while self.ch in '01234567': self.add(); self.gc()
                cs = self.finalize_with_suffix('o', 8)
            elif cs == 'N10':  # Decimal (явный 'd')
                while self.digit(self.ch): self.add(); self.gc()
                cs = self.finalize_with_suffix('d', 10)

            # --- ДРОБНЫЕ И ЭКСПОНЕНТА ---
            elif cs == 'F':  # Дробная часть (напр., 1.2 или 0.5)
                while self.digit(self.ch): self.add(); self.gc()
                if self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E'
                else:
                    cs = self.finalize_float(cs)

            elif cs == 'E':  # Экспонента
                if self.ch in '+-':
                    self.add();
                    self.gc()
                if not self.digit(self.ch):
                    cs = self.error(f"Ожидалась цифра после экспоненты: '{self.s}'")
                    continue
                while self.digit(self.ch):
                    self.add();
                    self.gc()

                cs = self.finalize_float(cs)

            # --- КОММЕНТАРИИ ---
            elif cs == 'C_START':
                comment_closed = False
                while self.ch:
                    if self.ch == '*' and self.peek() == '/':
                        self.gc();  # пропускаем '*'
                        self.gc();  # пропускаем '/'
                        cs = 'H'
                        comment_closed = True
                        break

                    self.gc()

                if not comment_closed:
                    # Позиция ошибки - конец файла
                    self.ptr = len(self.source_code.strip())
                    self.ch = ''
                    cs = self.error("Незакрытый многострочный комментарий в конце файла. Ожидалось '*/'")

                if cs != 'H':
                    continue

        return self.tokens, self.TI, self.TN, self.errors


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лексический анализатор — Модельный язык М")
        self.root.geometry("1100x850")

        # Размещаем виджеты CTk

        # Верхний фрейм (ввод)
        top_frame = ctk.CTkFrame(root, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(top_frame, text="Исходный код:", font=ctk.CTkFont(family="Arial", size=14, weight="bold")).pack(
            anchor="w")

        # Используем ctk.CTkTextbox, так как он более нативен для customtkinter
        self.input_text = ctk.CTkTextbox(top_frame, height=200, wrap="word", font=("Consolas", 12))
        self.input_text.pack(fill="both", expand=True, pady=(5, 10))

        sample_code = """{
writeln 0b101;      /* Двоичное (5) */
writeln 0o10;       /* Восьмеричное (8) */
writeln 20d;        /* Явное Десятичное (20) */
writeln 0x1AF;      /* Шестнадцатеричное (431) */
writeln 123.45e-2;  /* Действительное (1.2345) */
writeln .5;         /* Действительное, начинается с точки (0.5) */
writeln 99;         /* Простое десятичное (99) */
}"""

        self.input_text.insert(INSERT, sample_code)

        # Кнопки
        button_frame = ctk.CTkFrame(root, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkButton(button_frame, text="▶ Анализировать", command=self.analyze, width=150,
                      font=ctk.CTkFont(size=14, weight="bold")).pack(side="left",
                                                                     padx=(0, 10))
        ctk.CTkButton(button_frame, text="Очистить", command=self.clear_all, width=100).pack(side="left")

        # Вкладки
        self.tabview = ctk.CTkTabview(root, height=450)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.tabview.add("Поток Лексем")
        self.tabview.add("Таблицы Лексем")

        # Вкладка "Поток Лексем"
        result_frame = self.tabview.tab("Поток Лексем")
        ctk.CTkLabel(result_frame, text="Коды лексем (Класс, Код):", font=ctk.CTkFont(size=12, weight="bold")).pack(
            anchor="w", pady=(5, 0))
        self.output_text = ctk.CTkTextbox(result_frame, wrap="word", font=("Consolas", 11), state="disabled")
        self.output_text.pack(fill="both", expand=True)

        # Вкладка "Таблицы Лексем"
        tables_frame = self.tabview.tab("Таблицы Лексем")

        top_row = ctk.CTkFrame(tables_frame, fg_color="transparent")
        top_row.pack(fill="x", pady=(5, 10))
        bottom_row = ctk.CTkFrame(tables_frame, fg_color="transparent")
        bottom_row.pack(fill="x")

        self.kw_text = self._create_table(top_row, "1. Служебные слова (TW)")
        self.del_text = self._create_table(top_row, "2. Разделители/Операторы (TL)")
        self.id_text = self._create_table(bottom_row, "4. Идентификаторы (TI)")
        self.num_text = self._create_table(bottom_row, "3. Числа (TN)")

        self.load_static_tables()

    def _create_table(self, parent, title):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=5, pady=(0, 3))
        text_widget = ctk.CTkTextbox(frame, height=180, wrap="word", font=("Consolas", 11), state="disabled")
        text_widget.pack(fill="both", expand=True)
        return text_widget

    def load_static_tables(self):
        # Выводим статические таблицы (TW, TL)
        self._update_text(self.kw_text, self._format_table(TW))
        self._update_text(self.del_text, self._format_table(TL))

    def _format_table(self, table):
        # Форматирование для статических таблиц
        return "\n".join(f"{v:<3}: {k}" for k, v in sorted(table.items(), key=lambda item: item[1]))

    def analyze(self):
        source_code = self.input_text.get("1.0", END)
        if not source_code.strip():
            messagebox.showinfo("Анализ", "Введите исходный код.")
            return

        scanner = Scanner()
        tokens, ti, tn, errs = scanner.scan(source_code)

        output = ""

        # 1. Поток лексем
        if tokens:
            token_list_str = " ".join(f"({t['class']},{t['code']})" for t in tokens)
            # Разбиваем вывод на строки по 5 лексем для читаемости
            formatted_tokens = ""
            parts = token_list_str.split()
            for i, part in enumerate(parts):
                formatted_tokens += part + " "
                if (i + 1) % 5 == 0:
                    formatted_tokens += "\n"
            output = formatted_tokens.strip()
            self._update_text(self.output_text, output)
        else:
            self._update_text(self.output_text, "Нет лексем для вывода.")

        # 2. Таблицы
        # TI (Идентификаторы)
        self._update_text(self.id_text, self._format_dynamic_table(ti))
        # TN (Числа)
        self._update_text(self.num_text, self._format_dynamic_table(tn))

        # 3. Ошибки
        if errs:
            messagebox.showerror("Обнаружены ошибки лексического анализа", "\n".join(errs))
            # Добавляем ошибки в начало потока лексем
            self.output_text.configure(state="normal")
            self.output_text.insert("1.0", "⚠️ ОШИБКИ:\n" + "\n".join(errs) + "\n\n" + "-" * 30 + "\n\n")
            self.output_text.configure(state="disabled")

    def _format_dynamic_table(self, table):
        # Форматирование для динамических таблиц (TI, TN)
        return "\n".join(f"{v:<3}: {k}" for k, v in sorted(table.items(), key=lambda item: item[1]))

    def clear_all(self):
        self.input_text.delete("1.0", END)
        self.input_text.insert(INSERT, """{
/* Введите ваш код здесь */
}""")
        self._update_text(self.output_text, "")
        self._update_text(self.id_text, "")
        self._update_text(self.num_text, "")

    def _update_text(self, widget, content):
        widget.configure(state="normal")
        widget.delete("1.0", END)
        widget.insert("1.0", content)
        widget.configure(state="disabled")


if __name__ == "__main__":
    root = ctk.CTk()
    app = App(root)
    root.mainloop()