import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import io
import customtkinter as ctk


# --- ЛЕКСИЧЕСКИЙ АНАЛИЗАТОР (SCANNER) ---
class Scanner:
    def __init__(self):
        self.TW = {
            'readln': 1, 'writeln': 2, 'if': 3, 'then': 4, 'else': 5,
            'for': 6, 'to': 7, 'while': 8, 'do': 9, 'true': 10,
            'false': 11, 'or': 12, 'and': 13, 'not': 14, 'as': 15,
            'bool': 16, 'int': 17, 'float': 18,
            'step': 19, 'next': 20, 'begin': 21, 'end': 22
        }
        self.TL = {
            '{': 1, '}': 2, '%': 3, ',': 4, ';': 5,
            '[': 6, ']': 7, ':': 8, '(': 9, ')': 10,
            '+': 11, '-': 12, '*': 13, '||': 14, '=': 15,
            '/': 16, '&&': 17, '!=': 18, '>': 19, '<': 20,
            '<=': 21, '>=': 22, '==': 23, '!': 24
        }
        self.TI = {}
        self.TN = {}
        self.source_code = ""
        self.ptr = -1
        self.ch = ''
        self.s = ''
        self.tokens = []

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
        token_info = {"class": n, "code": k, "value": self.s}
        self.tokens.append(token_info)
        print(f"  -> Распознана лексема: (class={n}, code={k}, value='{self.s}')")

    def finalize_as_decimal(self):
        z = self.put(self.TN)
        self.out(3, z)
        return 'H'

    def scan(self, source_code):
        self.source_code = source_code
        self.gc()
        cs = 'H'
        while cs not in ['V', 'ER']:
            if cs == 'H':
                while self.ch.isspace(): self.gc()
                if not self.ch: cs = 'V'; continue
                self.nill()
                if self.let(self.ch):
                    self.add()
                    self.gc()
                    cs = 'I'
                elif self.digit(self.ch):
                    self.add()
                    self.gc()
                    if '0' <= self.s <= '1':
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
            elif cs in ['N2', 'N8', 'N10']:
                if self.ch.lower() == 'b':
                    self.gc(); cs = 'B'
                elif self.ch.lower() == 'o':
                    self.gc(); cs = 'O'
                elif self.ch.lower() == 'd':
                    self.gc(); cs = 'D'
                elif self.ch.lower() == 'h':
                    self.gc(); cs = 'HX'
                elif self.digit(self.ch) or self.is_hex_letter(self.ch):
                    self.add(); self.gc()
                    if '8' <= self.ch <= '9' or self.is_hex_letter(self.ch):
                        cs = 'N16' if cs == 'N10' else 'N16'
                elif self.ch == '.':
                    self.add(); self.gc(); cs = 'P2'
                elif self.ch.lower() == 'e':
                    self.add(); self.gc(); cs = 'E11'
                else:
                    cs = self.finalize_as_decimal()
            elif cs == 'N16':
                if self.digit(self.ch) or self.is_hex_letter(self.ch):
                    self.add(); self.gc()
                elif self.ch.lower() == 'h':
                    self.gc(); cs = 'HX'
                else:
                    print(f"Ошибка: недопустимый символ '{self.ch}' в HEX."); cs = 'ER'
            elif cs == 'B':
                self.s += 'b'; z = self.put(self.TN); self.out(3, z); cs = 'H'
            elif cs == 'O':
                self.s += 'o'; z = self.put(self.TN); self.out(3, z); cs = 'H'
            elif cs == 'D':
                self.s += 'd'; z = self.put(self.TN); self.out(3, z); cs = 'H'
            elif cs == 'HX':
                self.s += 'h'; z = self.put(self.TN); self.out(3, z); cs = 'H'
            elif cs == 'P1':
                if self.digit(self.ch):
                    self.add(); self.gc(); cs = 'P2'
                else:
                    print("Ошибка: после '.' ожидалась цифра."); cs = 'ER'
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
                    print("Ошибка: после 'E' ожидались цифры."); cs = 'ER'
            elif cs == 'C1':
                if self.ch == '*':
                    self.gc(); cs = 'C2'
                else:
                    self.s = '/'; self.out(2, 16); cs = 'H'
            elif cs == 'C2':
                while self.ch and self.ch != '*': self.gc()
                if not self.ch:
                    print("Ошибка: незакрытый комментарий."); cs = 'ER'
                else:
                    self.gc(); cs = 'C3'
            elif cs == 'C3':
                if self.ch == '/':
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
                    self.s = ':=';
                    # В TL нет :=, но в коде оно обрабатывается как отдельный токен
                    # Добавим его как код 25 (или любое свободное значение)
                    self.tokens.append({"class": 2, "code": 25, "value": ":="})
                    print(f"  -> Распознана лексема: (class=2, code=25, value=':=')")
                    self.gc(); cs = 'H'
                else:
                    self.s = ':'; self.out(2, 8); cs = 'H'
            elif cs == 'SP':
                if self.ch == '|':
                    self.s = '||'; self.out(2, 14); self.gc(); cs = 'H'
                else:
                    self.s = '|'; self.out(2, -1); cs = 'ER'
            elif cs == 'SA':
                if self.ch == '&':
                    self.s = '&&'; self.out(2, 17); self.gc(); cs = 'H'
                else:
                    self.s = '&'; self.out(2, -1); cs = 'ER'
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
                    print(f"Ошибка: неизвестный символ '{self.ch}'"); cs = 'ER'
        if cs == 'ER':
            print(f"\nАнализ прерван из-за ошибки на позиции {self.ptr}.")
            return None
        return self.tokens


