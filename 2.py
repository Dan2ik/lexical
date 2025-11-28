import tkinter as tk
from tkinter import scrolledtext, messagebox, font

# --- Таблицы лексем (статические) ---

TW = {
    'program': 1, 'var': 2, 'begin': 3, 'end': 4, 'as': 5, 'for': 6,
    'to': 7, 'read': 8, 'write': 9, 'if': 10, 'then': 11, 'else': 12,
    'while': 13, 'do': 14, 'true': 15, 'false': 16, 'NE': 17, 'EQ': 18,
    'LT': 19, 'LE': 20, 'GT': 21, 'GE': 22, 'plus': 23, 'min': 24,
    'or': 25, 'mult': 26, 'div': 27, 'and': 28
}

TL = {
    '(': 1, ')': 2, ',': 3, ';': 4, '{': 5, '}': 6,
    '/': 7, '~': 8, '[': 9, ']': 10, '.': 11,
    '%': 12,  # Целый
    '!': 13,  # Действительный
    '$': 14, # Логический
    ':': 15  # Двоеточие
}


class Scanner:
    def __init__(self):
        self.TW = TW
        self.TL = TL
        self.TI, self.TN = {}, {}
        self.source_code, self.ptr, self.ch, self.s = "", -1, '', ''
        self.tokens, self.errors = [], []

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
    def is_hex_letter(char):
        return char.lower() in 'abcdef'

    def nill(self):
        self.s = ''

    def add(self):
        self.s += self.ch

    def look(self, table):
        return table.get(self.s, 0)

    def put(self, table, custom_key=None):
        key = custom_key if custom_key is not None else self.s
        if key not in table:
            table[key] = len(table) + 1
        return table[key]

    def out(self, n, k):
        self.tokens.append((n, k))

    def error(self, message):
        error_message = f"Ошибка на позиции {self.ptr} ('{self.ch}'): {message}"
        self.errors.append(error_message)
        return 'ER'

    def finalize_with_suffix(self, suffix, base):
        raw = self.s
        self.s += suffix
        try:
            val = int(raw, base)
            display_str = f"{self.s} (= {val})"
        except ValueError:
            display_str = f"{self.s} (= ???)"

        z = self.put(self.TN, display_str)
        self.out(3, z)
        return 'H'

    def finalize_simple_decimal(self):
        z = self.put(self.TN, f"{self.s} (= {self.s})")
        self.out(3, z)
        return 'H'

    def scan(self, source_code):
        self.source_code = source_code
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
                elif self.digit(self.ch):
                    self.add()
                    if '0' <= self.ch <= '1':
                        cs = 'N2'
                    elif '2' <= self.ch <= '7':
                        cs = 'N8'
                    else:
                        cs = 'N10'
                    self.gc()
                elif self.ch == '.':
                    if self.digit(self.peek()):
                        # Начинаем с точки - добавляем ведущий ноль
                        self.s = '0'  # Добавляем ведущий ноль
                        self.add()  # Добавляем точку
                        self.gc();
                        cs = 'P1'
                    else:
                        self.add();
                        self.out(2, self.TL['.']);
                        self.gc()
                elif self.ch == '{':
                    self.gc();
                    cs = 'C1'
                elif self.ch in self.TL:
                    self.add();
                    self.out(2, self.TL[self.ch]);
                    self.gc()
                else:
                    cs = self.error(f"Неизвестный символ '{self.ch}'")

            elif cs == 'I':
                while self.let(self.ch) or self.digit(self.ch):
                    self.add();
                    self.gc()
                z = self.look(self.TW)
                if z != 0:
                    self.out(1, z)
                else:
                    z = self.put(self.TI);
                    self.out(4, z)
                cs = 'H'

            # --- ЦЕЛЫЕ ЧИСЛА ---
            elif cs == 'N2':
                if self.ch.lower() == 'b':
                    nxt = self.peek()
                    if (nxt not in ['1', '2', '3', '4', '5', '6', '7', '8', '9'] and
                            nxt.lower() not in ['a', 'b', 'c', 'd', 'e', 'f', 'h']):
                        self.gc();
                        cs = 'B'
                    elif nxt.lower() == 'h':
                        self.gc();
                        cs = 'HX'
                    else:
                        self.add();
                        self.gc();
                        cs = 'N16'
                elif self.ch.lower() == 'o':
                    self.gc();
                    cs = 'O'
                elif self.ch.lower() == 'd':
                    nxt = self.peek()
                    if (nxt not in ['1', '2', '3', '4', '5', '6', '7', '8', '9'] and
                            nxt.lower() not in ['a', 'b', 'c', 'd', 'e', 'f']):
                        self.gc();
                        cs = 'D'
                    elif nxt.lower() == 'h':
                        self.gc();
                        cs = 'HX'
                    else:
                        self.add();
                        self.gc();
                        cs = 'N16'
                elif self.ch.lower() == 'h':
                    self.gc();
                    cs = 'HX'

                # Приоритет проверки на экспоненту (e+, e-, e1) перед Hex
                elif self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E11'

                elif self.ch in '01':
                    self.add();
                    self.gc()
                elif '2' <= self.ch <= '7':
                    self.add();
                    self.gc();
                    cs = 'N8'
                elif self.ch in '89':
                    self.add();
                    self.gc();
                    cs = 'N10'
                elif self.is_hex_letter(self.ch):
                    self.add();
                    self.gc();
                    cs = 'N16'
                elif self.ch == '.':
                    self.add();
                    self.gc();
                    cs = 'P2'
                else:
                    cs = self.finalize_simple_decimal()

            elif cs == 'N8':
                if self.ch.lower() == 'o':
                    self.gc();
                    cs = 'O'
                elif self.ch.lower() == 'd':
                    nxt = self.peek()
                    if (nxt not in ['1', '2', '3', '4', '5', '6', '7', '8', '9'] and
                            nxt.lower() not in ['a', 'b', 'c', 'd', 'e', 'f']):
                        self.gc();
                        cs = 'D'
                    elif nxt.lower() == 'h':
                        self.gc();
                        cs = 'HX'
                    else:
                        self.add();
                        self.gc();
                        cs = 'N16'
                elif self.ch.lower() == 'h':
                    self.gc();
                    cs = 'HX'

                # Приоритет проверки на экспоненту
                elif self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E11'

                elif '0' <= self.ch <= '7':
                    self.add();
                    self.gc()
                elif self.ch in '89':
                    self.add();
                    self.gc();
                    cs = 'N10'
                elif self.is_hex_letter(self.ch):
                    self.add();
                    self.gc();
                    cs = 'N16'
                elif self.ch == '.':
                    self.add();
                    self.gc();
                    cs = 'P2'
                else:
                    cs = self.finalize_simple_decimal()

            elif cs == 'N10':
                if self.ch.lower() == 'o':
                    cs = self.error("Цифра > 7 в восьмеричном числе.")
                elif self.ch.lower() == 'd':
                    nxt = self.peek()
                    if (nxt not in ['1', '2', '3', '4', '5', '6', '7', '8', '9'] and
                            nxt.lower() not in ['a', 'b', 'c', 'd', 'e', 'f']):
                        self.gc();
                        cs = 'D'
                    elif nxt.lower() == 'h':
                        self.gc();
                        cs = 'HX'
                    else:
                        self.add();
                        self.gc();
                        cs = 'N16'
                elif self.ch.lower() == 'h':
                    self.gc();
                    cs = 'HX'

                # Приоритет проверки на экспоненту (ВАЖНО для 1.2e-5)
                elif self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E11'

                elif self.digit(self.ch):
                    self.add();
                    self.gc()
                elif self.is_hex_letter(self.ch):
                    self.add();
                    self.gc();
                    cs = 'N16'
                elif self.ch == '.':
                    self.add();
                    self.gc();
                    cs = 'P2'
                else:
                    cs = self.finalize_simple_decimal()

            elif cs == 'N16':
                if self.digit(self.ch) or self.is_hex_letter(self.ch):
                    self.add();
                    self.gc()
                elif self.ch.lower() == 'h':
                    self.gc();
                    cs = 'HX'
                else:
                    cs = self.error(f"Недопустимый символ '{self.ch}' в Hex числе.")

            elif cs == 'B':
                cs = self.finalize_with_suffix('b', 2)
            elif cs == 'O':
                cs = self.finalize_with_suffix('o', 8)
            elif cs == 'D':
                cs = self.finalize_with_suffix('d', 10)
            elif cs == 'HX':
                cs = self.finalize_with_suffix('h', 16)

            # --- ВЕЩЕСТВЕННЫЕ ЧИСЛА ---
            elif cs == 'P1':
                if self.digit(self.ch):
                    self.add();
                    self.gc();
                    cs = 'P2'
                else:
                    cs = self.error("После '.' ожидалась цифра.")
            elif cs == 'P2':
                while self.digit(self.ch): self.add(); self.gc()
                if self.ch.lower() == 'e':
                    self.add();
                    self.gc();
                    cs = 'E21'
                else:
                    # Для чисел вида .5 преобразуем в 0.5 для корректного отображения
                    normalized = self.s
                    if normalized.startswith('0.'):
                        pass  # Уже нормализовано
                    elif normalized.startswith('.'):
                        normalized = '0' + normalized  # Добавляем ведущий ноль

                    z = self.put(self.TN, f"{self.s} (= {normalized})")
                    self.out(3, z)
                    cs = 'H'

            # --- ЭКСПОНЕНЦИАЛЬНАЯ ФОРМА ---
            elif cs == 'E11':
                if self.ch in '+-':
                    self.add();
                    self.gc();
                    cs = 'ZN'
                elif self.digit(self.ch):
                    self.add();
                    self.gc();
                    cs = 'E12'
                else:
                    cs = self.error(f"Ожидался знак '+'/'-' или цифра после 'e' в числе '{self.s}'")

            elif cs == 'E21':
                if self.ch in '+-':
                    self.add();
                    self.gc();
                    cs = 'ZN'
                elif self.digit(self.ch):
                    self.add();
                    self.gc();
                    cs = 'E22'
                else:
                    cs = self.error(f"Ожидался знак '+'/'-' или цифра после 'e' в числе '{self.s}'")

            elif cs == 'ZN':
                if self.digit(self.ch):
                    self.add();
                    self.gc();
                    cs = 'E13'
                else:
                    cs = self.error(f"Ожидалась цифра после знака экспоненты в числе '{self.s}'")

            elif cs == 'E12':
                while self.digit(self.ch): self.add(); self.gc()
                if self.let(self.ch) or self.ch == '.':
                    cs = self.error(f"Недопустимый символ '{self.ch}' после экспоненты в числе '{self.s}'")
                else:
                    try:
                        computed_value = str(eval(self.s.replace('e', 'E')))
                        display_value = f"{self.s} (= {computed_value})"
                    except:
                        display_value = f"{self.s} (= ???)"
                    z = self.put(self.TN, display_value)
                    self.out(3, z)
                    cs = 'H'

            elif cs == 'E13':
                while self.digit(self.ch): self.add(); self.gc()
                if self.let(self.ch) or self.ch == '.':
                    cs = self.error(f"Недопустимый символ '{self.ch}' после экспоненты в числе '{self.s}'")
                else:
                    try:
                        computed_value = str(eval(self.s.replace('e', 'E')))
                        display_value = f"{self.s} (= {computed_value})"
                    except:
                        display_value = f"{self.s} (= ???)"
                    z = self.put(self.TN, display_value)
                    self.out(3, z)
                    cs = 'H'

            elif cs == 'E22':
                while self.digit(self.ch): self.add(); self.gc()
                if self.let(self.ch) or self.ch == '.':
                    cs = self.error(f"Недопустимый символ '{self.ch}' после экспоненты в числе '{self.s}'")
                else:
                    # Нормализуем числа вида .5e1 в 0.5e1
                    normalized = self.s
                    if normalized.startswith('0.'):
                        pass  # Уже нормализовано
                    elif normalized.startswith('.'):
                        normalized = '0' + normalized  # Добавляем ведущий ноль

                    try:
                        computed_value = str(eval(normalized.replace('e', 'E')))
                        display_value = f"{self.s} (= {computed_value})"
                    except:
                        display_value = f"{self.s} (= ???)"
                    z = self.put(self.TN, display_value)
                    self.out(3, z)
                    cs = 'H'

            elif cs == 'C1':
                comment_buffer = ""
                while self.ch and self.ch != '}':
                    if self.ch == 'e':
                        comment_buffer = 'e'
                    elif self.ch == 'n' and comment_buffer == 'e':
                        comment_buffer = 'en'
                    elif self.ch == 'd' and comment_buffer == 'en':
                        comment_buffer = 'end'
                    elif self.ch == '.' and comment_buffer == 'end':
                        cs = self.error("Запрещенная последовательность 'end.' внутри комментария")
                        break
                    else:
                        if self.ch != 'e':
                            comment_buffer = ""
                        elif self.ch == 'e':
                            comment_buffer = 'e'
                    self.gc()

                if cs != 'ER':
                    if not self.ch:
                        cs = self.error("Незакрытый комментарий в конце файла.")
                    else:
                        self.gc();
                        cs = 'H'

        return self.tokens, self.TI, self.TN, self.errors



