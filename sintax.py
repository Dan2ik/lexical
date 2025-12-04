import customtkinter as ctk
from tkinter import END, INSERT
import sys

# Установка рекурсии для предотвращения ошибок при глубоком синтаксическом анализе
# (Например, при сильно вложенных выражениях)
sys.setrecursionlimit(2000)


# ==========================================
# 1. ЛЕКСИЧЕСКИЙ АНАЛИЗАТОР (SCANNER)
# ==========================================
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
            '<=': 21, '>=': 22, '==': 23, '!': 24, ':=': 25
        }
        # Обратные словари
        self.REV_TW = {v: k for k, v in self.TW.items()}
        self.REV_TL = {v: k for k, v in self.TL.items()}
        # Добавляем := в обратный словарь для лучшего вывода в Parser
        self.REV_TL[25] = ':='

        self.TI = {}
        self.TN = {}
        self.tokens = []
        self.errors = []
        self.source_code = ""
        self.ptr = -1
        self.ch = ''
        self.s = ''

    def gc(self):
        self.ptr += 1
        self.ch = self.source_code[self.ptr] if self.ptr < len(self.source_code) else ''

    def peek(self):
        return self.source_code[self.ptr + 1] if self.ptr + 1 < len(self.source_code) else ''

    def let(self, c):
        return c.isalpha()

    def digit(self, c):
        return c.isdigit()

    def is_hex_char(self, c):
        return c.lower() in 'abcdef'

    def nill(self):
        self.s = ''

    def add(self):
        self.s += self.ch

    def put(self, table, key=None):
        k = key if key else self.s
        if k not in table: table[k] = len(table) + 1
        return table[k]

    def out(self, n, k):
        # Добавляем в токен текущую позицию для более точных ошибок
        line, col = self._get_position()
        self.tokens.append({"class": n, "code": k, "value": self.s, "line": line, "col": col})

    def _get_position(self):
        # Определение текущей строки и столбца (приблизительно)
        line = self.source_code[:self.ptr].count('\n') + 1
        last_newline = self.source_code.rfind('\n', 0, self.ptr)
        col = self.ptr - last_newline if last_newline != -1 else self.ptr + 1
        return line, col

    def _add_error(self, message):
        line, col = self._get_position()
        self.errors.append(f"[Строка {line}, Позиция {col}] {message}")

    def scan(self, source_code):
        self.source_code = source_code
        self.tokens = []
        self.errors = []
        self.TI = {}
        self.TN = {}
        self.ptr = -1
        self.gc()
        cs = 'H'

        while cs != 'E':
            if cs == 'H':
                while self.ch.isspace(): self.gc()
                if not self.ch: cs = 'E'; continue
                self.nill()

                if self.let(self.ch):
                    self.add();
                    self.gc();
                    cs = 'ID'
                elif self.digit(self.ch):
                    self.add();
                    self.gc()
                    if self.s == '0':
                        cs = 'N0'
                    else:
                        cs = 'N10'
                elif self.ch == '.':
                    if self.digit(self.peek()):
                        self.add();
                        self.gc();
                        cs = 'P1'
                    else:
                        # Точка как самостоятельный символ (если это не начало числа)
                        self.add();
                        self.out(2, self.put(self.TL, key='.'))
                        self.gc();
                        cs = 'H'
                elif self.ch == '/':
                    self.gc();
                    cs = 'C1'
                elif self.ch == '!':
                    self.gc();
                    cs = 'SE'
                elif self.ch == '=':
                    self.gc();
                    cs = 'SEQ'
                elif self.ch == ':':
                    self.gc();
                    cs = 'SC'
                elif self.ch == '|':
                    self.gc();
                    cs = 'SP'
                elif self.ch == '&':
                    self.gc();
                    cs = 'SA'
                elif self.ch == '<':
                    self.gc();
                    cs = 'M1'
                elif self.ch == '>':
                    self.gc();
                    cs = 'M2'
                elif self.ch == '}':
                    self.add();
                    self.out(2, self.TL['}']);
                    self.gc()
                else:
                    cs = 'OG'

            elif cs == 'ID':
                while self.let(self.ch) or self.digit(self.ch): self.add(); self.gc()
                if self.s in self.TW:
                    self.out(1, self.TW[self.s])
                else:
                    k = self.put(self.TI);
                    self.out(4, k)
                cs = 'H'

            # --- Числа ---
            elif cs == 'N0':
                if self.ch.lower() == 'b':
                    if self._is_hex_ctx():
                        self.add();
                        self.gc();
                        cs = 'N16'
                    else:
                        self.add();
                        self.gc();
                        cs = 'B_FIN'
                elif self.ch.lower() == 'o':
                    if self._is_hex_ctx():
                        self.add();
                        self.gc();
                        cs = 'N16'
                    else:
                        self.add();
                        self.gc();
                        cs = 'O_FIN'
                elif self.ch.lower() == 'd':
                    if self._is_hex_ctx():
                        self.add();
                        self.gc();
                        cs = 'N16'
                    else:
                        self.add();
                        self.gc();
                        cs = 'D_FIN'
                elif self.ch.lower() == 'h':
                    self.add();
                    self.gc();
                    cs = 'H_FIN'
                elif self.ch.lower() == 'e':  # 0e
                    if (self.peek() in '+-' or self.digit(self.peek())):
                        self.add();
                        self.gc();
                        cs = 'E1'
                    else:
                        self._add_error(
                            f"Неверный формат числа с экспонентой, ожидался знак или цифра после 'e' в '{self.s + self.ch}'")
                        self.gc();
                        cs = 'H'  # Consume 'e' and reset
                elif self.ch == '.':
                    self.add();
                    self.gc();
                    cs = 'P2'
                elif self.digit(self.ch) or self.is_hex_char(self.ch):
                    self.add();
                    self.gc();
                    cs = 'N16'
                else:
                    z = self.put(self.TN);
                    self.out(3, z);
                    cs = 'H'

            elif cs == 'N10':
                if self.ch.lower() == 'b':
                    if self._is_hex_ctx():
                        self.add();
                        self.gc();
                        cs = 'N16'
                    else:
                        self._add_error(
                            f"Суффикс 'b' (двоичное) не может следовать за ненулевым десятичным числом: {self.s + self.ch}");
                        cs = 'H'
                elif self.ch.lower() == 'd':
                    if self._is_hex_ctx():
                        self.add();
                        self.gc();
                        cs = 'N16'
                    else:
                        self.add();
                        self.gc();
                        cs = 'D_FIN'
                elif self.ch.lower() == 'h':
                    self.add();
                    self.gc();
                    cs = 'H_FIN'
                # ИСПРАВЛЕНИЕ: Обработка 'e'
                elif self.ch.lower() == 'e':
                    if (self.peek() in '+-' or self.digit(self.peek())):
                        self.add();
                        self.gc();
                        cs = 'E1'
                    else:
                        # 123e -> Lexical Error, как запрошено
                        self._add_error(
                            f"Неверный формат числа с экспонентой, ожидался знак или цифра после 'e' в '{self.s + self.ch}'")
                        self.gc();
                        cs = 'H'  # Consume 'e' and reset
                elif self.ch == '.':
                    self.add();
                    self.gc();
                    cs = 'P2'
                elif self.is_hex_char(self.ch):
                    self.add();
                    self.gc();
                    cs = 'N16'
                elif self.digit(self.ch):
                    self.add();
                    self.gc()
                else:
                    z = self.put(self.TN);
                    self.out(3, z);
                    cs = 'H'

            elif cs == 'N16':
                if self.digit(self.ch) or self.is_hex_char(self.ch):
                    self.add();
                    self.gc()
                elif self.ch.lower() == 'h':
                    self.add();
                    self.gc();
                    cs = 'H_FIN'
                else:
                    if self._check_hex(self.s):
                        z = self.put(self.TN);
                        self.out(3, z);
                        cs = 'H'
                    else:
                        self._add_error(f"Неверный символ в шестнадцатеричном числе: {self.s}");
                        cs = 'H'

            elif cs == 'B_FIN':
                if not self._check_binary(self.s[:-1]):
                    self._add_error(f"Неверный формат двоичного числа: {self.s}")
                    cs = 'H'
                else:
                    z = self.put(self.TN);
                    self.out(3, z);
                    cs = 'H'
            elif cs == 'O_FIN':
                if not self._check_octal(self.s[:-1]):
                    self._add_error(f"Неверный формат восьмеричного числа: {self.s}")
                    cs = 'H'
                else:
                    z = self.put(self.TN);
                    self.out(3, z);
                    cs = 'H'
            elif cs == 'D_FIN':
                z = self.put(self.TN);
                self.out(3, z);
                cs = 'H'
            elif cs == 'H_FIN':
                if self._check_hex(self.s[:-1]):
                    z = self.put(self.TN);
                    self.out(3, z);
                    cs = 'H'
                else:
                    self._add_error(f"Неверный формат шестнадцатеричного числа: {self.s}");
                    cs = 'H'

            elif cs == 'P1':
                if self.digit(self.ch):
                    self.add();
                    self.gc();
                    cs = 'P2'
                else:
                    self._add_error("Ожидалась цифра после точки");
                    cs = 'H'
            elif cs == 'P2':
                while self.digit(self.ch): self.add(); self.gc()
                if self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E1'
                else:
                    z = self.put(self.TN);
                    self.out(3, z);
                    cs = 'H'
            elif cs == 'E1':
                if self.digit(self.ch) or self.ch in '+-':
                    self.add();
                    self.gc();
                    cs = 'E2'
                else:
                    self._add_error("Ошибка в экспоненте: ожидалась цифра или знак");
                    cs = 'H'
            elif cs == 'E2':
                while self.digit(self.ch): self.add(); self.gc()
                z = self.put(self.TN);
                self.out(3, z);
                cs = 'H'

            elif cs == 'C1':
                if self.ch == '*':
                    self.gc();
                    cs = 'C2'
                else:
                    self.s = '/';
                    self.out(2, self.TL['/']);
                    cs = 'H'
            elif cs == 'C2':
                # Пропускаем все, пока не найдем *
                while self.ch and self.ch != '*':
                    self.gc()
                if not self.ch:
                    self._add_error("Незакрытый многострочный комментарий (ожидалось '*/')");
                    cs = 'E'
                else:
                    self.gc();
                    cs = 'C3'
            elif cs == 'C3':
                if self.ch == '/':
                    self.gc();
                    cs = 'H'
                else:
                    cs = 'C2'

            elif cs == 'SE':
                if self.ch == '=':
                    self.s = '!=';
                    self.out(2, self.TL['!=']);
                    self.gc()
                else:
                    self.s = '!';
                    self.out(2, self.TL['!'])
                cs = 'H'
            elif cs == 'SEQ':
                if self.ch == '=':
                    self.s = '==';
                    self.out(2, self.TL['==']);
                    self.gc()
                else:
                    self.s = '=';
                    self.out(2, self.TL['='])
                cs = 'H'
            elif cs == 'SC':
                if self.ch == '=':
                    self.s = ':=';
                    self.out(2, self.TL[':=']);
                    self.gc()
                else:
                    self.s = ':';
                    self.out(2, self.TL[':'])
                cs = 'H'
            elif cs == 'SP':
                if self.ch == '|':
                    self.s = '||';
                    self.out(2, self.TL['||']);
                    self.gc();
                    cs = 'H'
                else:
                    self._add_error("Ожидался второй '|' для оператора '||'");
                    cs = 'H'
            elif cs == 'SA':
                if self.ch == '&':
                    self.s = '&&';
                    self.out(2, self.TL['&&']);
                    self.gc();
                    cs = 'H'
                else:
                    self._add_error("Ожидался второй '&' для оператора '&&'");
                    cs = 'H'
            elif cs == 'M1':
                if self.ch == '=':
                    self.s = '<=';
                    self.out(2, self.TL['<=']);
                    self.gc()
                else:
                    self.s = '<';
                    self.out(2, self.TL['<'])
                cs = 'H'
            elif cs == 'M2':
                if self.ch == '=':
                    self.s = '>=';
                    self.out(2, self.TL['>=']);
                    self.gc()
                else:
                    self.s = '>';
                    self.out(2, self.TL['>'])
                cs = 'H'
            elif cs == 'OG':
                self.add()
                if self.s in self.TL:
                    self.out(2, self.TL[self.s]);
                    self.gc();
                    cs = 'H'
                else:
                    self._add_error(f"Неизвестный символ: {self.s}");
                    self.gc();
                    cs = 'H'

        return self.tokens, self.errors

    def _is_hex_ctx(self):
        if self.ptr + 1 >= len(self.source_code): return False
        c = self.source_code[self.ptr + 1]
        return self.digit(c) or self.is_hex_char(c) or c.lower() == 'h'

    def _check_hex(self, s):
        if not s: return False
        return all(c.upper() in '0123456789ABCDEF' for c in s)

    def _check_binary(self, s):
        if not s: return False
        return all(c in '01' for c in s)

    def _check_octal(self, s):
        if not s: return False
        return all(c in '01234567' for c in s)


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
        if not t: return "КОНЕЦ ПРОГРАММЫ"
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
        self.match(2, self.TL['{'], expected_desc="'{' (Начало блока)")
        self.validate_balance()

        while True:
            t = self.current()
            if not t: break
            if t['class'] == 2 and t['code'] == self.TL['}']: break

            if t['class'] == 1 and t['code'] in [self.TW['int'], self.TW['float'], self.TW['bool']]:
                self.parse_declaration()
            else:
                self.parse_statement()

            nt = self.current()
            if nt and nt['class'] == 2 and nt['code'] == self.TL[';']:
                self.match(2, self.TL[';'], expected_desc="';' (Разделитель команд)")
            elif nt and nt['class'] == 2 and nt['code'] == self.TL['}']:
                pass
            else:
                raise SyntaxError("Ожидалась ';' (точка с запятой) после команды")

        self.match(2, self.TL['}'], expected_desc="'}' (Конец блока)")
        self.log("Конец программы: найдено '}'")

    def parse_declaration(self):
        self.log("  Объявление переменных")
        self.match(1, expected_desc="Тип данных (int, float, bool)")
        self.match(4, expected_desc="Идентификатор")
        while True:
            if self.current() and self.current()['code'] == self.TL[',']:
                self.match(2, self.TL[','], expected_desc="','")
                self.match(4, expected_desc="Идентификатор")
            else:
                break

    def parse_statement(self):
        t = self.current()
        if not t: return

        # --- ИСПРАВЛЕНИЕ: Если видим точку с запятой, считаем это пустым оператором и выходим ---
        if t['class'] == 2 and t['code'] == self.TL[';']:
            return
        # -------------------------------------------------------------------------------------

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
        assign_code = self.TL.get(':=', self.TL.get(':', 8))
        self.match(2, assign_code, val=':=', expected_desc="':='")
        self.parse_expression()

    def parse_if(self):
        self.log("  Условный оператор (If)")
        self.match(1, self.TW['if'], expected_desc="'if'")
        self.match(2, self.TL['('], expected_desc="'('")
        self.parse_expression()
        self.match(2, self.TL[')'], expected_desc="')'")

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

        t_id = self.current()
        next_t = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None

        if t_id and t_id['class'] == 4 and next_t and next_t['value'] == ':=':
            self.parse_assignment()
        else:
            raise SyntaxError("Ожидалось присваивание (ID := Expression) в цикле For")

        self.match(1, self.TW['to'], expected_desc="'to' (Ключевое слово)")
        self.parse_expression()

        t = self.current()
        if t and t['class'] == 1 and t['code'] == self.TW.get('step'):
            self.match(1, self.TW['step'], expected_desc="'step'")
            self.parse_expression()

        # Тело цикла
        self.parse_statement()

        # Если тело закончилось точкой с запятой, съедаем её, чтобы не мешала next
        if self.current() and self.current()['code'] == self.TL[';']:
            self.match(2, self.TL[';'], expected_desc="';'")

        self.match(1, self.TW['next'], expected_desc="'next' (Конец цикла)")

    def parse_while(self):
        self.log("  Цикл While")
        self.match(1, self.TW['while'], expected_desc="'while'")
        self.match(2, self.TL['('], expected_desc="'('")
        self.parse_expression()
        self.match(2, self.TL[')'], expected_desc="')'")
        if 'do' in self.TW:
            self.match(1, self.TW['do'], expected_desc="'do'")
        self.parse_statement()

    def parse_compound(self):
        self.log("  Составной оператор (Begin...End)")
        self.match(1, self.TW['begin'], expected_desc="'begin'")

        t = self.current()
        if t and not (t['class'] == 1 and t['code'] == self.TW['end']):
            self.parse_statement()

        while True:
            t = self.current()
            if t and t['class'] == 2 and t['code'] == self.TL[';']:
                if self.pos + 1 < len(self.tokens):
                    nt = self.tokens[self.pos + 1]
                    if nt['class'] == 1 and nt['code'] == self.TW.get('end'):
                        self.match(2, self.TL[';'])
                        break
                self.match(2, self.TL[';'])
                self.parse_statement()
            else:
                break

        self.match(1, self.TW['end'], expected_desc="'end'")

    def parse_io(self, is_r):
        self.log(f"  Ввод/Вывод ({'Read' if is_r else 'Write'})")
        self.match(1, self.TW['readln'] if is_r else self.TW['writeln'], expected_desc="'readln' или 'writeln'")

        if is_r:
            self.match(4, expected_desc="ID переменной")
            while self.current() and self.current()['code'] == self.TL[',']:
                self.match(2, self.TL[','], expected_desc="','")
                self.match(4, expected_desc="ID переменной")
        else:
            self.parse_expression()
            while self.current() and self.current()['code'] == self.TL[',']:
                self.match(2, self.TL[','], expected_desc="','")
                self.parse_expression()

    def parse_expression(self):
        self.parse_simple()
        t = self.current()
        if t and t['class'] == 2 and t['code'] in [self.TL.get('!='), self.TL.get('=='), self.TL.get('<'),
                                                   self.TL.get('<='),
                                                   self.TL.get('>'), self.TL.get('>=')]:
            self.match(2, expected_desc="Оператор отношения")
            self.parse_simple()

    def parse_simple(self):
        self.parse_term()
        t = self.current()
        while t and t['class'] == 2 and t['code'] in [self.TL.get('+'), self.TL.get('-'), self.TL.get('||')]:
            self.match(2, expected_desc="Оператор (+, -, ||)")
            self.parse_term()
            t = self.current()

    def parse_term(self):
        self.parse_fact()
        t = self.current()
        while t and t['class'] == 2 and t['code'] in [self.TL.get('*'), self.TL.get('/'), self.TL.get('&&')]:
            self.match(2, expected_desc="Оператор (*, /, &&)")
            self.parse_fact()
            t = self.current()

    def parse_fact(self):
        t = self.current()
        if not t: raise SyntaxError("Ожидался операнд")

        if t['class'] == 4:
            self.match(4, expected_desc="Идентификатор")
        elif t['class'] == 3:
            self.match(3, expected_desc="Число")
        elif t['code'] == self.TL.get('('):
            self.match(2, self.TL['('], expected_desc="'('")
            self.parse_expression()
            self.match(2, self.TL[')'], expected_desc="')'")
        elif t['code'] == self.TL.get('!'):
            self.match(2, self.TL['!'], expected_desc="'!'")
            self.parse_fact()
        elif t['code'] in [self.TW.get('true'), self.TW.get('false')]:
            self.match(1, expected_desc="Логическое значение")
        else:
            raise SyntaxError(f"Неверный операнд: {self._get_token_info(t)}")