# --- PARSER ---
class Parser:
    def __init__(self, tokens, tw, tl, ti, tn, rev_tw, rev_tl):
        self.tokens = tokens
        self.TW = tw
        self.TL = tl
        self.TI = ti
        self.TN = tn
        self.REV_TW = rev_tw
        self.REV_TL = rev_tl
        self.pos = 0
        self.log_messages = []

    def log(self, msg):
        self.log_messages.append(msg)

    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _get_token_info(self, t):
        if not t:
            return "КОНЕЦ ПРОГРАММЫ"
        if t['class'] == 1:
            return f"'{self.REV_TW.get(t['code'], '?')}'"
        elif t['class'] == 2:
            symbol = self.REV_TL.get(t['code'], '?')
            if symbol == '?':
                # Для := и других специальных операторов
                return f"'{t['value']}'"
            if symbol in ['(', ')', ',', ';', '{', '}']:
                return f"'{symbol}'"
            return f"'{t['value']}'"
        elif t['class'] == 3:
            return f"число '{t['value']}'"
        elif t['class'] == 4:
            return f"идентификатор '{t['value']}'"
        return f"'{t['value']}'"

    def validate_balance(self):
        stack = []
        pairs = {
            self.TL['}']: self.TL['{'],
            self.TL[')']: self.TL['('],
            self.TL[']']: self.TL['[']
        }
        code_to_sym = {v: k for k, v in self.TL.items()}
        for t in self.tokens:
            if t['class'] == 2:
                code = t['code']
                # Обработка := как отдельного токена (code=25)
                if code == 25:
                    continue
                if code in pairs.values():
                    stack.append((code, t))
                elif code in pairs.keys():
                    if not stack:
                        raise SyntaxError(f"Лишняя закрывающая скобка: {self._get_token_info(t)}")
                    last_open_code, last_open_token = stack.pop()
                    if pairs[code] != last_open_code:
                        expected_close_code = [k for k, v in pairs.items() if v == last_open_code][0]
                        expected_char = code_to_sym[expected_close_code]
                        raise SyntaxError(
                            f"Несоответствие скобок. Ожидалась '{expected_char}' (для открывающей {self._get_token_info(last_open_token)}), найдена {self._get_token_info(t)}")
        if stack:
            last_open_code, last_open_token = stack[-1]
            char = code_to_sym[last_open_code]
            raise SyntaxError(f"Не закрыта скобка: '{char}' (открыта в {self._get_token_info(last_open_token)})")

    def match(self, cls, code=None, val=None, expected_desc=None):
        t = self.current()
        if not t:
            raise SyntaxError(
                f"Неожиданный конец программы. Ожидался: {expected_desc or 'закрывающий символ или команда'}")
        class_names = {1: "Ключевое слово", 2: "Символ", 3: "Число", 4: "Идентификатор"}
        if t['class'] != cls:
            exp = expected_desc or class_names.get(cls, f"тип {cls}")
            got = class_names.get(t['class'], str(t['class']))
            raise SyntaxError(f"Ожидался: {exp}, но получен '{got}' ({self._get_token_info(t)})")
        if code is not None and t['code'] != code:
            exp_str = self.REV_TW.get(code) if cls == 1 else self.REV_TL.get(code, f"код {code}")
            raise SyntaxError(f"Ожидался: '{exp_str}', но найдено: {self._get_token_info(t)}")
        if val is not None and t['value'] != val:
            raise SyntaxError(f"Ожидалось значение: '{val}', но найдено: {self._get_token_info(t)}")
        self.pos += 1
        return t

    def parse_program(self):
        self.log("Начало программы: Ожидается '{'")
        self.match(2, expected_desc="'{' (Начало блока)", val='{')
        self.validate_balance()
        while True:
            t = self.current()
            if not t:
                break
            if t['class'] == 2 and t['value'] == '}':
                break
            if t['class'] == 2 and t['code'] == self.TL[';']:
                self.match(2, self.TL[';'], expected_desc="';' (пустая команда)")
                continue
            if t['class'] == 1 and t['code'] in [self.TW['int'], self.TW['float'], self.TW['bool']]:
                self.parse_declaration()
            else:
                self.parse_statement()
            nt = self.current()
            if not nt:
                break
            if nt['class'] == 2 and nt['value'] == '}':
                continue
            if nt['class'] != 2 or nt['code'] != self.TL[';']:
                raise SyntaxError(f"Ожидалась ';' после команды. Получено: {self._get_token_info(nt)}")
            self.match(2, self.TL[';'], expected_desc="';' (Разделитель команд)")
        self.match(2, expected_desc="'}' (Конец блока)", val='}')
        self.log("Конец программы: найдено '}'")


    def parse_declaration(self):
        self.log("  Объявление переменных")
        type_token = self.match(1, expected_desc="Тип данных (int, float, bool)")
        first_id = self.match(4, expected_desc="Идентификатор")
        self.log(f"    Объявлена переменная: {first_id['value']} типа {type_token['value']}")
        while True:
            t = self.current()
            if t and t['class'] == 2 and t['code'] == self.TL[',']:
                self.match(2, self.TL[','], expected_desc="','")
                next_id = self.match(4, expected_desc="Идентификатор")
                self.log(f"    Объявлена переменная: {next_id['value']} типа {type_token['value']}")
            else:
                break

    def parse_statement(self):
        t = self.current()
        if not t:
            return
        if t['class'] == 2 and t['code'] == self.TL[';']:
            return
        if t['class'] == 4:
            self.parse_assignment()
        elif t['class'] == 1:
            c = t['code']
            if c == self.TW['if']:
                self.parse_if()
            elif c == self.TW['for']:
                self.parse_for()
            elif c == self.TW['while']:
                self.parse_while()
            elif c == self.TW['readln']:
                self.parse_io(True)
            elif c == self.TW['writeln']:
                self.parse_io(False)
            elif c == self.TW.get('begin'):
                self.parse_compound()
            else:
                raise SyntaxError(f"Неизвестный оператор или команда: {self._get_token_info(t)}")
        else:
            raise SyntaxError(f"Ожидался оператор или идентификатор, найдено: {self._get_token_info(t)}")

    def parse_assignment(self):
        self.log("  Присваивание")
        self.match(4, expected_desc="Идентификатор")
        t = self.current()
        if t and t['class'] == 2 and t['value'] == ':=':
            self.match(2, val=':=', expected_desc="':='")
        else:
            raise SyntaxError(f"Ожидался оператор присваивания ':='. Получено: {self._get_token_info(t)}")
        self.parse_expression()

    def parse_if(self):
        self.log("  Условный оператор (If)")
        self.match(1, self.TW['if'], expected_desc="'if'")
        self.match(2, expected_desc="'('", val='(')
        self.parse_expression()
        self.match(2, expected_desc="')'", val=')')
        if 'then' in self.TW:
            self.match(1, self.TW['then'], expected_desc="'then'")
        self.parse_statement()
        t = self.current()
        if t and t['class'] == 1 and t['code'] == self.TW.get('else'):
            self.match(1, self.TW['else'], expected_desc="'else'")
            self.parse_statement()

    def parse_for(self):
        self.log("  Цикл For")
        self.match(1, self.TW['for'], expected_desc="'for' (Начало цикла)")
        self.parse_assignment()
        self.match(1, self.TW['to'], expected_desc="'to'")
        self.parse_expression()
        t = self.current()
        if t and t['class'] == 1 and t['code'] == self.TW.get('step'):
            self.match(1, self.TW['step'], expected_desc="'step'")
            self.parse_expression()
        self.parse_statement()
        if self.current() and self.current()['value'] == ';':
            self.match(2, expected_desc="';'", val=';')
        self.match(1, self.TW['next'], expected_desc="'next'")

    def parse_while(self):
        self.log("  Цикл While")
        self.match(1, self.TW['while'], expected_desc="'while'")
        self.match(2, expected_desc="'('", val='(')
        self.parse_expression()
        self.match(2, expected_desc="')'", val=')')
        if 'do' in self.TW:
            self.match(1, self.TW['do'], expected_desc="'do'")
        self.parse_statement()

    def parse_compound(self):
        self.log("  Составной оператор (Begin...End)")
        self.match(1, self.TW['begin'], expected_desc="'begin'")
        t = self.current()
        if t and t['class'] == 1 and t['code'] == self.TW['end']:
            self.match(1, self.TW['end'], expected_desc="'end'")
            return
        self.parse_statement()
        while True:
            t = self.current()
            if not t:
                raise SyntaxError("Неожиданный конец файла в составном операторе")
            if t['class'] == 1 and t['code'] == self.TW['end']:
                break
            if t['class'] == 2 and t['value'] == ';':
                self.match(2, val=';', expected_desc="';'")
            else:
                raise SyntaxError(f"Ожидалась ';' в составном операторе. Получено: {self._get_token_info(t)}")
            self.parse_statement()
        self.match(1, self.TW['end'], expected_desc="'end'")

    def parse_io(self, is_r):
        self.log(f"  Ввод/Вывод ({'Read' if is_r else 'Write'})")
        self.match(1, self.TW['readln'] if is_r else self.TW['writeln'], expected_desc="'readln' или 'writeln'")
        t = self.current()
        if t and t['class'] == 2 and t['value'] == '(':
            self.match(2, expected_desc="'('", val='(')
        if is_r:
            self.match(4, expected_desc="ID переменной")
            while True:
                t = self.current()
                if t and t['class'] == 2 and t['value'] == ',':
                    self.match(2, expected_desc="','", val=',')
                    self.match(4, expected_desc="ID переменной")
                else:
                    break
        else:
            self.parse_expression()
            while True:
                t = self.current()
                if t and t['class'] == 2 and t['value'] == ',':
                    self.match(2, expected_desc="','", val=',')
                    self.parse_expression()
                else:
                    break
        t = self.current()
        if t and t['class'] == 2 and t['value'] == ')':
            self.match(2, expected_desc="')'", val=')')

    def parse_expression(self):
        self.parse_logical_or()

    def parse_logical_or(self):
        self.parse_logical_and()
        t = self.current()
        while t and t['class'] == 2 and t['value'] == '||':
            self.match(2, val='||', expected_desc="логический оператор '||'")
            self.parse_logical_and()
            t = self.current()

    def parse_logical_and(self):
        self.parse_relational()
        t = self.current()
        while t and t['class'] == 2 and t['value'] == '&&':
            self.match(2, val='&&', expected_desc="логический оператор '&&'")
            self.parse_relational()
            t = self.current()

    def parse_relational(self):
        self.parse_simple()
        t = self.current()
        rel_ops = ['==', '!=', '<', '<=', '>', '>=']
        if t and t['class'] == 2 and t['value'] in rel_ops:
            self.match(2, expected_desc="реляционный оператор")
            self.parse_simple()

    def parse_simple(self):
        self.parse_term()
        t = self.current()
        while t and t['class'] == 2 and t['value'] in ['+', '-']:
            self.match(2, expected_desc="арифметический оператор '+' или '-'")
            self.parse_term()
            t = self.current()

    def parse_term(self):
        self.parse_factor()
        t = self.current()
        while t and t['class'] == 2 and t['value'] in ['*', '/']:
            self.match(2, expected_desc="арифметический оператор '*' или '/'")
            self.parse_factor()
            t = self.current()

    def parse_factor(self):
        t = self.current()
        if not t:
            raise SyntaxError("Ожидался операнд")
        if t['class'] == 2 and t['value'] == '!':
            self.match(2, val='!', expected_desc="унарный логический оператор '!'")
            self.parse_factor()
        elif t['class'] == 2 and t['value'] == '-':
            self.match(2, val='-', expected_desc="унарный минус")
            self.parse_factor()
        elif t['class'] == 4:
            self.match(4, expected_desc="идентификатор")
        elif t['class'] == 3:
            self.match(3, expected_desc="числовая константа")
        elif t['class'] == 2 and t['value'] == '(':
            self.match(2, val='(', expected_desc="открывающая скобка '('")
            self.parse_expression()
            self.match(2, val=')', expected_desc="закрывающая скобка ')'")
        elif t['class'] == 1 and t['value'] in ['true', 'false']:
            self.match(1, expected_desc="логическая константа (true/false)")
        else:
            raise SyntaxError(f"Неверный операнд: {self._get_token_info(t)}")


