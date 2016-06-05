# rule format is (LHS[RHS])
# state is (rule, dot, pos, [parse tree so far])
import nltk
from Utils import Utils


class DialogParser(object):

    grammar = None
    transform_root = "TRANSFORM_ROOT"
    chart = None
    null_set = None
    terminal_symbols = None
    da_set = None
    concept_set = None
    is_top_down = False
    start_rule = None

    RULE = 0
    DOT = 1
    POS = 2
    PARSE = 3
    OPERATOR = 5

    LHS = 0
    RHS = 1

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
    def is_terminal(token):
        return token.islower()

    @staticmethod
    def normalize_input(x, with_eos=True):
        norm_x = [t for t in x if not DialogParser.is_dummy(t)]
        if with_eos:
            norm_x.append("eos")
        return norm_x

    def incomplete(self, s):
        return len(s[self.RULE][self.RHS]) > 0 and s[self.DOT] < len(s[self.RULE][self.RHS])

    def dot_terminal(self, s):
        if self.incomplete(s):
            return DialogParser.is_terminal(s[self.RULE][self.RHS][s[self.DOT]])
        else:
            return True

    def load_grammar_from_path(self, path):
        f = open(path, 'rb')
        lines = f.readlines()
        f.close()
        print "load grammars from " + path
        self.grammar = {}
        self.terminal_symbols = set()
        for l in lines:
            tokens = l.strip().split("->")
            lhs = tokens[0].strip()
            rhs = tokens[1].strip()
            rhs_rules = rhs.split("|")

            norm_rules = []
            for r in rhs_rules:
                tokens = r.strip().split(" ")
                norm_tokens = list(tokens)
                for idx, t in enumerate(tokens):
                    if DialogParser.is_terminal(t) and DialogParser.expect_input(t):
                        norm_tokens.insert(idx+1, self.transform_root)
                    if DialogParser.is_terminal(t):
                        self.terminal_symbols.add(t)
                norm_rules.append(norm_tokens)
            # save rules
            self.grammar[lhs] = norm_rules
        print "load " + str(len(self.grammar)) + " rules"

        # calculate da set and concept lexicon
        da_temp = set()
        concept_temp = set()
        for t in self.terminal_symbols:
            tokens = t.split("-")
            if not DialogParser.is_dummy(tokens[0]):
                da_temp.add(tokens[0])
                if len(tokens) > 1:
                    concept_temp.add(tokens[1])

        self.da_set = sorted(list(da_temp))
        self.concept_set = sorted(list(concept_temp))

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
                parse_trees = [t[self.PARSE] for t in self.chart[-1] if t[self.RULE][self.LHS] == 'S']
            else:
                parse_trees = [nltk.Tree.fromstring(t[self.PARSE]) for t in self.chart[-1] if t[self.RULE][self.LHS] == 'S']
        return parse_trees

    def decode_terminal(self, code):
        tokens = code.split('-')
        if tokens[0].isdigit():
            da_idx = int(tokens[0])
        else:
            return None

        if len(tokens) > 1 and tokens[1].isdigit():
            c_idx = int(tokens[1])
        else:
            c_idx = None

        if da_idx < 0 or da_idx >= len(self.da_set):
            return None
        if c_idx is not None:
            if c_idx < 0 or c_idx >= len(self.concept_set):
                return None

        if c_idx is None:
            result = self.da_set[da_idx]
        else:
            result = "-".join([self.da_set[da_idx], self.concept_set[c_idx]])

        if result in self.terminal_symbols:
            return result
        else:
            return None

    def encode_terminal(self, terminal):
        tokens = terminal.split('-')
        if len(tokens) < 2:
            return str(self.da_set.index(tokens[0]))
        return '-'.join([str(self.da_set.index(tokens[0])),
                         str(self.concept_set.index(tokens[1]))])

    """
    Print methods
    """
    def print_terminal_set(self):
        print str(len(self.terminal_symbols)) + " terminal symbols"
        for idx, da in enumerate(self.da_set):
            print da + "(" + str(idx) + ")",
        print
        for idx, c in enumerate(self.concept_set):
            print c + "(" + str(idx) + ")",
        print

    def print_last_chart(self):
        print len(self.chart)
        c = self.chart[-1]
        for cc in c:
            if (self.is_top_down and cc[self.RULE][self.LHS] == "START") or \
                    (not self.is_top_down and cc[self.RULE][self.LHS] == "S"):
                print cc

    def print_chart(self, with_parse=True):
        for idx, c in enumerate(self.chart):
            print idx
            for cc in c:
                if not with_parse:
                    print (cc[self.RULE], cc[self.DOT], cc[self.POS], cc[self.OPERATOR])
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

    def print_train_set(self):
        count = 0
        for lhs, rules in self.grammar.iteritems():
            if len(rules) > 1:
                print lhs + " -> " + str(len(rules)) + " actions"
                count += 1
        print str(count) + " trainable dialog agency"
    """
    Main Functions
    """

    def __init__(self, parse_type):
        super(DialogParser, self).__init__()
        if parse_type == "top_down":
            self.is_top_down = True
            self.start_rule = (('S', ['START', 'eos']), 0, 0, '(S START eos)', 'predict')
        else:
            self.is_top_down = False
            self.start_rule = (('S', ['START', 'eos']), 0, 0, '', 'predict')

    def completer(self, s, idx):
        c = self.chart[s[self.POS]]
        lhs = s[self.RULE][self.LHS]
        parse = s[self.PARSE]
        modified = False

        for ss in c:
            ss_lhs = ss[self.RULE][self.LHS]
            dot = ss[self.DOT]
            if self.incomplete(ss):
                dot_symbol = ss[self.RULE][self.RHS][dot]
                if dot_symbol == lhs:
                    if self.is_top_down:
                        parse_symbol = ss[self.PARSE]
                        if DialogParser.is_recursive(lhs) and parse_symbol.count(lhs) > 1:
                            parse = parse[1:-1].replace(lhs, "")
                        parse_symbol = Utils.rev_replace(parse_symbol, lhs, parse, 1)
                    else:
                        if DialogParser.is_recursive(lhs) and lhs == ss_lhs:
                            parse_symbol = ss[self.PARSE] + parse.strip()
                        else:
                            parse_symbol = ss[self.PARSE] + '(' + lhs + ' ' + parse.strip() + ')'

                    new_s = (ss[self.RULE], ss[self.DOT] + 1, ss[self.POS], parse_symbol, 'complete')
                    modified = self.add_to_chart(new_s, idx)

        return modified

    def scanner(self, s, idx, tokens):
        dot = s[self.DOT]
        dot_symbol = s[self.RULE][self.RHS][dot]

        if self.is_top_down:
            parse_symbol = ""
        else:
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

            new_s = (s[self.RULE], s[self.DOT] + 1, s[self.POS], s[self.PARSE] + parse_symbol, 'scanner')
            modified = self.add_to_chart(new_s, chart_idx)

        return modified

    def predictor(self, s, idx):
        dot = s[self.DOT]
        dot_symbol = s[self.RULE][self.RHS][dot]
        s_rules = self.grammar[dot_symbol]
        modified = False
        for sr in s_rules:
            if self.is_top_down:
                parse_symbol = "(" + dot_symbol + " " + " ".join(sr) + ")"
            else:
                parse_symbol = ""
            new_s = ((dot_symbol, sr), 0, idx, parse_symbol, 'predict')
            added = self.add_to_chart(new_s, idx)
            if not modified and added:
                modified = True
        return modified

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

    def inc_parse(self, x):
        """
        Parse a partial dialog with the last turn scanned
        :param x:
        :return:
        """
        norm_x = self.normalize_input(x, with_eos=False)
        self.chart = [[] for i in range(len(norm_x)+1)]
        # (lhs, rhs), dot, pos, parse, operator_type
        self.chart[0] = [self.start_rule]

        for i in range(len(self.chart)-1):
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

        # conduct completer on the last chart
        stable = False
        i = len(self.chart)-1
        while not stable:
            ever_updated = False
            s_idx = 0
            while s_idx < len(self.chart[i]):
                s = self.chart[i][s_idx]
                updated = self.completer(s, i)
                s_idx += 1
                if not ever_updated and updated:
                    ever_updated = True
                stable = not ever_updated

        # return all parses
        last_c = self.chart[-1]
        parses = []
        for cc in last_c:
            if (self.is_top_down and cc[self.RULE][self.LHS] == "START") or \
                        (not self.is_top_down and cc[self.RULE][self.LHS] == "S"):
                    parses.append(cc[self.PARSE])
        return parses


