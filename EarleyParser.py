# rule format is (LHS[RHS])
# state is (rule, dot, pos, [parse tree so far])
import nltk


class EarleyParser(object):

    grammar = None
    transform_root = "TRANSFORM_ROOT"
    chart = None
    start_rule = (('S', ['START', 'eos']), 0, 0, '', 'predict', False)

    def load_rule_from_path(self, path):
        f = open(path, 'rb')
        lines = f.readlines()
        f.close()
        print "load grammars from " + path
        self.grammar = {}
        for l in lines:
            tokens = l.strip().split("->")
            lhs = tokens[0].strip()
            rhs = tokens[1].strip()
            rhs_rules = rhs.split("|")

            rules = []
            for r in rhs_rules:
                rules.append(r.strip().split(" "))
            self.grammar[lhs] = rules

        self.grammar = None

    def completer(self, s, idx):
        pos = s[2]
        c = self.chart[pos]
        lhs = s[0][0]
        input_flag = s[5]
        parse = s[3]

        for ss in c:
            dot = ss[1]
            if self.incomplete(ss):
                dot_symbol = ss[0][1][dot]
                if dot_symbol == lhs:
                    if self.is_recursive(lhs):
                        parse_symbol = parse.strip()
                    else:
                        parse_symbol = '(' + lhs + ' ' + parse.strip() + ')'

                    new_s = (ss[0], ss[1]+1, ss[2], ss[3] + parse_symbol, 'complete', input_flag)
                    self.add_to_chart(new_s, idx)

                    if input_flag and not self.cannot_transform(new_s[0][0]):
                        ss_rhs_copy = list(new_s[0][1])
                        ss_rhs_copy.insert(new_s[1], self.transform_root)
                        insert_s = ((new_s[0][0], ss_rhs_copy), new_s[1], new_s[2], new_s[3], 'transform-complete', False)
                        self.add_to_chart(insert_s, idx)

    def scanner(self, s, idx, tokens):
        dot = s[1]
        dot_symbol = s[0][1][dot]
        input_flag = self.expect_input(dot_symbol)

        if dot_symbol != "eos":
            parse_symbol = dot_symbol + ' '
        else:
            parse_symbol = ""

        if (idx < len(tokens) and dot_symbol == tokens[idx]) or dot_symbol == "epsilon":
            if dot_symbol == "epsilon":
                chart_idx = idx
            else:
                chart_idx = idx + 1

            new_s = (s[0], s[1] + 1, s[2], s[3] + parse_symbol, 'scanner', input_flag)
            self.add_to_chart(new_s, chart_idx)

            if input_flag:
                rhs_copy = list(new_s[0][1])
                rhs_copy.insert(new_s[1], self.transform_root)
                insert_s = ((new_s[0][0], rhs_copy), new_s[1], new_s[2], new_s[3], 'transform-scanner', False)
                self.add_to_chart(insert_s, chart_idx)

    def predictor(self, s, idx):
        dot = s[1]
        dot_symbol = s[0][1][dot]
        s_rules = self.grammar[dot_symbol]
        for sr in s_rules:
            new_s = ((dot_symbol, sr), 0, idx, '', 'predict', False)
            self.add_to_chart(new_s, idx)

    def add_to_chart(self, new_s, idx):
        if new_s not in self.chart[idx]:
            self.chart[idx].append(new_s)

    def get_parses(self, in_string=True):
        parse_trees = None
        if self.chart is not None and len(self.chart[-1]) > 0:
            if in_string:
                parse_trees = [t[3] for t in self.chart[-1] if t[0][0] == 'S']
            else:
                parse_trees = [nltk.Tree.fromstring(t[3]) for t in self.chart[-1] if t[0][0] == 'S']
        return parse_trees

    def print_chart(self, with_parse=True):
        for idx, c in enumerate(self.chart):
            print idx
            for cc in c:
                if not with_parse:
                    print (cc[0], cc[1], cc[2], cc[4], cc[5])
                else:
                    print cc

    @staticmethod
    def expect_input(token):
        extra_set = ['ask_repeat', 'ask_rephrase']
        return 'request' in token or 'explicit_confirm' in token or token in extra_set

    @staticmethod
    def is_recursive(token):
        return '*' in token

    @staticmethod
    def cannot_transform(token):
        return token in ["RECOMMEND_CHOICE", "S", "DEPENDENCY_CHOICE-weather", "DEPENDENCY_CHOICE-datetime_date"] \
               or "INFORM_ROOT-weather" in token

    @staticmethod
    def incomplete(s):
        return s[1] < len(s[0][1])

    @staticmethod
    def is_terminal(s):
        if EarleyParser.incomplete(s):
            return s[0][1][s[1]].islower()
        else:
            return True

    @staticmethod
    def normalize_input(x):
        norm_x = [t for t in x if t != 'epsilon']
        norm_x.append("eos")
        return norm_x

    def parse(self, x):
        norm_x = self.normalize_input(x)
        self.chart = [[] for i in range(len(norm_x)+1)]
        # (lhs, rhs), dot, pos, parse, type, expectInput
        self.chart[0] = [self.start_rule]

        for i in range(len(self.chart)):
            s_idx = 0
            while s_idx < len(self.chart[i]):
                s = self.chart[i][s_idx]
                if self.incomplete(s) and not self.is_terminal(s):
                    self.predictor(s, i)
                elif self.incomplete(s) and self.is_terminal(s):
                    self.scanner(s, i, norm_x)
                else:
                    self.completer(s, i)
                s_idx += 1
        return self.chart