# ==========================================
# 3. GUI (APP)
# ==========================================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор (Scan -> Parse -> Dec)")
        self.root.geometry("1200x850")
        ctk.set_appearance_mode("System")

        # Top
        top_frame = ctk.CTkFrame(root, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(top_frame, text="Исходный код:", font=("Arial", 12, "bold")).pack(anchor="w")
        self.input_text = ctk.CTkTextbox(top_frame, height=180, font=("Consolas", 12))
        self.input_text.pack(fill="both", pady=5)

        # Обратите внимание: writeln 123e; удален, так как он должен вызывать ошибку.
        # Вместо него оставлено writeln 123;
        sample = """{
    int i, sum;
    
    /* 1. Простой вывод счетчика (одиночная команда) */
    for i := 1 to 5 step 1
       sum := sum + i;
    next;

    /* 2. Подсчет суммы (одиночное присваивание) */
    sum := 0;
    for i := 1 to 10
        sum := sum + i;
    next;

    writeln sum;
}"""
        self.input_text.insert(INSERT, sample)

        # Buttons
        btn_frame = ctk.CTkFrame(root, fg_color="transparent")
        btn_frame.pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(btn_frame, text="Анализировать", command=self.run_process).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Очистить", command=self.clear, fg_color="gray").pack(side="left", padx=5)


        # Tabs
        self.tabview = ctk.CTkTabview(root)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=10)

        self.out_parse = self._mk_tab("Синтаксис")
        self.out_tokens = self._mk_tab("Токены")
        self.out_tables = self.tabview.add("Таблицы")
        self.out_errors = self._mk_tab("Ошибки")

        # Grid for tables
        self.out_tables.grid_columnconfigure(0, weight=1);
        self.out_tables.grid_columnconfigure(1, weight=1)
        self.out_tables.grid_rowconfigure(0, weight=1);
        self.out_tables.grid_rowconfigure(1, weight=1)
        self.txt_tw = self._mk_table_box("1. KW (Ключевые слова)", 0, 0)
        self.txt_tl = self._mk_table_box("2. Delim (Разделители)", 0, 1)
        self.txt_ti = self._mk_table_box("3. ID (Идентификаторы)", 1, 0)
        self.txt_tn = self._mk_table_box("4. Numbers (с переводом)", 1, 1)

        self.scanner = Scanner()

    def _mk_tab(self, name):
        tab = self.tabview.add(name)
        t = ctk.CTkTextbox(tab, font=("Consolas", 12))
        t.pack(fill="both", expand=True)
        return t

    def _mk_table_box(self, t, r, c):
        f = ctk.CTkFrame(self.out_tables)
        f.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
        ctk.CTkLabel(f, text=t, font=("Arial", 10, "bold")).pack(anchor="w", padx=5)
        b = ctk.CTkTextbox(f, font=("Consolas", 11))
        b.pack(fill="both", expand=True)
        return b

    def _get_decimal_value(self, lexeme):
        val = "Nan/Err"
        s = lexeme
        try:
            if s.lower().endswith('h'):
                val = int(s[:-1], 16)
            elif s.lower().endswith('b'):
                val = int(s[:-1], 2)
            elif s.lower().endswith('o'):
                val = int(s[:-1], 8)
            elif s.lower().endswith('d'):
                val = int(s[:-1])
            elif '.' in s or 'e' in s.lower():
                val = float(s)
            else:
                if any(c.lower() in 'abcdef' for c in s):
                    val = int(s, 16)
                else:
                    val = int(s)
        except ValueError:
            val = "Ошибка конвертации"
        return val

    def run_process(self):
        code = self.input_text.get("1.0", END).strip()
        self.clear_outputs()
        if not code: return

        tokens, errs = self.scanner.scan(code)

        self.out_tokens.insert(INSERT, f"{'C':<3}|{'Code':<4}|{'Value':<10}|Line:Col\n" + ("-" * 30) + "\n")
        for t in tokens:
            pos_info = f"{t.get('line', '?'):<4}:{t.get('col', '?')}"
            self.out_tokens.insert(INSERT, f"{t['class']:<3}|{t['code']:<4}|{t['value']:<10}|{pos_info}\n")

        self._fill_kv(self.txt_tw, self.scanner.TW)
        self._fill_kv(self.txt_tl, self.scanner.TL)
        self._fill_kv(self.txt_ti, self.scanner.TI)

        self.txt_tn.delete("1.0", END)
        self.txt_tn.insert(INSERT, f"{'Лексема':<15}|{'Код':<3}| Значение (Dec)\n" + ("-" * 35) + "\n")
        items = sorted(self.scanner.TN.items(), key=lambda x: x[1])
        for lex, code_id in items:
            dec_val = self._get_decimal_value(lex)
            self.txt_tn.insert(INSERT, f"{lex:<15}|{code_id:<3}| {dec_val}\n")

        if errs:
            self.out_errors.insert(INSERT, "❌ ЛЕКСИЧЕСКИЕ ОШИБКИ:\n")
            for e in errs: self.out_errors.insert(INSERT, f" -> {e}\n")
            self.tabview.set("Ошибки")
            return

        self.out_parse.insert(INSERT, "Start Parsing...\n")
        parser = Parser(
            tokens,
            self.scanner.TW,
            self.scanner.TL,
            self.scanner.TI,
            self.scanner.TN,
            self.scanner.REV_TW,
            self.scanner.REV_TL
        )

        try:
            parser.parse_program()
            for m in parser.log_messages: self.out_parse.insert(INSERT, f" -> {m}\n")
            self.out_parse.insert(INSERT, "\n✅ Синтаксический анализ успешно завершен!")
            self.tabview.set("Синтаксис")
        except SyntaxError as e:
            self.out_errors.insert(INSERT, f"❌ СИНТАКСИЧЕСКАЯ ОШИБКА:\n")
            self.out_errors.insert(INSERT, f" -> {str(e)}\n\n")
            self.out_errors.insert(INSERT, "📜 Контекст (последние шаги):\n")
            for m in parser.log_messages[-7:]:
                self.out_errors.insert(INSERT, f" -> {m}\n")
            self.tabview.set("Ошибки")

    def _fill_kv(self, w, d):
        w.delete("1.0", END)
        w.insert(INSERT, f"{'Key':<15}| ID\n" + ("-" * 20) + "\n")
        for k, v in sorted(d.items(), key=lambda x: x[1]):
            w.insert(INSERT, f"{k:<15}| {v}\n")

    def clear(self):
        self.input_text.delete("1.0", END)
        self.clear_outputs()

    def clear_outputs(self):
        self.out_parse.delete("1.0", END)
        self.out_tokens.delete("1.0", END)
        self.out_errors.delete("1.0", END)
        self.txt_tw.delete("1.0", END)
        self.txt_tl.delete("1.0", END)
        self.txt_ti.delete("1.0", END)
        self.txt_tn.delete("1.0", END)


if __name__ == "__main__":
    root = ctk.CTk()
    app = App(root)
    root.mainloop()