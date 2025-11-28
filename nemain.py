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
        """Завершает распознавание числа как десятичного (по умолчанию)."""
        z = self.put(self.TN)
        self.out(3, z)
        return 'H'

    def is_valid_hex_number(self, s):
        """Проверяет, состоит ли строка только из hex-цифр"""
        if not s:
            return False
        # Разрешаем только цифры и буквы A-F. Точки и знаки e/p здесь вызовут False,
        # что приведет к ошибке, если они попадут в HX_FINAL (например, 12.34h)
        return all(c.upper() in '0123456789ABCDEF' for c in s)

    def is_hex_context(self):
        """
        Проверяет контекст: если следующий символ — цифра, буква a-f
        ИЛИ 'h' (суффикс hex), то мы продолжаем считать текущее число шестнадцатеричным.
        """
        if self.ptr + 1 >= len(self.source_code):
            return False

        next_char = self.source_code[self.ptr + 1]
        # ВАЖНО: Добавлена проверка на 'h'.
        # Если дальше 'h', то текущие b/d/o — это цифры, а не суффиксы.
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
                    self.add();
                    self.gc();
                    cs = 'P1'
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
                    self.add();
                    self.out(2, 2);
                    self.gc()
                else:
                    cs = 'OG'

            elif cs == 'I':
                while self.let(self.ch) or self.digit(self.ch):
                    self.add();
                    self.gc()
                z = self.look(self.TW)
                if z != 0:
                    self.out(1, z)
                else:
                    z = self.put(self.TI)
                    self.out(4, z)
                cs = 'H'

            # --- Числовые состояния ---

            elif cs == 'N0':
                # Если 0...
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
                elif self.ch in '01':
                    self.add();
                    self.gc();
                    cs = 'N2'
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
                elif self.ch.lower() == 'e':
                    self.add();
                    self.gc();
                    cs = 'E11'
                elif self.digit(self.ch):
                    self.add();
                    self.gc();
                    cs = 'N10'
                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ '{self.ch}'.")
                    cs = 'ER'
                else:
                    cs = self.finalize_as_decimal()

            elif cs == 'N2':
                if self.ch.lower() == 'b':
                    # Благодаря обновленному is_hex_context, если дальше 'h',
                    # то 'b' - это цифра, идем в N16. Иначе - суффикс binary.
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
                elif self.ch.lower() == 'e':
                    self.add();
                    self.gc();
                    cs = 'E11'
                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ '{self.ch}'.")
                    cs = 'ER'
                else:
                    cs = self.finalize_as_decimal()

            elif cs == 'N8':
                if self.ch.lower() == 'o':
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
                elif self.ch.lower() == 'e':
                    self.add();
                    self.gc();
                    cs = 'E11'
                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ '{self.ch}'.")
                    cs = 'ER'
                else:
                    cs = self.finalize_as_decimal()

            elif cs == 'N10':
                if self.ch.lower() == 'o':
                    # 'o' не Hex цифра, но если контекст hex (например 12oh), переходим в N16,
                    # чтобы там или в HX_FINAL выдать ошибку (так как o - недопустима в hex),
                    # но "воспринять" как hex.
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.errors.append(f"Ошибка: суффикс 'o' недопустим здесь: '{self.s}'")
                        cs = 'ER'
                elif self.ch.lower() == 'b':
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.errors.append(f"Ошибка: суффикс 'b' недопустим здесь: '{self.s}'")
                        cs = 'ER'
                elif self.ch.lower() == 'd':
                    if self.is_hex_context():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'D_FINAL'
                elif self.ch.lower() == 'h':
                    self.add();
                    self.gc();
                    cs = 'HX_FINAL'
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
                elif self.ch.lower() == 'e':
                    self.add();
                    self.gc();
                    cs = 'E11'
                elif self.let(self.ch):
                    self.errors.append(f"Ошибка: Недопустимый символ '{self.ch}'.")
                    cs = 'ER'
                else:
                    cs = self.finalize_as_decimal()

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
                    # Если пришли сюда без 'h' на конце (например, просто последовательность букв)
                    if self.is_valid_hex_number(self.s):
                        z = self.put(self.TN);
                        self.out(3, z);
                        cs = 'H'
                    else:
                        self.errors.append(f"Ошибка: '{self.s}'")
                        cs = 'ER'

            # --- Финализаторы ---
            elif cs == 'B_FINAL':
                if not all(c in '01' for c in self.s[:-1]):
                    self.errors.append(f"Ошибка Binary: '{self.s}'")
                    cs = 'ER'
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'

            elif cs == 'O_FINAL':
                if not all(c in '01234567' for c in self.s[:-1]):
                    self.errors.append(f"Ошибка Octal: '{self.s}'")
                    cs = 'ER'
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'

            elif cs == 'D_FINAL':
                if not all(c in '0123456789' for c in self.s[:-1]):
                    self.errors.append(f"Ошибка Decimal: '{self.s}'")
                    cs = 'ER'
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'

            elif cs == 'HX_FINAL':
                # Проверка валидности. 123.45e-2h попадет сюда.
                # Функция is_valid_hex_number вернет False из-за точек и минусов.
                # Сканер "воспринял" как hex (раз дошел сюда), но пометил как ошибочный hex.
                num_part = self.s[:-1]
                if not self.is_valid_hex_number(num_part):
                    self.errors.append(f"Ошибка Hex (недопустимые символы): '{self.s}'")
                    cs = 'ER'
                else:
                    z = self.put(self.TN);
                    self.out(3, z);
                    cs = 'H'

            # --- Float ---
            elif cs == 'P1':
                if self.digit(self.ch):
                    self.add();
                    self.gc();
                    cs = 'P2'
                else:
                    self.errors.append("Ошибка: ожидалась цифра после '.'")
                    cs = 'ER'

            elif cs == 'P2':
                while self.digit(self.ch):
                    self.add();
                    self.gc()
                if self.ch.lower() == 'e':
                    self.add();
                    self.gc();
                    cs = 'E11'
                elif self.ch.lower() == 'h':  # <--- Добавлен переход в Hex
                    self.add();
                    self.gc();
                    cs = 'HX_FINAL'
                else:
                    cs = self.finalize_as_decimal()

            elif cs == 'E11':
                if self.ch in '+-':
                    self.add();
                    self.gc()
                if self.digit(self.ch):
                    while self.digit(self.ch):
                        self.add();
                        self.gc()
                    # После цифр экспоненты:
                    if self.ch.lower() == 'h':  # <--- Добавлен переход в Hex
                        self.add();
                        self.gc();
                        cs = 'HX_FINAL'
                    else:
                        cs = self.finalize_as_decimal()
                else:
                    self.errors.append("Ошибка: ожидались цифры в экспоненте")
                    cs = 'ER'

            # --- Комментарии и операторы ---
            elif cs == 'C1':
                if self.ch == '*':
                    self.gc(); cs = 'C2'
                else:
                    self.s = '/'; self.out(2, 16); cs = 'H'

            elif cs == 'C2':
                while self.ch and self.ch != '*': self.gc()
                if not self.ch:
                    self.errors.append("Ошибка: незакрытый комментарий")
                    cs = 'ER'
                else:
                    self.gc();
                    cs = 'C3'

            elif cs == 'C3':
                if not self.ch:
                    self.errors.append("Ошибка: незакрытый комментарий")
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
                    self.s = '=='; self.out(2, 23); self.gc(); cs = 'H'
                else:
                    self.errors.append("Ошибка ==")
                    cs = 'ER'
            elif cs == 'SC':
                if self.ch == '=':
                    self.s = ':='; self.out(2, 15); self.gc(); cs = 'H'
                else:
                    self.errors.append("Ошибка :=")
                    cs = 'ER'
            elif cs == 'SP':
                if self.ch == '|':
                    self.s = '||'; self.out(2, 14); self.gc(); cs = 'H'
                else:
                    self.errors.append("Ошибка ||")
                    cs = 'ER'
            elif cs == 'SA':
                if self.ch == '&':
                    self.s = '&&'; self.out(2, 17); self.gc(); cs = 'H'
                else:
                    self.errors.append("Ошибка &&")
                    cs = 'ER'
            elif cs == 'M1':
                if self.ch == '=':
                    self.s = '<='; self.out(2, 21); self.gc()
                else:
                    self.s = '<'; self.out(2, 20)
                cs = 'H'
            elif cs == 'M2':
                if self.ch == '=': self.s = '>='; self.out(2, 22);
                self.gc()
                else:
                    self.s = '>';
                    self.out(2, 19)
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
        self.scan(self.source_code)
        # Логика для GUI дублируется в App.analyze, но для справки:
        return self.tokens, self.errors