# --- GUI CLASS ---
class CompilerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Компилятор (CustomTkinter) — Лексика + Синтаксис")
        self.root.geometry("1000x800")
        self.root.minsize(800, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        main_frame = ctk.CTkFrame(root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        top_frame = ctk.CTkFrame(main_frame)
        top_frame.pack(fill="both", expand=False, pady=(0, 10))
        label = ctk.CTkLabel(top_frame, text="Исходный код:", font=("Helvetica", 14, "bold"))
        label.pack(anchor="w", padx=5)
        self.input_text = ctk.CTkTextbox(top_frame, font=("Consolas", 12), height=180)
        self.input_text.pack(fill="both", expand=True, padx=5, pady=5)
        default_code = """{
    int x, n, i;
    n := 3;
    for i := 1 to n step 1 begin
        readln(x);
        if ((x >= 10) && (x < 20)) then
            writeln(1)
        else
            if ((x >= 20) && (x <= 30)) then
                writeln(2)
            else
                writeln(3);
    end next;
}"""
        self.input_text.insert("1.0", default_code)

        self.run_btn = ctk.CTkButton(
            top_frame,
            text="▶ Запустить Анализ",
            command=self.run_analysis,
            font=("Helvetica", 12, "bold"),
            height=35
        )
        self.run_btn.pack(fill="x", padx=5, pady=5)

        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True)
        self.tab_tokens = self.tabview.add("Лексика (Токены)")
        self.tab_semantics = self.tabview.add("Семантика")
        self.tab_console = self.tabview.add("Консоль / Ошибки")

        self.text_widgets = {}
        for name, tab in [("tokens", self.tab_tokens),
                          ("semantics", self.tab_semantics),
                          ("console", self.tab_console)]:
            text = ctk.CTkTextbox(tab, wrap="none", font=("Consolas", 11))
            text.pack(fill="both", expand=True, padx=5, pady=5)
            text.configure(state="disabled")
            self.text_widgets[name] = text

    def write_to_tab(self, tab_name, content):
        widget = self.text_widgets[tab_name]
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    def run_analysis(self):
        source_code = self.input_text.get("1.0", "end").strip()
        if not source_code:
            messagebox.showwarning("Внимание", "Введите исходный код!")
            return

        log_tokens = io.StringIO()
        log_semantics = io.StringIO()
        log_console = io.StringIO()
        original_stdout = sys.stdout

        try:
            sys.stdout = log_tokens
            print("=== ЛЕКСИЧЕСКИЙ АНАЛИЗ ===")
            scanner = Scanner()
            tokens = scanner.scan(source_code)
            if not tokens:
                raise ValueError("Лексический анализ завершился с ошибкой.")

            sys.stdout = log_semantics
            print("=== СЕМАНТИЧЕСКИЙ АНАЛИЗ ===")
            rev_tw = {v: k for k, v in scanner.TW.items()}
            rev_tl = {v: k for k, v in scanner.TL.items()}
            parser = Parser(tokens, scanner.TW, scanner.TL, scanner.TI, scanner.TN, rev_tw, rev_tl)
            parser.parse_program()
            print("\n--- Синтаксический анализ завершён успешно ---")
            for msg in parser.log_messages:
                print(msg)

            sys.stdout = log_console
            log_console.write("✅ Анализ завершён без ошибок.\n")

        except Exception as e:
            sys.stdout = log_console
            log_console.write(f"❌ ОШИБКА: {str(e)}\n")
            import traceback
            traceback.print_exc(file=log_console)
        finally:
            sys.stdout = original_stdout

        self.write_to_tab("tokens", log_tokens.getvalue())
        self.write_to_tab("semantics", log_semantics.getvalue())
        self.write_to_tab("console", log_console.getvalue())

        if "❌" in log_console.getvalue():
            self.tabview.set("Консоль / Ошибки")
        else:
            self.tabview.set("Семантика")


# --- ЗАПУСК ---
if __name__ == "__main__":
    root = ctk.CTk()
    app = CompilerApp(root)
    root.mainloop()