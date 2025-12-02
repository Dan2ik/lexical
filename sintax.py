import customtkinter as ctk
from tkinter import END, INSERT


# ==========================================
# 1. ЛЕКСИЧЕСКИЙ АНАЛИЗАТОР (SCANNER)
# ==========================================
class Scanner:
    def __init__(self):
        # --- Таблицы лексем ---
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
                        self.add(); self.gc(); cs = 'P1'
                    else:
                        self.add(); self.out(2, 11); self.gc(); cs = 'H'
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

            elif cs == 'ID':
                while self.let(self.ch) or self.digit(self.ch): self.add(); self.gc()
                if self.s in self.TW:
                    self.out(1, self.TW[self.s])
                else:
                    k = self.put(self.TI); self.out(4, k)
                cs = 'H'

            # --- Логика чисел (Объединенная) ---
            elif cs == 'N0':  # Начинается с 0
                if self.ch.lower() == 'b':  # 0b...
                    if self._is_hex_ctx():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'B_FIN'
                elif self.ch.lower() == 'o':  # 0o...
                    if self._is_hex_ctx():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'O_FIN'
                elif self.ch.lower() == 'd':
                    if self._is_hex_ctx():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'D_FIN'
                elif self.ch.lower() == 'h':
                    self.add(); self.gc(); cs = 'H_FIN'
                elif self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E1'
                elif self.ch == '.':
                    self.add(); self.gc(); cs = 'P2'
                elif self.digit(self.ch) or self.is_hex_char(self.ch):
                    self.add();
                    self.gc();
                    cs = 'N16'
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'

            elif cs == 'N10':  # Начинается с 1-9
                if self.ch.lower() == 'b':
                    if self._is_hex_ctx():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.errors.append("Err 'b' on decimal"); cs = 'H'
                elif self.ch.lower() == 'd':
                    if self._is_hex_ctx():
                        self.add(); self.gc(); cs = 'N16'
                    else:
                        self.add(); self.gc(); cs = 'D_FIN'
                elif self.ch.lower() == 'h':
                    self.add(); self.gc(); cs = 'H_FIN'
                elif self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E1'
                elif self.ch == '.':
                    self.add(); self.gc(); cs = 'P2'
                elif self.is_hex_char(self.ch):
                    self.add(); self.gc(); cs = 'N16'
                elif self.digit(self.ch):
                    self.add(); self.gc()
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'

            elif cs == 'N16':  # Потенциальный Hex
                if self.digit(self.ch) or self.is_hex_char(self.ch):
                    self.add(); self.gc()
                elif self.ch.lower() == 'h':
                    self.add(); self.gc(); cs = 'H_FIN'
                else:
                    if self._check_hex(self.s):
                        z = self.put(self.TN); self.out(3, z); cs = 'H'
                    else:
                        self.errors.append(f"Bad Hex: {self.s}"); cs = 'H'

            # Финализаторы суффиксов
            elif cs == 'B_FIN':
                z = self.put(self.TN); self.out(3, z); cs = 'H'
            elif cs == 'O_FIN':
                z = self.put(self.TN); self.out(3, z); cs = 'H'
            elif cs == 'D_FIN':
                z = self.put(self.TN); self.out(3, z); cs = 'H'
            elif cs == 'H_FIN':
                if self._check_hex(self.s[:-1]):
                    z = self.put(self.TN); self.out(3, z); cs = 'H'
                else:
                    self.errors.append(f"Invalid Hex: {self.s}"); cs = 'H'

            # Float
            elif cs == 'P1':
                if self.digit(self.ch):
                    self.add(); self.gc(); cs = 'P2'
                else:
                    self.errors.append("Digit expected after ."); cs = 'H'
            elif cs == 'P2':
                while self.digit(self.ch): self.add(); self.gc()
                if self.ch.lower() == 'e' and (self.peek() in '+-' or self.digit(self.peek())):
                    self.add();
                    self.gc();
                    cs = 'E1'
                else:
                    z = self.put(self.TN); self.out(3, z); cs = 'H'
            elif cs == 'E1':
                if self.digit(self.ch) or self.ch in '+-':
                    self.add(); self.gc(); cs = 'E2'
                else:
                    self.errors.append("Exp error"); cs = 'H'
            elif cs == 'E2':
                while self.digit(self.ch): self.add(); self.gc()
                z = self.put(self.TN);
                self.out(3, z);
                cs = 'H'

            # Остальные состояния
            elif cs == 'C1':
                if self.ch == '*':
                    self.gc(); cs = 'C2'
                else:
                    self.s = '/'; self.out(2, 16); cs = 'H'
            elif cs == 'C2':
                while self.ch and self.ch != '*': self.gc()
                if not self.ch:
                    cs = 'E'
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
                    self.errors.append("Exp ||"); cs = 'H'
            elif cs == 'SA':
                if self.ch == '&':
                    self.s = '&&'; self.out(2, 17); self.gc(); cs = 'H'
                else:
                    self.errors.append("Exp &&"); cs = 'H'
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
                if self.s in self.TL:
                    self.out(2, self.TL[self.s]); self.gc(); cs = 'H'
                else:
                    self.errors.append(f"Unknown: {self.s}"); self.gc(); cs = 'H'

        return self.tokens, self.errors

    def _is_hex_ctx(self):
        # Если следующий символ - цифра, буква или h, то текущая b/o/d - это часть hex числа
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
    def __init__(self, tokens, tw, tl, ti, tn):
        self.tokens = tokens
        self.TW = tw;
        self.TL = tl;
        self.TI = ti;
        self.TN = tn
        self.pos = 0;
        self.log_messages = []

    def log(self, msg):
        self.log_messages.append(msg)

    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def match(self, cls, code=None, val=None):
        t = self.current()
        if not t: raise SyntaxError("Unexpected EOF")
        if t['class'] != cls: raise SyntaxError(f"Exp class {cls}, got {t['class']} ({t['value']})")
        if code is not None and t['code'] != code: raise SyntaxError(f"Exp code {code}, got {t['code']}")
        if val is not None and t['value'] != val: raise SyntaxError(f"Exp val '{val}', got '{t['value']}'")
        self.pos += 1
        return t

    def parse_program(self):
        self.log("Start Program: Expect '{'")
        self.match(2, self.TL['{'])
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
                self.match(2, self.TL[';'])
            elif nt and nt['class'] == 2 and nt['code'] == self.TL['}']:
                pass
            else:
                raise SyntaxError("Expected ';' after statement")
        self.match(2, self.TL['}'])
        self.log("End Program: '}' found")

    def parse_declaration(self):
        self.log("  Declaration")
        self.match(1);
        self.match(4)
        while True:
            if self.current() and self.current()['code'] == self.TL[',']:
                self.match(2); self.match(4)
            else:
                break

    def parse_statement(self):
        t = self.current()
        if not t: return
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
                raise SyntaxError(f"Unknown op: {t['value']}")
        else:
            raise SyntaxError(f"Expected statement, got {t['value']}")

    def parse_assignment(self):
        self.log("  Assignment")
        self.match(4);
        self.match(2, self.TL[':'], ':=');
        self.parse_expression()

    def parse_if(self):
        self.log("  If")
        self.match(1, self.TW['if']);
        self.match(2, self.TL['(']);
        self.parse_expression();
        self.match(2, self.TL[')'])
        self.parse_statement()
        if self.current() and self.current()['code'] == self.TW.get('else'):
            self.match(1);
            self.parse_statement()

    def parse_for(self):
        self.log("  For")
        self.match(1, self.TW['for']);
        self.parse_assignment();
        self.match(1, self.TW['to']);
        self.parse_expression()
        if self.current() and self.current()['code'] == self.TW.get('step'):
            self.match(1);
            self.parse_expression()
        self.parse_statement();
        self.match(1, self.TW.get('next'))

    def parse_while(self):
        self.log("  While")
        self.match(1, self.TW['while']);
        self.match(2, self.TL['(']);
        self.parse_expression();
        self.match(2, self.TL[')'])
        self.parse_statement()

    def parse_compound(self):
        self.log("  Compound")
        self.match(1, self.TW['begin']);
        self.parse_statement()
        while True:
            if self.current() and self.current()['code'] == self.TL[';']:
                # Check lookahead for end
                if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1]['code'] == self.TW.get('end'): break
                self.match(2);
                self.parse_statement()
            else:
                break
        self.match(1, self.TW['end'])

    def parse_io(self, is_r):
        self.log(f"  IO ({'Read' if is_r else 'Write'})")
        self.match(1, self.TW['readln'] if is_r else self.TW['writeln'])
        if is_r:
            self.match(4)
            while self.current() and self.current()['code'] == self.TL[',']: self.match(2); self.match(4)
        else:
            self.parse_expression()
            while self.current() and self.current()['code'] == self.TL[',']: self.match(2); self.parse_expression()

    def parse_expression(self):
        self.parse_simple();
        t = self.current()
        if t and t['class'] == 2 and t['code'] in [self.TL['!='], self.TL['=='], self.TL['<'], self.TL['<='],
                                                   self.TL['>'], self.TL['>=']]:
            self.match(2);
            self.parse_simple()

    def parse_simple(self):
        self.parse_term();
        t = self.current()
        while t and t['class'] == 2 and t['code'] in [self.TL['+'], self.TL['-'], self.TL['||']]:
            self.match(2);
            self.parse_term();
            t = self.current()

    def parse_term(self):
        self.parse_fact();
        t = self.current()
        while t and t['class'] == 2 and t['code'] in [self.TL['*'], self.TL['/'], self.TL['&&']]:
            self.match(2);
            self.parse_fact();
            t = self.current()

    def parse_fact(self):
        t = self.current()
        if not t: raise SyntaxError("Exp operand")
        if t['class'] == 4:
            self.match(4)
        elif t['class'] == 3:
            self.match(3)
        elif t['code'] == self.TL['(']:
            self.match(2); self.parse_expression(); self.match(2)
        elif t['code'] == self.TL['!']:
            self.match(2); self.parse_fact()
        elif t['code'] in [self.TW.get('true'), self.TW.get('false')]:
            self.match(1)
        else:
            raise SyntaxError(f"Bad operand: {t['value']}")


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

        sample = """{
    int i;
    writeln 0AFh;     /* Hex -> 175 */
    writeln 0101b;    /* Bin -> 5 */
    writeln 123.45;   /* Float */
    writeln 123e;     /* Hex -> 4670 (0x123E) */

    for i := 1 to 5 step 1 begin
        if (i < 3) writeln 1 else writeln 0
    end next
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
        """Логика преобразования строки в число (из старого кода)"""
        val = "Nan/Err"
        s = lexeme
        try:
            # 1. Суффиксы
            if s.lower().endswith('h'):
                val = int(s[:-1], 16)
            elif s.lower().endswith('b'):
                val = int(s[:-1], 2)
            elif s.lower().endswith('o'):
                val = int(s[:-1], 8)
            elif s.lower().endswith('d'):
                val = int(s[:-1])
            # 2. Float или Hex с 'e'
            elif '.' in s or 'e' in s.lower():
                is_hex = False
                # Если есть e, но нет точки и после e нет цифр/знаков -> Hex (123e)
                if 'e' in s.lower() and '.' not in s:
                    idx = s.lower().find('e')
                    suffix = s[idx + 1:]
                    if not suffix or (suffix[0] not in '+-' and not suffix[0].isdigit()):
                        is_hex = True

                if is_hex:
                    val = int(s, 16)
                else:
                    val = float(s)
            # 3. Остальное
            else:
                if any(c.lower() in 'abcdef' for c in s):
                    val = int(s, 16)
                else:
                    val = int(s)
        except:
            # Fallback
            try:
                val = int(s, 16)
            except:
                pass
        return val

    def run_process(self):
        code = self.input_text.get("1.0", END).strip()
        self.clear_outputs()
        if not code: return

        # 1. SCAN
        tokens, errs = self.scanner.scan(code)

        for t in tokens:
            self.out_tokens.insert(INSERT, f"{t['class']}|{t['code']:<2}| {t['value']}\n")

        # Fill static tables
        self._fill_kv(self.txt_tw, self.scanner.TW)
        self._fill_kv(self.txt_tl, self.scanner.TL)
        self._fill_kv(self.txt_ti, self.scanner.TI)

        # Fill Numbers table with CALCULATION
        self.txt_tn.delete("1.0", END)
        self.txt_tn.insert(INSERT, f"{'Лексема':<15}|{'Код':<3}| Значение\n" + ("-" * 35) + "\n")

        # Сортируем по коду
        items = sorted(self.scanner.TN.items(), key=lambda x: x[1])
        for lex, code_id in items:
            dec_val = self._get_decimal_value(lex)
            self.txt_tn.insert(INSERT, f"{lex:<15}|{code_id:<3}| {dec_val}\n")

        if errs:
            self.out_errors.insert(INSERT, "❌ ЛЕКСИЧЕСКИЕ ОШИБКИ:\n")
            for e in errs:
                self.out_errors.insert(INSERT, f" -> {e}\n")
            self.tabview.set("Ошибки")
            return

        # 2. PARSE
        self.out_parse.insert(INSERT, "Start Parsing...\n")
        parser = Parser(tokens, self.scanner.TW, self.scanner.TL, self.scanner.TI, self.scanner.TN)
        try:
            parser.parse_program()
            for m in parser.log_messages: self.out_parse.insert(INSERT, f" -> {m}\n")
            self.out_parse.insert(INSERT, "\n✅ Success!")
            self.tabview.set("Синтаксис")
        except SyntaxError as e:
            # Форматированный вывод ошибки синтаксиса
            self.out_errors.insert(INSERT, f"❌ СИНТАКСИЧЕСКАЯ ОШИБКА:\n")
            self.out_errors.insert(INSERT, f"{str(e)}\n\n")
            self.out_errors.insert(INSERT, "📜 Последние действия парсера:\n")
            # Показываем 7 последних шагов для контекста
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