# --- GUI ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лексический анализатор — Модификация Hex")
        self.root.geometry("1100x850")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("dark-blue")

        # Ввод
        top_frame = ctk.CTkFrame(root, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 10))
        ctk.CTkLabel(top_frame, text="Исходный код:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")

        self.input_text = ctk.CTkTextbox(top_frame, height=200, wrap="word", font=("Consolas", 12))
        self.input_text.pack(fill="both", expand=True, pady=(5, 10))

        # Тестовый пример из задачи
        sample_code = """
writeln 01b;      { Binary: 1 }
writeln 01bh;     { Hex: 27 (1*16 + 11) }
writeln 03dh;     { Hex: 61 (3*16 + 13) }
writeln 123.45e-2h; { Воспринимается как Hex, но даст ошибку структуры }
writeln 0AFh;     { Стандартный Hex }
"""
        self.input_text.insert(INSERT, sample_code.strip())

        # Кнопки
        button_frame = ctk.CTkFrame(root, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkButton(button_frame, text="Анализировать", command=self.analyze, width=120).pack(side="left",
                                                                                                padx=(0, 10))
        ctk.CTkButton(button_frame, text="Очистить", command=self.clear_all, width=100).pack(side="left")

        # Вкладки
        self.tabview = ctk.CTkTabview(root)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.tabview.add("Результат")
        self.tabview.add("Таблицы")

        self.output_text = ctk.CTkTextbox(self.tabview.tab("Результат"), wrap="word", font=("Consolas", 11))
        self.output_text.pack(fill="both", expand=True)

        tables_frame = self.tabview.tab("Таблицы")
        self.num_text = ctk.CTkTextbox(tables_frame, height=300, wrap="word", font=("Consolas", 11))
        self.num_text.pack(fill="both", expand=True)

    def analyze(self):
        source_code = self.input_text.get("1.0", END)
        lexer = Scanner()
        lexer.scan(source_code)

        # Формирование вывода
        tokens_str = " ".join(f"({t['class']},{t['code']})" for t in lexer.tokens)

        output = ""
        if lexer.errors:
            output += "⚠️ Ошибки:\n" + "\n".join(lexer.errors) + "\n\n"
        else:
            output += "✅ Анализ успешен.\n\n"
        output += "Лексемы:\n" + tokens_str

        # Таблица чисел с переводом
        nums_output = "Таблица чисел (Класс 3):\n"
        numbers = list(lexer.TN.keys())
        for i, num in enumerate(numbers):
            try:
                val = "Error"
                if num.lower().endswith('h'):
                    val = int(num[:-1], 16)
                elif num.lower().endswith('b'):
                    val = int(num[:-1], 2)
                elif num.lower().endswith('o'):
                    val = int(num[:-1], 8)
                elif num.lower().endswith('d'):
                    val = int(num[:-1])
                else:
                    if '.' in num or 'e' in num.lower():
                        val = float(num)
                    elif all(c.upper() in '0123456789ABCDEF' for c in num):
                        val = int(num, 16)
                    else:
                        val = int(num)
                nums_output += f"{i + 1}: {num} -> {val}\n"
            except:
                nums_output += f"{i + 1}: {num} -> Ошибка конвертации\n"

        self._update(self.output_text, output)
        self._update(self.num_text, nums_output)

    def clear_all(self):
        self.input_text.delete("1.0", END)
        self._update(self.output_text, "")
        self._update(self.num_text, "")

    def _update(self, widget, text):
        widget.configure(state="normal")
        widget.delete("1.0", END)
        widget.insert("1.0", text)
        widget.configure(state="disabled")


if __name__ == "__main__":
    root = ctk.CTk()
    app = App(root)
    root.mainloop()