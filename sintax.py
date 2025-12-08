import customtkinter as ctk
from tkinter import END, INSERT


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
            '<=': 21, '>=': 22, '==': 23, '!': 24
        }
        # Обратные словари
        self.REV_TW = {v: k for k, v in self.TW.items()}
        self.REV_TL = {v: k for k, v in self.TL.items()}

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
        self.tokens.append({"class": n, "code": k, "value": self.s})

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
                        self.add();
                        self.out(2, 11);
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
                    self.out(2, 2);
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
                elif self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E1'
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
                        self.errors.append("Ошибка: суффикс 'b' у десятичного числа");
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
                elif self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E1'
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
                        self.errors.append(f"Ошибка Hex: {self.s}");
                        cs = 'H'

            elif cs == 'B_FIN':
                z = self.put(self.TN);
                self.out(3, z);
                cs = 'H'
            elif cs == 'O_FIN':
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
                    self.errors.append(f"Неверный Hex: {self.s}");
                    cs = 'H'

            elif cs == 'P1':
                if self.digit(self.ch):
                    self.add();
                    self.gc();
                    cs = 'P2'
                else:
                    self.errors.append("Ожидалась цифра после точки");
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
                    self.errors.append("Ошибка в экспоненте");
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
                    self.out(2, 16);
                    self.gc()
            elif cs == 'C2':
                while self.ch and self.ch != '*': self.gc()
                if not self.ch:
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
                    self.out(2, 18);
                    self.gc()
                else:
                    self.s = '!';
                    self.out(2, 24)
                cs = 'H'
            elif cs == 'SEQ':
                if self.ch == '=':
                    self.s = '==';
                    self.out(2, 23);
                    self.gc()
                else:
                    self.s = '=';
                    self.out(2, 15)
                cs = 'H'
            elif cs == 'SC':
                if self.ch == '=':
                    self.s = ':=';
                    self.out(2, 8);
                    self.gc()
                else:
                    self.s = ':';
                    self.out(2, 8)
                cs = 'H'
            elif cs == 'SP':
                if self.ch == '|':
                    self.s = '||';
                    self.out(2, 14);
                    self.gc();
                    cs = 'H'
                else:
                    self.errors.append("Ожидался второй '|'");
                    cs = 'H'
            elif cs == 'SA':
                if self.ch == '&':
                    self.s = '&&';
                    self.out(2, 17);
                    self.gc();
                    cs = 'H'
                else:
                    self.errors.append("Ожидался второй '&'");
                    cs = 'H'
            elif cs == 'M1':
                if self.ch == '=':
                    self.s = '<=';
                    self.out(2, 21);
                    self.gc()
                else:
                    self.s = '<';
                    self.out(2, 20)
                cs = 'H'
            elif cs == 'M2':
                if self.ch == '=':
                    self.s = '>=';
                    self.out(2, 22);
                    self.gc()
                else:
                    self.s = '>';
                    self.out(2, 19)
                cs = 'H'
            elif cs == 'OG':
                self.add()
                if self.s in self.TL:
                    self.out(2, self.TL[self.s]);
                    self.gc();
                    cs = 'H'
                else:
                    self.errors.append(f"Неизвестный символ: {self.s}");
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


