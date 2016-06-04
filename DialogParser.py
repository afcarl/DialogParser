# rule format is (LHS[RHS])
# state is (rule, dot, pos, [parse tree so far])
import nltk


class DialogParser(object):

    grammar = None
    transform_root = "TRANSFORM_ROOT"
    chart = None
    null_set = None
    start_rule = (('S', ['START', 'eos']), 0, 0, '', 'predict')

    def load_grammar_from_path(self, path):
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
            norm_rules = []
            for r in rhs_rules:
                tokens = r.strip().split(" ")
                norm_tokens = list(tokens)
                for idx, t in enumerate(tokens):
                    if DialogParser.is_terminal(t) and DialogParser.expect_input(t):
                        norm_tokens.insert(idx+1, self.transform_root)
                norm_rules.append(norm_tokens)
                rules.append(tokens)
            # save rules
            self.grammar[lhs] = norm_rules
        print "load " + str(len(self.grammar)) + " rules"
        # find all null non terminal symbols
        self.find_all_nullable()

    def completer(self, s, idx):
        pos = s[2]
        c = self.chart[pos]
        lhs = s[0][0]
        parse = s[3]
        modified = False

        for ss in c:
            ss_lhs = ss[0][0]
            dot = ss[1]
            if self.incomplete(ss):
                dot_symbol = ss[0][1][dot]
                if dot_symbol == lhs:
                    if DialogParser.is_recursive(lhs) and lhs == ss_lhs:
                        parse_symbol = parse.strip()
                    else:
                        parse_symbol = '(' + lhs + ' ' + parse.strip() + ')'

                    new_s = (ss[0], ss[1]+1, ss[2], ss[3] + parse_symbol, 'complete')
                    modified = self.add_to_chart(new_s, idx)

        return modified

    def scanner(self, s, idx, tokens):
        dot = s[1]
        dot_symbol = s[0][1][dot]

        if dot_symbol != "eos":
            parse_symbol = dot_symbol + ' '
        else:
            parse_symbol = ""

        modified = False
        if (idx < len(tokens) and dot_symbol == tokens[idx]) or DialogParser.is_dummy(dot_symbol):
            if DialogParser.is_dummy(dot_symbol):
                chart_idx = idx
            else:
                chart_idx = idx + 1

            new_s = (s[0], s[1] + 1, s[2], s[3] + parse_symbol, 'scanner')
            modified = self.add_to_chart(new_s, chart_idx)

        return modified

    def predictor(self, s, idx):
        dot = s[1]
        dot_symbol = s[0][1][dot]
        s_rules = self.grammar[dot_symbol]
        modified = False
        for sr in s_rules:
            new_s = ((dot_symbol, sr), 0, idx, '', 'predict')
            added = self.add_to_chart(new_s, idx)
            if not modified and added:
                modified = True
        return modified

    """
    Helper
    """
    def add_to_chart(self, new_s, idx):
        if new_s not in self.chart[idx]:
            self.chart[idx].append(new_s)
            return True
        else:
            return False

    def get_parses(self, in_string=True):
        parse_trees = None
        if self.chart is not None and len(self.chart[-1]) > 0:
            if in_string:
                parse_trees = [t[3] for t in self.chart[-1] if t[0][0] == 'S']
            else:
                parse_trees = [nltk.Tree.fromstring(t[3]) for t in self.chart[-1] if t[0][0] == 'S']
        return parse_trees

    def find_all_nullable(self):
        if self.grammar is None:
            print "Error: call find null set before read grammmar"
            return
        self.null_set = {}
        prev_size = -1
        while prev_size != len(self.null_set):
            prev_size = len(self.null_set)

            for lhs, rules in self.grammar.iteritems():
                null_parse = self.null_set.get(lhs, [])
                for rhs in rules:
                    all_null = True
                    parse = [""]
                    for token in rhs:
                        if DialogParser.is_terminal(token):
                            if not DialogParser.is_dummy(token):
                                all_null = False
                                break
                            else:
                                for idx in range(len(parse)):
                                    parse[idx] += token + " "

                        else:
                            if token not in self.null_set.keys():
                                all_null = False
                                break
                            else:
                                all_ways = self.null_set.get(token, [])
                                parse = parse * len(all_ways)
                                for idx, way in enumerate(all_ways):
                                    parse[idx] += "(" + token + " " + way + ")"
                    if all_null:
                        null_parse.extend(set(parse))

                if len(null_parse) > 0:
                    self.null_set[lhs] = list(set(null_parse))

        print "Null set size is " + str(len(self.null_set))

    """
    Print methods
    """
    def print_chart(self, with_parse=True):
        for idx, c in enumerate(self.chart):
            print idx
            for cc in c:
                if not with_parse:
                    print (cc[0], cc[1], cc[2], cc[4])
                else:
                    print cc

    def print_grammar(self):
        g = self.grammar
        for lhs, rules in g.iteritems():
            print lhs + " -> "
            for r in rules:
                print r
            print "-------------"

    def print_null_set(self):
        for lhs, rules in self.null_set.iteritems():
            print lhs + " -> "
            for r in rules:
                print r
            print "-------------"

    @staticmethod
    def is_dummy(token):
        return token == "epsilon" or token == "pop"

    @staticmethod
    def expect_input(token):
        extra_set = ['ask_repeat', 'ask_rephrase']
        return 'request' in token or 'explicit_confirm' in token or token in extra_set

    @staticmethod
    def is_recursive(token):
        return '*' in token

    @staticmethod
    def incomplete(s):
        return len(s[0][1]) > 0 and s[1] < len(s[0][1])

    @staticmethod
    def is_terminal(token):
        return token.islower()

    @staticmethod
    def dot_terminal(s):
        if DialogParser.incomplete(s):
            return DialogParser.is_terminal(s[0][1][s[1]])
        else:
            return True

    @staticmethod
    def normalize_input(x):
        norm_x = [t for t in x if not DialogParser.is_dummy(t)]
        norm_x.append("eos")
        return norm_x

    def parse(self, x):
        norm_x = self.normalize_input(x)
        self.chart = [[] for i in range(len(norm_x)+1)]
        # (lhs, rhs), dot, pos, parse, operator_type
        self.chart[0] = [self.start_rule]

        for i in range(len(self.chart)):
            stable = False
            while not stable:
                ever_updated = False
                s_idx = 0
                while s_idx < len(self.chart[i]):
                    s = self.chart[i][s_idx]
                    if self.incomplete(s) and not self.dot_terminal(s):
                        updated = self.predictor(s, i)
                    elif self.incomplete(s) and self.dot_terminal(s):
                        updated = self.scanner(s, i, norm_x)
                    else:
                        updated = self.completer(s, i)
                    s_idx += 1
                    if not ever_updated and updated:
                        ever_updated = True
                stable = not ever_updated

        return self.chart

