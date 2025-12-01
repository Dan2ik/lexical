import customtkinter as ctk
from tkinter import END, INSERT


class Scanner:
    """
    Лексический анализатор (сканер), реализованный на основе диаграммы состояний.
    """

    def __init__(self):
        # --- Таблицы лексем ---
        self.TW = {
            'readln': 1, 'writeln': 2, 'if': 3, 'then': 4, 'else': 5,
            'for': 6, 'to': 7, 'while': 8, 'do': 9, 'true': 10,
            'false': 11, 'or': 12, 'and': 13, 'not': 14, 'as': 15,
            'bool': 16, 'int': 17, 'float': 18
        }
        self.TL = {
            '{': 1, '}': 2, '%': 3, ',': 4, ';': 5,
            '[': 6, ']': 7, ':': 8, '(': 9, ')': 10,
            '+': 11, '-': 12, '*': 13, '||': 14, '=': 15,
            '/': 16, '&&': 17, '!=': 18, '>': 19, '<': 20,
            '<=': 21, '>=': 22, '==': 23,
            '!': 24
        }
        # Динамические таблицы
        self.TI = {}
        self.TN = {}

        # --- Переменные состояния ---
        self.source_code = ""
        self.ptr = -1
        self.ch = ''
        self.s = ''
        self.tokens = []
        self.errors = []

    # --- Вспомогательные функции ---
    def gc(self):
        self.ptr += 1
        if self.ptr < len(self.source_code):
            self.ch = self.source_code[self.ptr]
        else:
            self.ch = ''

    @staticmethod
    def let(char):
        return char.isalpha()

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

    def put(self, table):
        if self.s not in table:
            new_id = len(table) + 1
            table[self.s] = new_id
        return table[self.s]

    def out(self, n, k):
        token_info = {
            "class": n,
            "code": k,
            "value": self.s
        }
        self.tokens.append(token_info)

    def finalize_as_decimal(self):
        z = self.put(self.TN)
        self.out(3, z)
        return 'H'

    def is_valid_hex_number(self, s):
        if not s:
            return False
        return all(c.upper() in '0123456789ABCDEF' for c in s)

    def is_hex_context(self):
        if self.ptr + 1 >= len(self.source_code):
            return False
        next_char = self.source_code[self.ptr + 1]
        return (self.digit(next_char) or
                self.is_hex_letter(next_char) or
                next_char.lower() == 'h')

    def is_exponent_start(self):
        """
        Проверяет, является ли следующий символ началом экспоненты (+, - или цифра).
        Это позволяет отличить 123e-1 (float) от 123eh (hex).
        """
        if self.ptr + 1 >= len(self.source_code):
            return False
        next_char = self.source_code[self.ptr + 1]
        return next_char in '+-' or self.digit(next_char)

    # --- Основной метод сканирования ---
    def scan(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.errors = []
        self.TI = {}
        self.TN = {}
        self.ptr = -1

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
                    self.add();
                    self.gc()
                    if self.s == '0':
                        cs = 'N0'
                    elif '1' <= self.s <= '1':
                        cs = 'N2'
                    elif '2' <= self.s <= '7':
                        cs = 'N8'
                    else:
                        cs = 'N10'
                elif self.ch == '.':
                    self.add(); self.gc(); cs = 'P1'
                elif self.ch == '/':
                    self.gc(); cs = 'C1'
                elif self.ch == '!':
                    self.gc(); cs = 'SE'
                elif self.ch == '=':
                    self.gc(); cs = 'SEQ'
                elif self.ch == ':':
                    self.gc(); cs = 'SC'
                elif self.ch == '|':
                    self.gc(); cs = 'SP'
                elif self.ch == '&':
                    self.gc(); cs = 'SA'
                elif self.ch == '<':
                    self.gc(); cs = 'M1'
                elif self.ch == '>':
                    self.gc(); cs = 'M2'
                elif self.ch == '}':
                    self.add(); self.out(2, 2); self.gc()
                else:
                    cs = 'OG'

            elif cs == 'I':
                while self.let(self.ch) or self.digit(self.ch): self.add(); self.gc()
                z = self.look(self.TW)
                if z != 0:
                    self.out(1, z)
                else:
                    z = self.put(self.TI); self.out(4, z)
                cs = 'H'

            # --- ЧИСЛОВЫЕ СОСТОЯНИЯ ---
            # Ключевое изменение: проверка на 'e' (экспоненту) поднята ВЫШЕ проверки is_hex_letter

            elif cs == 'N0':
                if self.ch.lower() == 'b' and not self.is_hex_context():
                    self.add(); self.gc(); cs = 'B_FINAL'
                elif self.ch.lower() == 'o' and not self.is_hex_context():
                    self.add(); self.gc(); cs = 'O_FINAL'
                elif self.ch.lower() == 'd' and not self.is_hex_context():
                    self.add(); self.gc(); cs = 'D_FINAL'
                elif self.ch.lower() == 'h':
                    self.add(); self.gc(); cs = 'HX_FINAL'

                # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
                elif self.ch.lower() == 'e' and self.is_exponent_start():
                    self.add();
                    self.gc();
                    cs = 'E11'
                # -------------------------

                elif self.ch in '01':
                    self.add(); self.gc(); cs = 'N2'
                elif '2' <= self.ch <= '7':
                    self.add(); self.gc(); cs = 'N8'
                elif self.ch in '89':
                    self.add(); self.gc(); cs = 'N10'
                elif self.is_hex_letter(self.ch):
                    self.add(); self.gc(); cs = 'N16'
                elif self.ch == '.':
                    self.add(); self.gc(); cs = 'P2'
                elif self.digit(self.ch):
                    self.add(); self.gc(); cs = 'N10'
                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ '{self.ch}'."); cs = 'ER'
                else:
                    cs = self.finalize_as_decimal()

            elif cs == 'N2':
                if self.ch.lower() == 'b' and not self.is_hex_context():
                    self.add(); self.gc(); cs = 'B_FINAL'
                elif self.ch.lower() == 'o' and not self.is_hex_context():
                    self.add(); self.gc(); cs = 'O_FINAL'
                elif self.ch.lower() == 'd' and not self.is_hex_context():
                    self.add(); self.gc(); cs = 'D_FINAL'
                elif self.ch.lower() == 'h':
                    self.add(); self.gc(); cs = 'HX_FINAL'

                # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
                elif self.ch.lower() == 'e' and self.is_exponent_start():
                    self.add();
                    self.gc();
                    cs = 'E11'
                # -------------------------

                elif self.ch in '01':
                    self.add(); self.gc()
                elif '2' <= self.ch <= '7':
                    self.add(); self.gc(); cs = 'N8'
                elif self.ch in '89':
                    self.add(); self.gc(); cs = 'N10'
                elif self.is_hex_letter(self.ch):
                    self.add(); self.gc(); cs = 'N16'
                elif self.ch == '.':
                    self.add(); self.gc(); cs = 'P2'
                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ '{self.ch}'."); cs = 'ER'
                else:
                    cs = self.finalize_as_decimal()

            elif cs == 'N8':
                if self.ch.lower() == 'b' and not self.is_hex_context():
                    self.errors.append(f"Ошибка: недопустимый суффикс 'b' для цифр 2-7");
                    cs = 'ER'
                elif self.ch.lower() == 'o' and not self.is_hex_context():
                    self.add(); self.gc(); cs = 'O_FINAL'
                elif self.ch.lower() == 'd' and not self.is_hex_context():
                    self.add(); self.gc(); cs = 'D_FINAL'
                elif self.ch.lower() == 'h':
                    self.add(); self.gc(); cs = 'HX_FINAL'

                # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
                elif self.ch.lower() == 'e' and self.is_exponent_start():
                    self.add();
                    self.gc();
                    cs = 'E11'
                # -------------------------

                elif '0' <= self.ch <= '7':
                    self.add(); self.gc()
                elif self.ch in '89':
                    self.add(); self.gc(); cs = 'N10'
                elif self.is_hex_letter(self.ch):
                    self.add(); self.gc(); cs = 'N16'
                elif self.ch == '.':
                    self.add(); self.gc(); cs = 'P2'
                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ '{self.ch}'."); cs = 'ER'
                else:
                    cs = self.finalize_as_decimal()

            elif cs == 'N10':
                if self.ch.lower() == 'o' and not self.is_hex_context():
                    self.errors.append(f"Ошибка: суффикс 'o' недопустим при цифрах 8-9");
                    cs = 'ER'
                elif self.ch.lower() == 'b' and not self.is_hex_context():
                    self.errors.append(f"Ошибка: суффикс 'b' недопустим");
                    cs = 'ER'
                elif self.ch.lower() == 'd' and not self.is_hex_context():
                    self.add(); self.gc(); cs = 'D_FINAL'
                elif self.ch.lower() == 'h':
                    self.add(); self.gc(); cs = 'HX_FINAL'

                # --- ИСПРАВЛЕНИЕ ЗДЕСЬ ---
                elif self.ch.lower() == 'e' and self.is_exponent_start():
                    self.add();
                    self.gc();
                    cs = 'E11'
                # -------------------------

                elif self.digit(self.ch):
                    self.add(); self.gc()
                elif self.is_hex_letter(self.ch):
                    self.add(); self.gc(); cs = 'N16'
                elif self.ch == '.':
                    self.add(); self.gc(); cs = 'P2'
                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ '{self.ch}'."); cs = 'ER'
                else:
                    cs = self.finalize_as_decimal()

            elif cs == 'N16':
                if self.digit(self.ch) or self.is_hex_letter(self.ch):
                    self.add(); self.gc()
                elif self.ch.lower() == 'h':
                    self.add(); self.gc(); cs = 'HX_FINAL'
                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ в HEX '{self.ch}'");
                    cs = 'ER'
                else:
                    if self.is_valid_hex_number(self.s):
                        z = self.put(self.TN);
                        self.out(3, z);
                        cs = 'H'
                    else:
                        self.errors.append(f"Ошибка в HEX числе: '{self.s}'");
                        cs = 'ER'

            # --- Остальные состояния ---
            elif cs == 'B_FINAL':
                if not all(c in '01' for c in self.s[:-1]):
                    self.errors.append("Ошибка в BIN"); cs = 'ER'
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'
            elif cs == 'O_FINAL':
                if not all(c in '01234567' for c in self.s[:-1]):
                    self.errors.append("Ошибка в OCT"); cs = 'ER'
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'
            elif cs == 'D_FINAL':
                if not all(c.isdigit() for c in self.s[:-1]):
                    self.errors.append("Ошибка в DEC"); cs = 'ER'
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'
            elif cs == 'HX_FINAL':
                if not self.is_valid_hex_number(self.s[:-1]):
                    self.errors.append("Ошибка в HEX"); cs = 'ER'
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'

            elif cs == 'P1':
                if self.digit(self.ch):
                    self.add(); self.gc(); cs = 'P2'
                else:
                    self.errors.append("Ошибка: после '.' ожидалась цифра."); cs = 'ER'
            elif cs == 'P2':
                while self.digit(self.ch): self.add(); self.gc()
                if self.ch.lower() == 'e':
                    self.add(); self.gc(); cs = 'E11'
                else:
                    cs = self.finalize_as_decimal()
            elif cs == 'E11':
                if self.ch in '+-': self.add(); self.gc()
                if self.digit(self.ch):
                    while self.digit(self.ch): self.add(); self.gc()
                    cs = self.finalize_as_decimal()
                else:
                    self.errors.append("Ошибка: после 'E' ожидались цифры."); cs = 'ER'

            # --- Комментарии и операторы ---
            elif cs == 'C1':
                if self.ch == '*':
                    self.gc(); cs = 'C2'
                else:
                    self.s = '/'; self.out(2, 16); cs = 'H'
            elif cs == 'C2':
                while self.ch and self.ch != '*': self.gc()
                if not self.ch:
                    self.errors.append("Незакрытый комментарий"); cs = 'ER'
                else:
                    self.gc(); cs = 'C3'
            elif cs == 'C3':
                if not self.ch:
                    self.errors.append("Незакрытый комментарий"); cs = 'ER'
                elif self.ch == '/':
                    self.gc(); cs = 'H'
                else:
                    cs = 'C2'
            elif cs == 'SE':
                if self.ch == '=':
                    self.s = '!='; self.out(2, 18); self.gc()
                else:
                    self.s = '!'; self.out(2, 24)
                cs = 'H'
            elif cs == 'SEQ':
                if self.ch == '=':
                    self.s = '=='; self.out(2, 23); self.gc(); cs = 'H'
                else:
                    self.s = '='; self.out(2, 15); cs = 'H'
            elif cs == 'SC':
                if self.ch == '=':
                    self.s = ':='; self.out(2, 8); self.gc(); cs = 'H'
                else:
                    self.s = ':'; self.out(2, 8); cs = 'H'
            elif cs == 'SP':
                if self.ch == '|':
                    self.s = '||'; self.out(2, 14); self.gc(); cs = 'H'
                else:
                    self.errors.append("Ожидалось '||'"); cs = 'ER'
            elif cs == 'SA':
                if self.ch == '&':
                    self.s = '&&'; self.out(2, 17); self.gc(); cs = 'H'
                else:
                    self.errors.append("Ожидалось '&&'"); cs = 'ER'
            elif cs == 'M1':
                if self.ch == '=':
                    self.s = '<='; self.out(2, 21); self.gc()
                else:
                    self.s = '<'; self.out(2, 20)
                cs = 'H'
            elif cs == 'M2':
                if self.ch == '=':
                    self.s = '>='; self.out(2, 22); self.gc()
                else:
                    self.s = '>'; self.out(2, 19)
                cs = 'H'
            elif cs == 'OG':
                self.add()
                z = self.look(self.TL)
                if z != 0:
                    self.out(2, z); self.gc(); cs = 'H'
                else:
                    self.errors.append(f"Неизвестный символ '{self.ch}'"); cs = 'ER'

        if cs == 'ER':
            return False
        return True

    # run() и остальной код остаются без изменений...

# --- GUI (оставлен без изменений, но с обновленным тестовым примером) ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лексический анализатор — Модельный язык М")
        self.root.geometry("1100x850")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")

        # Верхний фрейм (ввод)
        top_frame = ctk.CTkFrame(root, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(top_frame, text="Исходный код:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")

        self.input_text = ctk.CTkTextbox(top_frame, height=200, wrap="word", font=("Consolas", 12))
        self.input_text.pack(fill="both", expand=True, pady=(5, 10))

        sample_code = """{
int num, i, isPrime;
isPrime := 1;

readln num;

/* Проверка чисел в разных системах */
writeln 01b;      
writeln 01bh;     
writeln 03dh;     
writeln 1AFh;     
writeln 123.45e-2; 
writeln 99;     
}
"""

        self.input_text.insert(INSERT, sample_code.strip())  # strip() убран, чтобы соответствовать вашему коду

        # Кнопки
        button_frame = ctk.CTkFrame(root, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkButton(button_frame, text="Анализировать", command=self.analyze, width=120).pack(side="left",
                                                                                                padx=(0, 10))
        ctk.CTkButton(button_frame, text="Очистить", command=self.clear_all, width=100).pack(side="left")

        # Вкладки
        self.tabview = ctk.CTkTabview(root, height=450)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        self.tabview.add("Результат")
        self.tabview.add("Таблицы")

        # Вкладка "Результат"
        result_frame = self.tabview.tab("Результат")
        self.output_text = ctk.CTkTextbox(result_frame, wrap="word", font=("Consolas", 11))
        self.output_text.pack(fill="both", expand=True)

        # Вкладка "Таблицы"
        tables_frame = self.tabview.tab("Таблицы")

        top_row = ctk.CTkFrame(tables_frame, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 10))
        bottom_row = ctk.CTkFrame(tables_frame, fg_color="transparent")
        bottom_row.pack(fill="x")

        self.kw_text = self._create_table(top_row, "Служебные слова (Табл. 1)")
        self.del_text = self._create_table(top_row, "Разделители (Табл. 2)")
        self.id_text = self._create_table(bottom_row, "Идентификаторы (Табл. 4)")
        self.num_text = self._create_table(bottom_row, "Числа (Табл. 3)")

        self.load_static_tables()

    def _create_table(self, parent, title):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=5, pady=(0, 3))
        text_widget = ctk.CTkTextbox(frame, height=180, wrap="word", font=("Consolas", 11))
        text_widget.pack(fill="both", expand=True)
        return text_widget

    def load_static_tables(self):
        lexer = Scanner()
        self._update_text(self.kw_text, "\n".join(f"{i + 1}: {kw}" for i, kw in enumerate(lexer.TW.keys())))
        self._update_text(self.del_text, "\n".join(f"{i + 1}: {dl}" for i, dl in enumerate(lexer.TL.keys())))

    def _format_numbers_table(self, numbers, decimal_values):
        lines = []
        for i, lexeme in enumerate(numbers):
            index = i + 1
            decimal_val = decimal_values.get(lexeme, "Н/Д")
            if isinstance(decimal_val, (int, str)):
                decimal_val_str = str(decimal_val)
            else:
                decimal_val_str = f"{decimal_val:.6g}"

            # Добавление информации о системе счисления
            sys = "HEX" if lexeme.lower().endswith('h') or (not lexeme.lower().endswith(('b', 'o', 'd')) and any(
                c.upper() in 'ABCDEF' for c in lexeme)) else \
                "BIN" if lexeme.lower().endswith('b') else \
                    "OCT" if lexeme.lower().endswith('o') else \
                        "DEC" if lexeme.lower().endswith('d') or ('.' not in lexeme and 'e' not in lexeme.lower()) else \
                            "FLOAT"

            lines.append(f"{index}: {lexeme} ({sys}: {decimal_val_str})")
        return "\n".join(lines)

    def analyze(self):
        source_code = self.input_text.get("1.0", END)
        lexer = Scanner()
        success = lexer.scan(source_code)

        # Получаем результаты
        tokens = [(token["class"], token["code"]) for token in lexer.tokens]
        identifiers = list(lexer.TI.keys())
        numbers = list(lexer.TN.keys())

        # Создаем decimal_values
        decimal_values = {}
        for num in numbers:
            try:
                if num.lower().endswith('b'):
                    decimal_values[num] = int(num[:-1], 2)
                elif num.lower().endswith('o'):
                    decimal_values[num] = int(num[:-1], 8)
                elif num.lower().endswith('h'):
                    decimal_values[num] = int(num[:-1], 16)
                elif num.lower().endswith('d'):
                    decimal_values[num] = int(num[:-1])
                elif 'e' in num.lower() or '.' in num:
                    decimal_values[num] = float(num)
                else:
                    # Если число без суффикса, но содержит hex-цифры (напр. 0AF), то оно тоже HEX
                    if all(c.upper() in '0123456789ABCDEF' for c in num):
                        decimal_values[num] = int(num, 16)
                    else:
                        decimal_values[num] = int(num)
            except ValueError:
                decimal_values[num] = "Ошибка конвертации"

        output = ""
        if lexer.errors:
            output += "⚠️ Ошибки:\n" + "\n".join(lexer.errors) + "\n\n"
        else:
            output += "✅ Лексический анализ завершен успешно.\n\n"

        output += "✅ Лексемы (таблица, номер):\n"
        output += " ".join(f"({t[0]},{t[1]})" for t in tokens)

        self._update_text(self.output_text, output)
        self._update_text(self.id_text, "\n".join(f"{i + 1}: {name}" for i, name in enumerate(identifiers)))
        self._update_text(self.num_text, self._format_numbers_table(numbers, decimal_values))

    def clear_all(self):
        self.input_text.delete("1.0", END)
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