# ==========================================
# 2. СИНТАКСИЧЕСКИЙ АНАЛИЗАТОР (PARSER)
# ==========================================
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

        # Пропуск пустой команды (;)
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

        # Если после оператора стоит ;, съедаем её
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
# 3. СЕМАНТИЧЕСКИЙ АНАЛИЗАТОР
# ==========================================
class SemanticAnalyzer:
    def __init__(self, tokens, ti, tn, tw, tl, rev_tw):
        self.tokens = tokens
        self.TI = ti
        self.TN = tn
        self.TW = tw
        self.TL = tl
        self.REV_TW = rev_tw

        # Таблица символов: {id: {'type': тип, 'declared': bool, 'initialized': bool}}
        self.symbol_table = {}

        # Текущий контекст (для проверки вложенных блоков)
        self.current_context = []

        # Типы операций
        self.arithmetic_ops = [tl['+'], tl['-'], tl['*'], tl['/']]
        self.relational_ops = [tl['<'], tl['<='], tl['>'], tl['>='], tl['=='], tl['!=']]
        self.logical_ops = [tl['||'], tl['&&'], tl['!']]

        self.errors = []
        self.warnings = []
        self.log_messages = []

    def log(self, msg):
        self.log_messages.append(msg)

    def error(self, msg, token=None):
        if token:
            pos = self._find_token_position(token)
            self.errors.append(f"Семантическая ошибка (позиция {pos}): {msg}")
        else:
            self.errors.append(f"Семантическая ошибка: {msg}")

    def warning(self, msg, token=None):
        if token:
            pos = self._find_token_position(token)
            self.warnings.append(f"Семантическое предупреждение (позиция {pos}): {msg}")
        else:
            self.warnings.append(f"Семантическое предупреждение: {msg}")

    def _find_token_position(self, token):
        for i, t in enumerate(self.tokens):
            if t == token:
                return i
        return "неизвестно"

    def analyze(self):
        self.log("Начало семантического анализа")

        try:
            self._analyze_tokens()
            self._check_uninitialized_vars()

            if not self.errors:
                self.log("Семантический анализ завершен успешно")
        except Exception as e:
            self.error(f"Ошибка во время семантического анализа: {str(e)}")

        return self.errors, self.warnings

    def _analyze_tokens(self):
        i = 0
        while i < len(self.tokens):
            token = self.tokens[i]

            # Проверка объявления переменных
            if token['class'] == 1 and token['code'] in [self.TW['int'], self.TW['float'], self.TW['bool']]:
                var_type = self.REV_TW[token['code']]
                i += 1

                # Переменные после типа
                while i < len(self.tokens) and self.tokens[i]['class'] == 4:
                    var_name = self.tokens[i]['value']

                    # Проверка повторного объявления
                    if var_name in self.symbol_table:
                        self.error(f"Переменная '{var_name}' уже объявлена", self.tokens[i])
                    else:
                        self.symbol_table[var_name] = {
                            'type': var_type,
                            'declared': True,
                            'initialized': False,
                            'used': False
                        }
                        self.log(f"  Объявлена переменная '{var_name}' типа {var_type}")

                    i += 1

                    # Проверка следующего токена (запятая или точка с запятой)
                    if i < len(self.tokens) and self.tokens[i]['code'] == self.TL[',']:
                        i += 1
                    elif i < len(self.tokens) and self.tokens[i]['code'] == self.TL[';']:
                        break

            # Проверка присваивания
            elif token['class'] == 4 and i + 1 < len(self.tokens) and self.tokens[i + 1]['value'] == ':=':
                var_name = token['value']

                # Проверка объявления переменной
                if var_name not in self.symbol_table:
                    self.error(f"Использование необъявленной переменной '{var_name}'", token)
                else:
                    self.symbol_table[var_name]['used'] = True

                # Пропускаем :=
                i += 2

                # Анализ правой части выражения
                expr_end = self._find_expression_end(i)
                expr_tokens = self.tokens[i:expr_end]
                self._analyze_expression(expr_tokens, var_name)
                i = expr_end

            # Проверка использования в выражениях
            elif token['class'] == 4:
                var_name = token['value']
                if var_name in self.symbol_table:
                    self.symbol_table[var_name]['used'] = True

            i += 1

    def _find_expression_end(self, start):
        i = start
        paren_count = 0

        while i < len(self.tokens):
            token = self.tokens[i]

            if token['class'] == 2:
                if token['code'] == self.TL['(']:
                    paren_count += 1
                elif token['code'] == self.TL[')']:
                    if paren_count > 0:
                        paren_count -= 1
                    else:
                        break
                elif token['code'] == self.TL[';'] and paren_count == 0:
                    break
                elif token['code'] == self.TL[','] and paren_count == 0:
                    break
                elif token['code'] == self.TL['}'] and paren_count == 0:
                    break

            i += 1

        return i

    def _analyze_expression(self, expr_tokens, target_var=None):
        if not expr_tokens:
            return None

        # Анализ типа выражения
        expr_type = self._get_expression_type(expr_tokens)

        # Если есть целевая переменная, проверяем совместимость типов
        if target_var and target_var in self.symbol_table:
            target_type = self.symbol_table[target_var]['type']

            # Проверка инициализации
            self.symbol_table[target_var]['initialized'] = True

            # Проверка совместимости типов
            if expr_type and not self._types_compatible(target_type, expr_type):
                self.error(
                    f"Несовместимость типов: нельзя присвоить выражение типа '{expr_type}' переменной типа '{target_type}'",
                    expr_tokens[0])

        return expr_type

    def _get_expression_type(self, tokens):
        if not tokens:
            return None

        # Если один токен
        if len(tokens) == 1:
            token = tokens[0]

            if token['class'] == 4:  # Идентификатор
                var_name = token['value']
                if var_name in self.symbol_table:
                    return self.symbol_table[var_name]['type']
                else:
                    self.error(f"Использование необъявленной переменной '{var_name}'", token)
                    return None

            elif token['class'] == 3:  # Число
                # Определяем тип числа
                num_val = token['value']
                if '.' in num_val or 'e' in num_val.lower():
                    return 'float'
                else:
                    # Проверяем, не является ли это hex/oct/binary числом
                    if num_val.lower().endswith('h'):
                        return 'int'
                    elif num_val.lower().endswith('b') or num_val.lower().endswith('o'):
                        return 'int'
                    elif num_val.lower().endswith('d'):
                        return 'int'
                    elif any(c.lower() in 'abcdef' for c in num_val):
                        return 'int'  # Hex без суффикса
                    else:
                        return 'int'

            elif token['class'] == 1:  # Ключевое слово
                if token['code'] in [self.TW['true'], self.TW['false']]:
                    return 'bool'

        # Если есть операторы
        op_positions = []
        for i, token in enumerate(tokens):
            if token['class'] == 2:
                op_positions.append((i, token['code']))

        # Проверка операторов
        for pos, op_code in op_positions:
            if op_code in self.arithmetic_ops:
                left_type = self._get_expression_type(tokens[:pos])
                right_type = self._get_expression_type(tokens[pos + 1:]) if pos + 1 < len(tokens) else None

                # Арифметические операции требуют числовых типов
                if left_type and left_type not in ['int', 'float']:
                    self.error(f"Неверный тип для арифметической операции: '{left_type}'", tokens[0])

                if right_type and right_type not in ['int', 'float']:
                    self.error(f"Неверный тип для арифметической операции: '{right_type}'",
                               tokens[pos + 1] if pos + 1 < len(tokens) else tokens[-1])

                # Результирующий тип - более широкий из двух
                if left_type == 'float' or right_type == 'float':
                    return 'float'
                elif left_type == 'int' and right_type == 'int':
                    return 'int'
                elif left_type == 'int' and right_type is None:
                    return 'int'
                elif left_type is None and right_type == 'int':
                    return 'int'
                else:
                    return None  # Неопределенный тип

            elif op_code in self.relational_ops:
                left_type = self._get_expression_type(tokens[:pos])
                right_type = self._get_expression_type(tokens[pos + 1:]) if pos + 1 < len(tokens) else None

                # Отношения требуют совместимых типов
                if left_type and right_type and not self._types_comparable(left_type, right_type):
                    self.error(f"Несравнимые типы: '{left_type}' и '{right_type}'", tokens[pos])

                return 'bool'

            elif op_code in self.logical_ops:
                left_type = self._get_expression_type(tokens[:pos])
                if op_code != self.TL['!']:  # Унарный !
                    right_type = self._get_expression_type(tokens[pos + 1:]) if pos + 1 < len(self.tokens) else None

                # Логические операции требуют булевых типов
                if left_type and left_type != 'bool':
                    self.error(f"Неверный тип для логической операции: '{left_type}'", tokens[0])

                if op_code != self.TL['!'] and right_type and right_type != 'bool':
                    self.error(f"Неверный тип для логической операции: '{right_type}'",
                               tokens[pos + 1] if pos + 1 < len(tokens) else tokens[-1])

                return 'bool'

        # Если выражение в скобках
        if tokens and tokens[0]['code'] == self.TL['('] and tokens[-1]['code'] == self.TL[')']:
            return self._get_expression_type(tokens[1:-1])

        return None

    def _types_compatible(self, target_type, expr_type):
        # Правила совместимости типов для присваивания
        # int <- int
        # float <- int или float
        # bool <- bool

        if not expr_type:  # Если тип выражения не определен
            return True  # Пропускаем проверку

        compatibility = {
            'int': ['int'],
            'float': ['int', 'float'],
            'bool': ['bool']
        }

        if target_type not in compatibility:
            return False

        return expr_type in compatibility[target_type]

    def _types_comparable(self, type1, type2):
        # Правила сравнения типов
        comparable_pairs = [
            ('int', 'int'),
            ('int', 'float'),
            ('float', 'int'),
            ('float', 'float'),
            ('bool', 'bool')
        ]

        return (type1, type2) in comparable_pairs or (type2, type1) in comparable_pairs

    def _check_uninitialized_vars(self):
        # Проверка использования неинициализированных переменных
        for var_name, info in self.symbol_table.items():
            if info['used'] and not info['initialized']:
                self.warning(f"Использование неинициализированной переменной '{var_name}'")

    def get_symbol_table_report(self):
        report = "ТАБЛИЦА СИМВОЛОВ:\n"
        report += "=" * 50 + "\n"
        report += f"{'Имя':<15} {'Тип':<10} {'Объявлена':<12} {'Инициализирована':<18} {'Использована':<15}\n"
        report += "-" * 70 + "\n"

        for var_name, info in self.symbol_table.items():
            report += f"{var_name:<15} {info['type']:<10} "
            report += f"{'Да':<12} {'Да' if info['initialized'] else 'Нет':<18} {'Да' if info['used'] else 'Нет':<15}\n"

        return report


