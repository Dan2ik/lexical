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

    def peek(self):
        """Возвращает следующий символ без сдвига указателя."""
        return self.source_code[self.ptr + 1] if self.ptr + 1 < len(self.source_code) else ''

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

    def put(self, table, custom_key=None):
        key = custom_key if custom_key is not None else self.s
        if key not in table:
            new_id = len(table) + 1
            table[key] = new_id
        return table[key]

    def out(self, n, k):
        token_info = {
            "class": n,
            "code": k,
            "value": self.s
        }
        self.tokens.append(token_info)

    def error(self, message):
        error_message = f"Ошибка: {message} на позиции {self.ptr} ('{self.ch}')"
        self.errors.append(error_message)
        return 'ER'

    def finalize_simple_decimal(self):
        z = self.put(self.TN, f"{self.s} (= {self.s})")
        self.out(3, z)
        return 'H'

    def is_valid_hex_number(self, s):
        if not s:
            return False
        return all(c.upper() in '0123456789ABCDEF' for c in s)

    def is_hex_context(self):
        """
        Проверяет, является ли текущий контекст частью шестнадцатеричного числа.
        """
        if self.ptr + 1 >= len(self.source_code):
            return False
        next_char = self.source_code[self.ptr + 1]
        return (self.digit(next_char) or
                self.is_hex_letter(next_char) or
                next_char.lower() == 'h')

    # --- Основной метод сканирования ---
    def scan(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.errors = []
        self.TI = {}
        self.TN = {}
        self.ptr = -1

        self.gc()
        cs = 'H'  # Начальное состояние

        while cs not in ['V', 'ER']:
            # --- H: Начальное состояние ---
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
                    if self.digit(self.peek()):
                        self.add();
                        self.gc();
                        cs = 'P1'
                    else:
                        self.add();
                        self.out(2, 11);
                        self.gc();
                        cs = 'H'
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

            # --- I: Идентификаторы ---
            elif cs == 'I':
                while self.let(self.ch) or self.digit(self.ch): self.add(); self.gc()
                z = self.look(self.TW)
                if z != 0:
                    self.out(1, z)
                else:
                    z = self.put(self.TI);
                    self.out(4, z)
                cs = 'H'

            # --- Числовые состояния с исправлением приоритетов ---

            elif cs == 'N0':
                if self.ch.lower() == 'b':
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'B_FINAL'
                elif self.ch.lower() == 'o':
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'O_FINAL'
                elif self.ch.lower() == 'd':
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'D_FINAL'
                elif self.ch.lower() == 'h':
                    self.add();
                    self.gc();
                    cs = 'HX_FINAL'

                # ВАЖНО: Сначала проверяем экспоненту (float), потом Hex-буквы
                elif self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E11'

                elif self.ch == '.':
                    self.add();
                    self.gc();
                    cs = 'P2'

                # Только теперь проверяем обычные hex буквы
                elif self.ch in '01':
                    self.add(); self.gc(); cs = 'N2'
                elif '2' <= self.ch <= '7':
                    self.add(); self.gc(); cs = 'N8'
                elif self.ch in '89':
                    self.add(); self.gc(); cs = 'N10'
                elif self.is_hex_letter(self.ch):
                    self.add(); self.gc(); cs = 'N16'

                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ '{self.ch}'.")
                    cs = 'ER'
                else:
                    cs = self.finalize_simple_decimal()

            elif cs == 'N2':
                if self.ch.lower() == 'b':
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'B_FINAL'
                elif self.ch.lower() == 'o':
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'O_FINAL'
                elif self.ch.lower() == 'd':
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'D_FINAL'
                elif self.ch.lower() == 'h':
                    self.add();
                    self.gc();
                    cs = 'HX_FINAL'

                # ВАЖНО: Экспонента перед Hex
                elif self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E11'

                elif self.ch == '.':
                    self.add();
                    self.gc();
                    cs = 'P2'
                elif self.ch in '01':
                    self.add(); self.gc()
                elif '2' <= self.ch <= '7':
                    self.add(); self.gc(); cs = 'N8'
                elif self.ch in '89':
                    self.add(); self.gc(); cs = 'N10'
                elif self.is_hex_letter(self.ch):
                    self.add(); self.gc(); cs = 'N16'
                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ '{self.ch}'.")
                    cs = 'ER'
                else:
                    cs = self.finalize_simple_decimal()

            elif cs == 'N8':
                if self.ch.lower() == 'b':
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.errors.append(f"Ошибка: недопустимый суффикс 'b'"); cs = 'ER'
                elif self.ch.lower() == 'o':
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'O_FINAL'
                elif self.ch.lower() == 'd':
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'D_FINAL'
                elif self.ch.lower() == 'h':
                    self.add();
                    self.gc();
                    cs = 'HX_FINAL'

                # ВАЖНО: Экспонента перед Hex
                elif self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E11'

                elif self.ch == '.':
                    self.add();
                    self.gc();
                    cs = 'P2'
                elif '0' <= self.ch <= '7':
                    self.add(); self.gc()
                elif self.ch in '89':
                    self.add(); self.gc(); cs = 'N10'
                elif self.is_hex_letter(self.ch):
                    self.add(); self.gc(); cs = 'N16'
                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ '{self.ch}'.")
                    cs = 'ER'
                else:
                    cs = self.finalize_simple_decimal()

            elif cs == 'N10':
                if self.ch.lower() in 'bo':
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.errors.append(f"Ошибка: недопустимый суффикс"); cs = 'ER'
                elif self.ch.lower() == 'd':
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'D_FINAL'
                elif self.ch.lower() == 'h':
                    self.add();
                    self.gc();
                    cs = 'HX_FINAL'

                # ВАЖНО: Экспонента перед Hex
                elif self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E11'

                elif self.ch == '.':
                    self.add();
                    self.gc();
                    cs = 'P2'
                elif self.digit(self.ch):
                    self.add(); self.gc()
                elif self.is_hex_letter(self.ch):
                    self.add(); self.gc(); cs = 'N16'
                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ '{self.ch}'.")
                    cs = 'ER'
                else:
                    cs = self.finalize_simple_decimal()

            # --- N16: Hex ---
            elif cs == 'N16':
                if self.digit(self.ch) or self.is_hex_letter(self.ch):
                    self.add();
                    self.gc()
                elif self.ch.lower() == 'h':
                    self.add();
                    self.gc();
                    cs = 'HX_FINAL'
                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ '{self.ch}' в hex.")
                    cs = 'ER'
                else:
                    if self.is_valid_hex_number(self.s):
                        z = self.put(self.TN)
                        self.out(3, z)
                        cs = 'H'
                    else:
                        self.errors.append(f"Ошибка: недопустимые символы в hex: '{self.s}'")
                        cs = 'ER'

            # --- Финализаторы чисел ---
            elif cs == 'B_FINAL':
                if not all(c in '01' for c in self.s[:-1]):
                    self.errors.append(f"Ошибка binary: {self.s}");
                    cs = 'ER'
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'

            elif cs == 'O_FINAL':
                if not all(c in '01234567' for c in self.s[:-1]):
                    self.errors.append(f"Ошибка octal: {self.s}");
                    cs = 'ER'
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'

            elif cs == 'D_FINAL':
                if not all(c.isdigit() for c in self.s[:-1]):
                    self.errors.append(f"Ошибка decimal: {self.s}");
                    cs = 'ER'
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'

            elif cs == 'HX_FINAL':
                if not self.is_valid_hex_number(self.s[:-1]):
                    self.errors.append(f"Ошибка hex: {self.s}");
                    cs = 'ER'
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'

            # --- Float (P1, P2, E11, E12) ---
            elif cs == 'P1':
                if self.digit(self.ch):
                    self.add();
                    self.gc();
                    cs = 'P2'
                else:
                    self.errors.append("Ошибка: после '.' ожидалась цифра.")
                    cs = 'ER'

            elif cs == 'P2':
                while self.digit(self.ch): self.add(); self.gc()
                if self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E11'
                else:
                    z = self.put(self.TN, f"{self.s} (= {self.s})")
                    self.out(3, z)
                    cs = 'H'

            elif cs == 'E11':
                if self.digit(self.ch) or self.ch in '+-':
                    self.add();
                    self.gc();
                    cs = 'E12'
                else:
                    cs = self.error("Ошибка в экспоненте: ожидалась цифра или знак.")
            elif cs == 'E12':
                while self.digit(self.ch): self.add(); self.gc()
                z = self.put(self.TN, f"{self.s}")
                self.out(3, z)
                cs = 'H'

            # --- Комментарии и операторы ---
            elif cs == 'C1':
                if self.ch == '*':
                    self.gc(); cs = 'C2'
                else:
                    self.s = '/'; self.out(2, 16); cs = 'H'

            elif cs == 'C2':
                while self.ch and self.ch != '*': self.gc()
                if not self.ch:
                    self.errors.append("Ошибка: незакрытый комментарий.")
                    cs = 'ER'
                else:
                    self.gc(); cs = 'C3'

            elif cs == 'C3':
                if not self.ch:
                    self.errors.append("Ошибка: незакрытый комментарий.")
                    cs = 'ER'
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
                    self.s = '=='; self.out(2, 23); self.gc()
                else:
                    self.s = '='; self.out(2, 15)
                cs = 'H'

            elif cs == 'SC':
                if self.ch == '=':
                    self.s = ':='; self.out(2, 8); self.gc()
                else:
                    self.s = ':'; self.out(2, 8)
                cs = 'H'

            elif cs == 'SP':
                if self.ch == '|':
                    self.s = '||'; self.out(2, 14); self.gc(); cs = 'H'
                else:
                    self.errors.append("Ошибка: ожидался второй '|'")
                cs = 'ER'

            elif cs == 'SA':
                if self.ch == '&':
                    self.s = '&&'; self.out(2, 17); self.gc(); cs = 'H'
                else:
                    self.errors.append("Ошибка: ожидался второй '&'")
                cs = 'ER'

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
                    self.errors.append(f"Ошибка: неизвестный символ '{self.ch}'")
                    cs = 'ER'

        if cs == 'ER':
            return False
        return True

    def run(self):
        """Запуск анализа и конвертация результатов для GUI"""
        success = self.scan(self.source_code)

        tokens = [(token["class"], token["code"]) for token in self.tokens]
        keywords = list(self.TW.keys())
        delimiters = list(self.TL.keys())
        identifiers = list(self.TI.keys())
        numbers = list(self.TN.keys())

        decimal_values = {}
        for num in numbers:
            try:
                # Очистка от возможных меток (= val), которые добавляются в finalize_simple_decimal
                clean_num = num.split(' (=')[0]

                if clean_num.endswith('b'):
                    decimal_values[num] = int(clean_num[:-1], 2)
                elif clean_num.endswith('o'):
                    decimal_values[num] = int(clean_num[:-1], 8)
                elif clean_num.endswith('h'):
                    decimal_values[num] = int(clean_num[:-1], 16)
                elif clean_num.endswith('d'):
                    decimal_values[num] = int(clean_num[:-1])
                elif 'e' in clean_num.lower() or '.' in clean_num:
                    # Коррекция для float: если есть 'e', но нет точки (123e-1)
                    val_str = clean_num
                    if 'e' in val_str.lower() and '.' not in val_str:
                        e_pos = val_str.lower().find('e')
                        if e_pos > 0:
                            val_str = val_str[:e_pos] + '.0' + val_str[e_pos:]
                    decimal_values[num] = float(val_str)
                else:
                    # Если суффикса нет, но это Hex (например 0AF), пробуем как hex
                    if all(c.upper() in '0123456789ABCDEF' for c in clean_num) and any(
                            c.upper() in 'ABCDEF' for c in clean_num):
                        decimal_values[num] = int(clean_num, 16)
                    else:
                        decimal_values[num] = int(clean_num)
            except ValueError:
                decimal_values[num] = "Nan/Err"

        return tokens, keywords, delimiters, identifiers, numbers, decimal_values, self.errors


# --- GUI ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лексический анализатор — Модельный язык М")
        self.root.geometry("1100x850")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")

        # Верхний фрейм
        top_frame = ctk.CTkFrame(root, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(top_frame, text="Исходный код:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")

        self.input_text = ctk.CTkTextbox(top_frame, height=200, wrap="word", font=("Consolas", 12))
        self.input_text.pack(fill="both", expand=True, pady=(5, 10))

        sample_code = """{
int num;
writeln 01b;      /* Binary */
writeln 0AFh;     /* Hex */
writeln 123.45e-2; /* Float standard */
writeln 123e-1;    /* Float without dot */
writeln 123e;      /* Hex (valid hex digits) */
}
"""
        self.input_text.insert(INSERT, sample_code.strip())

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

        # Сетка для таблиц
        tables_frame.grid_columnconfigure(0, weight=1)
        tables_frame.grid_columnconfigure(1, weight=1)
        tables_frame.grid_rowconfigure(0, weight=1)
        tables_frame.grid_rowconfigure(1, weight=1)

        self.kw_text = self._create_table(tables_frame, "Служебные слова (Табл. 1)", 0, 0)
        self.del_text = self._create_table(tables_frame, "Разделители (Табл. 2)", 0, 1)
        self.id_text = self._create_table(tables_frame, "Идентификаторы (Табл. 4)", 1, 0)
        self.num_text = self._create_table(tables_frame, "Числа (Табл. 3)", 1, 1)

        self.scanner = Scanner()

    def _create_table(self, parent, title, row, col):
        frame = ctk.CTkFrame(parent)
        frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(frame, text=title, font=("Arial", 11, "bold")).pack(pady=2)
        text_widget = ctk.CTkTextbox(frame, font=("Consolas", 10))
        text_widget.pack(fill="both", expand=True, padx=2, pady=2)
        return text_widget

    def analyze(self):
        code = self.input_text.get("1.0", END).strip()
        if not code: return

        self.scanner.source_code = code
        tokens, kw, dl, ids, nums, dec_vals, errors = self.scanner.run()

        # Вывод токенов
        self.output_text.delete("1.0", END)
        if errors:
            self.output_text.insert(INSERT, "НАЙДЕНЫ ОШИБКИ:\n" + "\n".join(errors) + "\n\n")

        self.output_text.insert(INSERT, "ПОСЛЕДОВАТЕЛЬНОСТЬ ЛЕКСЕМ:\n")
        line = ""
        for cls, code in tokens:
            token_str = f"({cls}, {code}) "
            if len(line) + len(token_str) > 80:
                self.output_text.insert(INSERT, line + "\n")
                line = ""
            line += token_str
        self.output_text.insert(INSERT, line + "\n")

        # Заполнение таблиц
        self._fill_table(self.kw_text, kw, self.scanner.TW)
        self._fill_table(self.del_text, dl, self.scanner.TL)

        # Идентификаторы
        self.id_text.delete("1.0", END)
        self.id_text.insert(INSERT, f"{'ID':<20} | {'Код'}\n{'-' * 30}\n")
        for val, code in self.scanner.TI.items():
            self.id_text.insert(INSERT, f"{val:<20} | {code}\n")

        # Числа с переводом
        self.num_text.delete("1.0", END)
        self.num_text.insert(INSERT, f"{'Лексема':<15} | {'Код':<3} | {'Значение'}\n{'-' * 40}\n")
        for val, code in self.scanner.TN.items():
            dec = dec_vals.get(val, "Err")
            # Убираем (= ...) из отображения ключа, если он там есть
            display_val = val.split(' (=')[0]
            self.num_text.insert(INSERT, f"{display_val:<15} | {code:<3} | {dec}\n")

    def _fill_table(self, widget, keys, mapping):
        widget.delete("1.0", END)
        widget.insert(INSERT, f"{'Лексема':<15} | {'Код'}\n{'-' * 25}\n")
        # Сортируем по коду для красоты
        sorted_items = sorted(mapping.items(), key=lambda x: x[1])
        for k, v in sorted_items:
            widget.insert(INSERT, f"{k:<15} | {v}\n")

    def clear_all(self):
        self.input_text.delete("1.0", END)
        self.output_text.delete("1.0", END)
        self.kw_text.delete("1.0", END)
        self.del_text.delete("1.0", END)
        self.id_text.delete("1.0", END)
        self.num_text.delete("1.0", END)


if __name__ == "__main__":
    root = ctk.CTk()
    app = App(root)
    root.mainloop()