class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лексический анализатор")
        self.root.geometry("1200x800")
        self.label_font = font.Font(family="Arial", size=12, weight="bold")
        self.text_font = font.Font(family="Courier New", size=11)

        main_frame = tk.Frame(root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main_frame)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        tk.Label(left, text="Исходный код:", font=self.label_font).pack(anchor="w")
        self.input_text = scrolledtext.ScrolledText(left, wrap=tk.WORD, height=10, font=self.text_font)
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        tk.Button(left, text="▶ Анализировать", command=self.analyze, font=self.label_font, bg="#4CAF50",
                  fg="white").pack(fill=tk.X, pady=(0, 10))
        tk.Label(left, text="Поток лексем:", font=self.label_font).pack(anchor="w")
        self.output_tokens = scrolledtext.ScrolledText(left, wrap=tk.WORD, height=10, font=self.text_font,
                                                       state='disabled')
        self.output_tokens.pack(fill=tk.BOTH, expand=True)

        right = tk.Frame(main_frame)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        right.grid_columnconfigure(0, weight=1);
        right.grid_columnconfigure(1, weight=1)
        right.grid_rowconfigure(0, weight=1);
        right.grid_rowconfigure(1, weight=1)

        self.out_tw = self._create_table(right, "TW (Служебные слова)", 0, 0)
        self.out_tl = self._create_table(right, "TL (Ограничители)", 0, 1)
        self.out_ti = self._create_table(right, "TI (Идентификаторы)", 1, 0)
        self.out_tn = self._create_table(right, "TN (Числа + Значения)", 1, 1)

        self._populate_static()
        self._insert_example()

    def _create_table(self, parent, title, r, c):
        f = tk.Frame(parent, bd=2, relief=tk.SUNKEN)
        f.grid(row=r, column=c, sticky="nsew", padx=5, pady=5)
        tk.Label(f, text=title, font=self.label_font).pack(anchor="w")
        t = scrolledtext.ScrolledText(f, wrap=tk.WORD, font=self.text_font, state='disabled')
        t.pack(fill=tk.BOTH, expand=True)
        return t

    def _populate_static(self):
        self._display(self.out_tw, TW)
        self._display(self.out_tl, TL)

    def analyze(self):
        code = self.input_text.get("1.0", tk.END)
        if not code.strip(): return

        scanner = Scanner()
        tokens, ti, tn, errs = scanner.scan(code)

        self._display_tokens(tokens)
        self._display(self.out_ti, ti)
        self._display(self.out_tn, tn)

        if errs: messagebox.showerror("Ошибки", "\n".join(errs))

    def _display(self, widget, data):
        widget.config(state='normal')
        widget.delete("1.0", tk.END)
        for k, v in sorted(data.items(), key=lambda x: x[1]):
            widget.insert(tk.END, f"{v:<3}: {k}\n")
        widget.config(state='disabled')

    def _display_tokens(self, tokens):
        self.output_tokens.config(state='normal')
        self.output_tokens.delete("1.0", tk.END)
        s = ""
        for i, t in enumerate(tokens):
            s += f"({t[0]},{t[1]})".ljust(10)
            if (i + 1) % 5 == 0: s += "\n"
        self.output_tokens.insert(tk.END, s)
        self.output_tokens.config(state='disabled')

    def _insert_example(self):
        code = """program ExponentTest;
var
    val1 as !;
begin
    { Экспоненциальная форма }
    val1 as 123e-1;   { 12.3 }
    val1 as 1.5e+2;   { 150.0 }
    val1 as 0FEh;     { Hex 254 }
end."""
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", code)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()