# ==========================================
# 4. GUI (APP)
# ==========================================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор (Scan -> Parse -> Sem)")
        self.root.geometry("1200x900")
        ctk.set_appearance_mode("System")

        # Top
        top_frame = ctk.CTkFrame(root, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(top_frame, text="Исходный код:", font=("Arial", 12, "bold")).pack(anchor="w")
        self.input_text = ctk.CTkTextbox(top_frame, height=180, font=("Consolas", 12))
        self.input_text.pack(fill="both", pady=5)

        # Обновленный пример с семантическими проверками
        sample = """{
    int i, sum, count;
    float avg, pi;
    bool flag, ready;

    sum := 0;
    count := 5;
    pi := 3.14;
    flag := true;

    /* Корректные операции */
    avg := sum / count;

    /* Семантические ошибки */
    sum := flag;       /* Ошибка: несовместимость типов */
    result := 10;      /* Ошибка: необъявленная переменная */
    ready := count;    /* Ошибка: несовместимость типов */

    /* Цикл */
    for i := 1 to 10 step 1 begin
        sum := sum + i;
        writeln sum
    end next;

    writeln avg, pi
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
        self.out_semantic = self._mk_tab("Семантический")
        self.out_tokens = self._mk_tab("Токены")
        self.out_tables = self.tabview.add("Таблицы")
        self.out_errors = self._mk_tab("Ошибки")

        # Grid for tables
        self.out_tables.grid_columnconfigure(0, weight=1);
        self.out_tables.grid_columnconfigure(1, weight=1)
        self.out_tables.grid_rowconfigure(0, weight=1);
        self.out_tables.grid_rowconfigure(1, weight=1)
        self.txt_tw = self._mk_table_box("1. KW", 0, 0)
        self.txt_tl = self._mk_table_box("2. Delim", 0, 1)
        self.txt_ti = self._mk_table_box("3. ID", 1, 0)
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
                is_hex = False
                if 'e' in s.lower() and '.' not in s:
                    idx = s.lower().find('e')
                    suffix = s[idx + 1:]
                    if not suffix or (suffix[0] not in '+-' and not suffix[0].isdigit()): is_hex = True
                if is_hex:
                    val = int(s, 16)
                else:
                    val = float(s)
            else:
                if any(c.lower() in 'abcdef' for c in s):
                    val = int(s, 16)
                else:
                    val = int(s)
        except:
            try:
                val = int(s, 16)
            except:
                pass
        return val

    def run_process(self):
        code = self.input_text.get("1.0", END).strip()
        self.clear_outputs()
        if not code: return

        tokens, errs = self.scanner.scan(code)

        for t in tokens:
            self.out_tokens.insert(INSERT, f"{t['class']}|{t['code']:<2}| {t['value']}\n")

        self._fill_kv(self.txt_tw, self.scanner.TW)
        self._fill_kv(self.txt_tl, self.scanner.TL)
        self._fill_kv(self.txt_ti, self.scanner.TI)

        self.txt_tn.delete("1.0", END)
        self.txt_tn.insert(INSERT, f"{'Лексема':<15}|{'Код':<3}| Значение\n" + ("-" * 35) + "\n")
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
            self.out_parse.insert(INSERT, "\n✅ Синтаксический анализ завершен успешно!\n")

            # Запуск семантического анализа
            self.out_semantic.insert(INSERT, "Start Semantic Analysis...\n")
            semantic = SemanticAnalyzer(
                tokens,
                self.scanner.TI,
                self.scanner.TN,
                self.scanner.TW,
                self.scanner.TL,
                self.scanner.REV_TW
            )

            errors, warnings = semantic.analyze()

            # Вывод логов семантического анализа
            for m in semantic.log_messages:
                self.out_semantic.insert(INSERT, f" -> {m}\n")

            # Вывод таблицы символов
            self.out_semantic.insert(INSERT, "\n" + semantic.get_symbol_table_report())

            # Вывод ошибок и предупреждений
            if errors:
                self.out_semantic.insert(INSERT, "\n❌ СЕМАНТИЧЕСКИЕ ОШИБКИ:\n")
                for e in errors: self.out_semantic.insert(INSERT, f" -> {e}\n")

            if warnings:
                self.out_semantic.insert(INSERT, "\n⚠️ СЕМАНТИЧЕСКИЕ ПРЕДУПРЕЖДЕНИЯ:\n")
                for w in warnings: self.out_semantic.insert(INSERT, f" -> {w}\n")

            if not errors:
                self.out_semantic.insert(INSERT, "\n✅ Семантический анализ завершен успешно!\n")

            # Показываем вкладку семантического анализа
            self.tabview.set("Семантический")

        except SyntaxError as e:
            self.out_errors.insert(INSERT, f"❌ СИНТАКСИЧЕСКАЯ ОШИБКА:\n")
            self.out_errors.insert(INSERT, f"{str(e)}\n\n")
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
        self.out_semantic.delete("1.0", END)
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