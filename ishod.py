import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import io


# --- ЛЕКСИЧЕСКИЙ АНАЛИЗАТОР (SCANNER) ---
class Scanner:
    def __init__(self):
        self.TW = {
            'integer': 1, 'real': 2, 'boolean': 3, 'true': 4, 'false': 5,
            'begin': 6, 'end': 7, 'if': 8, 'else': 9, 'for': 10, 'to': 11,
            'step': 12, 'next': 13, 'while': 14, 'readln': 15, 'writeln': 16
        }
        self.TL = {
            '{': 1, '}': 2, '!': 3, ',': 4, ';': 5, '==': 6, ':=': 7,
            '&&': 8, '(': 9, ')': 10, '+': 11, '-': 12, '*': 13, '/': 14,
            '||': 15, '!=': 16, '>': 17, '<': 18, '<=': 19, '>=': 20
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

            elif cs == 'N2':
                if self.ch.lower() == 'b':
                    if (self.ptr + 1 < len(self.source_code) and self.source_code[self.ptr + 1].lower() == 'h'):
                        self.gc()
                        cs = 'HX'
                    elif (self.ptr + 1 < len(self.source_code) and self.source_code[self.ptr + 1] not in ['1', '2', '3',
                                                                                                          '4', '5', '6',
                                                                                                          '7', '8',
                                                                                                          '9'] and
                          self.source_code[self.ptr + 1].lower() not in ['a', 'b', 'c', 'd', 'e', 'f']):
                        self.gc()
                        cs = 'B'
                    else:
                        self.add(); self.gc(); cs = 'N16'
                elif self.ch.lower() == 'o':
                    self.gc(); cs = 'O'
                elif self.ch.lower() == 'd':
                    if (self.ptr + 1 < len(self.source_code) and self.source_code[self.ptr + 1].lower() == 'h'):
                        self.gc(); cs = 'HX'
                    elif (self.ptr + 1 < len(self.source_code) and self.source_code[self.ptr + 1] not in ['1', '2', '3',
                                                                                                          '4', '5', '6',
                                                                                                          '7', '8',
                                                                                                          '9'] and
                          self.source_code[self.ptr + 1].lower() not in ['a', 'b', 'c', 'd', 'e', 'f']):
                        self.gc(); cs = 'D'
                    else:
                        self.add(); self.gc(); cs = 'N16'
                elif self.ch.lower() == 'h':
                    self.gc(); cs = 'HX'
                elif self.ch in '01':
                    self.add(); self.gc()
                elif '2' <= self.ch <= '7':
                    self.add(); self.gc(); cs = 'N8'
                elif self.ch in '89':
                    self.add(); self.gc(); cs = 'N10'
                elif self.is_hex_letter(self.ch) and self.source_code[self.ptr + 1].lower() not in ['+', '-']:
                    self.add(); self.gc(); cs = 'N16'
                elif self.ch == '.':
                    self.add(); self.gc(); cs = 'P2'
                elif self.ch.lower() == 'e':
                    self.add(); self.gc(); cs = 'E11'
                else:
                    cs = self.finalize_as_decimal()

            elif cs == 'N8':
                if self.ch.lower() == 'o':
                    self.gc(); cs = 'O'
                elif self.ch.lower() == 'd':
                    if (self.ptr + 1 < len(self.source_code) and self.source_code[self.ptr + 1].lower() == 'h'):
                        self.gc(); cs = 'HX'
                    elif (self.ptr + 1 < len(self.source_code) and self.source_code[self.ptr + 1] not in ['1', '2', '3',
                                                                                                          '4', '5', '6',
                                                                                                          '7', '8',
                                                                                                          '9'] and
                          self.source_code[self.ptr + 1].lower() not in ['a', 'b', 'c', 'd', 'e', 'f']):
                        self.gc(); cs = 'D'
                    else:
                        self.add(); self.gc(); cs = 'N16'
                elif self.ch.lower() == 'h':
                    self.gc(); cs = 'HX'
                elif '0' <= self.ch <= '7':
                    self.add(); self.gc()
                elif self.ch in '89':
                    self.add(); self.gc(); cs = 'N10'
                elif self.is_hex_letter(self.ch) and self.source_code[self.ptr + 1].lower() not in ['+', '-']:
                    self.add(); self.gc(); cs = 'N16'
                elif self.ch == '.':
                    self.add(); self.gc(); cs = 'P2'
                elif self.ch.lower() == 'e':
                    self.add(); self.gc(); cs = 'E11'
                else:
                    cs = self.finalize_as_decimal()

            elif cs == 'N10':
                if self.ch.lower() == 'o':
                    print(f"Ошибка: недопустимая цифра."); cs = 'ER'
                elif self.ch.lower() == 'd':
                    if (self.ptr + 1 < len(self.source_code) and self.source_code[self.ptr + 1].lower() == 'h'):
                        self.gc(); cs = 'HX'
                    elif (self.ptr + 1 < len(self.source_code) and self.source_code[self.ptr + 1] not in ['1', '2', '3',
                                                                                                          '4', '5', '6',
                                                                                                          '7', '8',
                                                                                                          '9'] and
                          self.source_code[self.ptr + 1].lower() not in ['a', 'b', 'c', 'd', 'e', 'f']):
                        self.gc(); cs = 'D'
                    else:
                        self.add(); self.gc(); cs = 'N16'
                elif self.ch.lower() == 'h':
                    self.gc(); cs = 'HX'
                elif self.digit(self.ch):
                    self.add(); self.gc()
                elif self.is_hex_letter(self.ch) and self.source_code[self.ptr + 1].lower() not in ['+', '-']:
                    self.add(); self.gc(); cs = 'N16'
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
                    self.s = '/'; self.out(2, 14); cs = 'H'
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
                    self.s = '!='; self.out(2, 16); self.gc()
                else:
                    self.s = '!'; self.out(2, 3)
                cs = 'H'
            elif cs == 'SEQ':
                if self.ch == '=':
                    self.s = '=='; self.out(2, 6); self.gc(); cs = 'H'
                else:
                    print(f"Ошибка: после '=' ожидался второй '='"); cs = 'ER'
            elif cs == 'SC':
                if self.ch == '=':
                    self.s = ':='; self.out(2, 7); self.gc(); cs = 'H'
                else:
                    print(f"Ошибка: после ':' ожидался '='"); cs = 'ER'
            elif cs == 'SP':
                if self.ch == '|':
                    self.s = '||'; self.out(2, 15); self.gc(); cs = 'H'
                else:
                    print(f"Ошибка: после '|' ожидался второй '|'"); cs = 'ER'
            elif cs == 'SA':
                if self.ch == '&':
                    self.s = '&&'; self.out(2, 8); self.gc(); cs = 'H'
                else:
                    print(f"Ошибка: после '&' ожидался второй '&'"); cs = 'ER'
            elif cs == 'M1':
                if self.ch == '=':
                    self.s = '<='; self.out(2, 19); self.gc()
                else:
                    self.s = '<'; self.out(2, 18)
                cs = 'H'
            elif cs == 'M2':
                if self.ch == '=':
                    self.s = '>='; self.out(2, 20); self.gc()
                else:
                    self.s = '>'; self.out(2, 17)
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
    def __init__(self, tokens):
        if not tokens:
            print("Ошибка: Нет токенов.")
            raise SystemExit
        self.tokens = tokens
        self.token_idx = -1
        self.current_token = None
        self.rpn_prog = []
        self.sem_ids = {}
        self.sem_stack = []
        self.sem_ops_table = {
            ('+', 'integer', 'integer'): 'integer', ('-', 'integer', 'integer'): 'integer',
            ('*', 'integer', 'integer'): 'integer', ('/', 'integer', 'integer'): 'real',
            ('+', 'real', 'real'): 'real', ('-', 'real', 'real'): 'real',
            ('*', 'real', 'real'): 'real', ('/', 'real', 'real'): 'real',
            ('+', 'integer', 'real'): 'real', ('+', 'real', 'integer'): 'real',
            ('-', 'integer', 'real'): 'real', ('-', 'real', 'integer'): 'real',
            ('*', 'integer', 'real'): 'real', ('*', 'real', 'integer'): 'real',
            ('/', 'integer', 'real'): 'real', ('/', 'real', 'integer'): 'real',
            ('>', 'integer', 'integer'): 'boolean', ('<', 'integer', 'integer'): 'boolean',
            ('>=', 'integer', 'integer'): 'boolean', ('<=', 'integer', 'integer'): 'boolean',
            ('==', 'integer', 'integer'): 'boolean', ('!=', 'integer', 'integer'): 'boolean',
            ('&&', 'boolean', 'boolean'): 'boolean', ('||', 'boolean', 'boolean'): 'boolean',
        }
        self.next_token()

    def gen(self, item):
        self.rpn_prog.append(item)

    def get_current_rpn_idx(self):
        return len(self.rpn_prog)

    def reserve_rpn_idx(self):
        idx = len(self.rpn_prog)
        self.rpn_prog.append(0)
        return idx

    def fix_rpn_label(self, idx, target):
        self.rpn_prog[idx] = target

    def sem_error(self, message):
        print(f"\n!!! СЕМАНТИЧЕСКАЯ ОШИБКА !!! : {message}")
        print(f"    Рядом с токеном: {self.current_token['value']}")
        raise SystemExit

    def sem_declare(self, id_code, id_name, id_type):
        if id_code in self.sem_ids and self.sem_ids[id_code]['declared']:
            self.sem_error(f"Идентификатор '{id_name}' уже описан.")
        self.sem_ids[id_code] = {'type': id_type, 'declared': 1, 'name': id_name}
        print(f"  [Семантика] Объявлена: {id_name} ({id_type})")

    def sem_check_declared(self, id_code, id_name):
        if id_code not in self.sem_ids or self.sem_ids[id_code]['declared'] == 0:
            self.sem_error(f"Переменная '{id_name}' не описана.")
        return self.sem_ids[id_code]['type']

    def sem_push(self, type_val):
        self.sem_stack.append(type_val)

    def sem_check_unary(self, op):
        t = self.sem_stack.pop()
        res = None
        if op == '!' and t == 'boolean': res = 'boolean'
        if res is None: self.sem_error(f"Несоответствие типов '{op}': {t}")
        self.sem_stack.append(res)

    def sem_check_binary(self, op):
        t2 = self.sem_stack.pop()
        t1 = self.sem_stack.pop()
        res = self.sem_ops_table.get((op, t1, t2))
        if res is None: self.sem_error(f"Недопустимая операция '{op}' для '{t1}' и '{t2}'")
        self.sem_stack.append(res)

    def sem_check_assignment(self, id_code, id_name):
        rhs = self.sem_stack.pop()
        lhs = self.sem_check_declared(id_code, id_name)
        if lhs != rhs and not (lhs == 'real' and rhs == 'integer'):
            self.sem_error(f"Нельзя присвоить '{rhs}' переменной '{lhs}' ({id_name})")
        print(f"  [Семантика] Присваивание OK: {id_name} ({lhs}) := {rhs}")

    def sem_check_bool_condition(self, context):
        if self.sem_stack.pop() != 'boolean': self.sem_error(f"В условии '{context}' ожидается boolean")

    def next_token(self):
        self.token_idx += 1
        self.current_token = self.tokens[self.token_idx] if self.token_idx < len(self.tokens) else {"class": 0,
                                                                                                    "value": "EOF"}

    def error(self, message):
        print(f"\nСинтаксическая ошибка: {message}")
        if self.current_token: print(f"  -> Рядом с токеном: '{self.current_token.get('value', 'N/A')}'")
        raise SystemExit

    def expect(self, token_value=None, token_class=None):
        if token_value is not None:
            if self.current_token and self.current_token['value'] == token_value:
                self.next_token()
            else:
                self.error(f"Ожидался '{token_value}', получен '{self.current_token['value']}'")
        elif token_class is not None:
            if self.current_token and self.current_token['class'] == token_class:
                self.next_token()
            else:
                self.error(f"Ожидался класс {token_class}, получен '{self.current_token['value']}'")

    def program(self):
        self.expect('{')
        while self.current_token and self.current_token['value'] != '}':
            if self.current_token['value'] in ['integer', 'real', 'boolean']:
                self.description()
            else:
                self.statement()
            if self.current_token['value'] == ';':
                self.next_token()
            elif self.current_token['value'] == '}':
                break
            else:
                self.error("Ожидался ';'")
        if self.tokens[self.token_idx - 1]['value'] != ';': self.error("Ожидался ';'")
        self.expect('}')

    def description(self):
        cur_type = self.current_token['value']
        self.next_token()
        id_code = self.current_token['code']
        id_name = self.current_token['value']
        self.expect(token_class=4)
        self.sem_declare(id_code, id_name, cur_type)
        while self.current_token['value'] == ',':
            self.next_token()
            id_code = self.current_token['code']
            id_name = self.current_token['value']
            self.expect(token_class=4)
            self.sem_declare(id_code, id_name, cur_type)

    def statement(self):
        val = self.current_token['value']
        if val == 'begin':
            self.compound_statement()
        elif self.current_token['class'] == 4:
            self.assignment_statement()
        elif val == 'if':
            self.if_statement()
        elif val == 'for':
            self.for_loop()
        elif val == 'while':
            self.while_loop()
        elif val == 'readln':
            self.read_statement()
        elif val == 'writeln':
            self.write_statement()
        else:
            self.error(f"Неизвестный оператор '{val}'")

    def compound_statement(self):
        self.expect('begin')
        self.statement()
        while self.current_token['value'] == ';': self.next_token(); self.statement()
        self.expect('end')

    def assignment_statement(self):
        id_code = self.current_token['code']
        id_name = self.current_token['value']
        self.gen(id_name)
        self.expect(token_class=4)
        self.expect(':=')
        self.expression()
        self.gen(':=')
        self.sem_check_assignment(id_code, id_name)
        return id_name

    def if_statement(self):
        self.expect('if')
        self.expect('(')
        self.expression()
        self.expect(')')
        self.sem_check_bool_condition("if")
        idx_false = self.reserve_rpn_idx()
        self.gen('!F')
        self.statement()
        if self.current_token['value'] == 'else':
            idx_after = self.reserve_rpn_idx()
            self.gen('!')
            self.fix_rpn_label(idx_false, self.get_current_rpn_idx())
            self.next_token()
            self.statement()
            self.fix_rpn_label(idx_after, self.get_current_rpn_idx())
        else:
            self.fix_rpn_label(idx_false, self.get_current_rpn_idx())

    def for_loop(self):
        self.expect('for')
        var_name = self.assignment_statement()
        start_label = self.get_current_rpn_idx()
        self.gen(var_name)
        self.expect('to')
        self.expression()
        self.gen('<=')
        if self.sem_stack.pop() != 'integer': self.sem_error("Граница for не integer")
        exit_idx = self.reserve_rpn_idx()
        self.gen('!F')

        step_val = "1"
        if self.current_token['value'] == 'step':
            self.next_token()
            if self.current_token['class'] in [3, 4]:
                step_val = self.current_token['value']
                self.expression()
                self.rpn_prog.pop()
            else:
                self.expression(); self.rpn_prog.pop()
            if self.sem_stack.pop() != 'integer': self.sem_error("Шаг for не integer")

        self.statement()
        self.gen(var_name)
        self.gen(var_name)
        self.gen(step_val)
        self.gen('+')
        self.gen(':=')
        self.gen(start_label)
        self.gen('!')
        self.fix_rpn_label(exit_idx, self.get_current_rpn_idx())
        self.expect('next')

    def while_loop(self):
        self.expect('while')
        start_label = self.get_current_rpn_idx()
        self.expect('(')
        self.expression()
        self.expect(')')
        self.sem_check_bool_condition("while")
        exit_idx = self.reserve_rpn_idx()
        self.gen('!F')
        self.statement()
        self.gen(start_label)
        self.gen('!')
        self.fix_rpn_label(exit_idx, self.get_current_rpn_idx())

    def read_statement(self):
        self.expect('readln')
        id_c = self.current_token['code']
        id_n = self.current_token['value']
        self.expect(token_class=4)
        self.sem_check_declared(id_c, id_n)
        self.gen(id_n)
        self.gen('READ')
        while self.current_token['value'] == ',':
            self.next_token()
            id_c = self.current_token['code']
            id_n = self.current_token['value']
            self.expect(token_class=4)
            self.sem_check_declared(id_c, id_n)
            self.gen(id_n)
            self.gen('READ')

    def write_statement(self):
        self.expect('writeln')
        self.expression()
        if self.sem_stack: self.sem_stack.pop()
        self.gen('WRITE')
        while self.current_token['value'] == ',':
            self.next_token()
            self.expression()
            if self.sem_stack: self.sem_stack.pop()
            self.gen('WRITE')

    def expression(self):
        self.operand()
        while self.current_token['value'] in ['!=', '==', '<', '<=', '>', '>=']:
            op = self.current_token['value']
            self.next_token()
            self.operand()
            self.sem_check_binary(op)
            self.gen(op)

    def operand(self):
        self.term()
        while self.current_token['value'] in ['+', '-', '||']:
            op = self.current_token['value']
            self.next_token()
            self.term()
            self.sem_check_binary(op)
            self.gen(op)

    def term(self):
        self.factor()
        while self.current_token['value'] in ['*', '/', '&&']:
            op = self.current_token['value']
            self.next_token()
            self.factor()
            self.sem_check_binary(op)
            self.gen(op)

    def factor(self):
        tok = self.current_token
        if tok['class'] == 4:
            t = self.sem_check_declared(tok['code'], tok['value'])
            self.sem_push(t)
            self.gen(tok['value'])
            self.next_token()
        elif tok['class'] == 3:
            val = tok['value'].lower()
            self.sem_push('real' if '.' in val or 'e' in val else 'integer')
            self.gen(tok['value'])
            self.next_token()
        elif tok['value'] in ['true', 'false']:
            self.sem_push('boolean')
            self.gen(tok['value'])
            self.next_token()
        elif tok['value'] == '!':
            op = '!'
            self.next_token()
            self.factor()
            self.sem_check_unary(op)
            self.gen('UN_!')
        elif tok['value'] == '(':
            self.next_token()
            self.expression()
            self.expect(')')
        else:
            self.error("Ожидался операнд")


# --- INTERPRETER ---
class Interpreter:
    def __init__(self, rpn_prog, input_func=None):
        self.prog = rpn_prog
        self.stack = []
        self.vars = {}
        self.pc = 0
        self.input_func = input_func if input_func else input

    def parse_val(self, val):
        if isinstance(val, (int, float, bool)): return val
        if isinstance(val, str):
            if val.lower().endswith('h'): return int(val[:-1], 16)
            if val.lower().endswith('b'): return int(val[:-1], 2)
            if val.lower().endswith('o'): return int(val[:-1], 8)
            if val.lower().endswith('d'): return int(val[:-1])
            if val.lower() == 'true': return True
            if val.lower() == 'false': return False
            try:
                return float(val) if '.' in val or 'e' in val.lower() else int(val)
            except:
                return val  # Возвращаем строку (имя переменной)
        return val

    def get_val(self, x):
        if isinstance(x, str) and x in self.vars: return self.vars[x]
        return self.parse_val(x)

    def execute(self):
        print(f"{'Step':<5} | {'Element':<10} | {'Operation':<20} | {'Stack':<30} | {'Vars'}")
        print("-" * 100)

        step_count = 0
        while self.pc < len(self.prog):
            elem = self.prog[self.pc]
            op_desc = "Push"

            if elem == 'UN_!':
                val = self.get_val(self.stack.pop())
                self.stack.append(not val)
                op_desc = f"NOT {val}"
                self.pc += 1
            elif elem in ['+', '-', '*', '/', '&&', '||', '==', '!=', '<', '>', '<=', '>=']:
                b = self.get_val(self.stack.pop())
                a = self.get_val(self.stack.pop())
                res = 0
                if elem == '+':
                    res = a + b
                elif elem == '-':
                    res = a - b
                elif elem == '*':
                    res = a * b
                elif elem == '/':
                    res = a / b
                elif elem == '&&':
                    res = a and b
                elif elem == '||':
                    res = a or b
                elif elem == '==':
                    res = (a == b)
                elif elem == '!=':
                    res = (a != b)
                elif elem == '<':
                    res = (a < b)
                elif elem == '>':
                    res = (a > b)
                elif elem == '<=':
                    res = (a <= b)
                elif elem == '>=':
                    res = (a >= b)
                self.stack.append(res)
                op_desc = f"{a} {elem} {b}"
                self.pc += 1
            elif elem == ':=':
                val = self.get_val(self.stack.pop())
                name = self.stack.pop()
                self.vars[name] = val
                op_desc = f"{name} := {val}"
                self.pc += 1
            elif elem == 'WRITE':
                val = self.get_val(self.stack.pop())
                print(f"      >>> OUTPUT: {val}")
                op_desc = f"Write {val}"
                self.pc += 1
            elif elem == 'READ':
                name = self.stack.pop()
                # Обработка ввода
                inp_str = self.input_func(f"Введите значение для '{name}':")
                if inp_str is None: inp_str = "0"

                # Пытаемся строго преобразовать ввод
                try:
                    if '.' in inp_str or 'e' in inp_str.lower():
                        val = float(inp_str)
                    elif inp_str.lower() == 'true':
                        val = True
                    elif inp_str.lower() == 'false':
                        val = False
                    else:
                        # Попытка преобразовать в int
                        if inp_str.lower().endswith('h') or inp_str.lower().endswith('b') or inp_str.lower().endswith(
                                'd'):
                            val = self.parse_val(inp_str)
                        else:
                            val = int(inp_str)
                except ValueError:
                    print(f"ОШИБКА ВРЕМЕНИ ВЫПОЛНЕНИЯ: Некорректный ввод '{inp_str}' для числа.")
                    break  # Прерываем выполнение

                self.vars[name] = val
                op_desc = f"Read {name}"
                self.pc += 1

            elif elem == '!':
                target = self.stack.pop()
                op_desc = f"Jump to {target}"
                self.pc = target
            elif elem == '!F':
                target = self.stack.pop()
                cond = self.get_val(self.stack.pop())
                if not cond:
                    op_desc = f"JumpFalse to {target}"; self.pc = target
                else:
                    op_desc = f"NoJump (True)"; self.pc += 1
            else:
                self.stack.append(elem)
                self.pc += 1

            stack_str = str(self.stack)
            if len(stack_str) > 30: stack_str = stack_str[-30:]
            vars_str = str(self.vars).replace('{', '').replace('}', '')
            print(f"{step_count:<5} | {str(elem):<10} | {op_desc:<20} | {stack_str:<30} | {vars_str}")
            step_count += 1


# --- GUI CLASS ---
class CompilerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Компилятор")
        self.root.geometry("1000x800")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook.Tab", font=('Helvetica', 10, 'bold'))

        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        ttk.Label(top_frame, text="Исходный код:", font=('Helvetica', 12, 'bold')).pack(anchor=tk.W)
        self.input_text = tk.Text(top_frame, height=15, font=('Consolas', 11))
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=5)

        default_code = """{
    integer n, f, i;
    n := 5;
    f := 1;
    for i := 1 to n step 1 
        f := f * i
    next;
    writeln f;
}"""
        self.input_text.insert("1.0", default_code)

        run_btn = ttk.Button(top_frame, text="▶ Запустить Анализ и Интерпретацию", command=self.run_analysis)
        run_btn.pack(fill=tk.X, pady=5)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_tokens = self.create_tab("Лексика (Токены)")
        self.tab_semantics = self.create_tab("Семантика")
        self.tab_rpn = self.create_tab("ПОЛИЗ")
        self.tab_trace = self.create_tab("Ход Интерпретации")
        self.tab_console = self.create_tab("Консоль / Ошибки")

    def create_tab(self, title):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=title)
        text_widget = tk.Text(frame, state='disabled', font=('Consolas', 10), wrap=tk.NONE)

        ys = ttk.Scrollbar(frame, orient='vertical', command=text_widget.yview)
        xs = ttk.Scrollbar(frame, orient='horizontal', command=text_widget.xview)
        text_widget['yscrollcommand'] = ys.set
        text_widget['xscrollcommand'] = xs.set

        ys.pack(side=tk.RIGHT, fill=tk.Y)
        xs.pack(side=tk.BOTTOM, fill=tk.X)
        text_widget.pack(fill=tk.BOTH, expand=True)
        return text_widget

    def write_to_tab(self, tab, content):
        tab.config(state='normal')
        tab.delete("1.0", tk.END)
        tab.insert("1.0", content)
        tab.config(state='disabled')

    def gui_input_callback(self, prompt):
        return simpledialog.askstring("Ввод данных", prompt, parent=self.root)

    def run_analysis(self):
        source_code = self.input_text.get("1.0", tk.END).strip()
        if not source_code:
            messagebox.showwarning("Внимание", "Введите исходный код!")
            return

        log_tokens = io.StringIO()
        log_semantics = io.StringIO()
        log_rpn = io.StringIO()
        log_trace = io.StringIO()
        log_console = io.StringIO()

        original_stdout = sys.stdout

        try:
            sys.stdout = log_tokens
            print("=== ЛЕКСИЧЕСКИЙ АНАЛИЗ ===")
            scanner = Scanner()
            tokens = scanner.scan(source_code)

            if not tokens: raise ValueError("Лексический анализ не вернул токенов.")

            sys.stdout = log_semantics
            print("=== СЕМАНТИЧЕСКИЙ АНАЛИЗ ===")
            parser = Parser(tokens)
            parser.program()
            print("\n--- Таблица Идентификаторов ---")
            for k, v in parser.sem_ids.items(): print(f"{k}: {v}")

            sys.stdout = log_rpn
            rpn_str = ""
            for idx, item in enumerate(parser.rpn_prog):
                rpn_str += f"{idx}:{item}  "
            print(rpn_str)

            sys.stdout = log_trace
            interpreter = Interpreter(parser.rpn_prog, input_func=self.gui_input_callback)
            interpreter.execute()

            log_console.write("Анализ и выполнение завершены успешно.\n")

        except SystemExit:
            log_console.write("\nПроцесс был остановлен из-за ошибки (см. вкладки).\n")
        except Exception as e:
            log_console.write(f"\nКритическая ошибка: {str(e)}\n")
            import traceback
            traceback.print_exc(file=log_console)
        finally:
            sys.stdout = original_stdout

        self.write_to_tab(self.tab_tokens, log_tokens.getvalue())
        self.write_to_tab(self.tab_semantics, log_semantics.getvalue())
        self.write_to_tab(self.tab_rpn, log_rpn.getvalue())
        self.write_to_tab(self.tab_trace, log_trace.getvalue())
        self.write_to_tab(self.tab_console, log_console.getvalue())

        if "Критическая ошибка" in log_console.getvalue() or "остановлен" in log_console.getvalue():
            self.notebook.select(self.tab_console.master)
        else:
            self.notebook.select(self.tab_trace.master)


if __name__ == "__main__":
    root = tk.Tk()
    app = CompilerApp(root)
    root.mainloop()
