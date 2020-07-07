"""
Simple calculator
"""
import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

### we're hard-coding for GTK/GDK right now
from gi.repository import Gdk

# Keycodes to show the "alternate" buttons
SHOW_ALT = {
    Gdk.KEY_Control_L,
    Gdk.KEY_Control_R,
    }

# Special characters for display
CHR_DIVIDE = '\u00f7'
CHR_MULTIPLY = '\u00d7'
CHR_BACKSPACE = '\u232b'

# Characters allowed for insertion to EXPR
ALLOWED_CHR = (
    '0123456789+-*/().'
    + CHR_DIVIDE
    + CHR_MULTIPLY
    )


class GJSCalculator(toga.App):

    def startup(self):
        """
        Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        # stack a number of rows in a single column
        main_box = toga.Box(style=Pack(direction=COLUMN))

        self.expr = make_display_item()
        main_box.add(self.expr)

        self.result = make_display_item()
        self.result.value = 'RESULT:'
        main_box.add(self.result)

        self.buttons = [ ]
        self.alts = [ ]

        def make_row(*labels):
            # place the buttons along a single row
            row = toga.Box(style=Pack(direction=ROW))
            btns = [ ]
            for l in labels:
                if isinstance(l, Button):
                    if l.alt:
                        self.alts.append((len(self.buttons), len(btns), l.label, l.alt))
                    btn = l
                elif isinstance(l, tuple):
                    # two forms:
                    # NAME, ALTNAME, ALTPERFORM
                    # NAME, PERFORM, ALTNAME, ALTPERFORM
                    self.alts.append((len(self.buttons), len(btns), l[0], l[1]))
                    btn = Button(l[0])
                else:
                    btn = Button(l)
                btns.append(btn)
                row.add(btn)
            self.buttons.append(btns)
            main_box.add(row)

        make_row(Button('C', lfunc=self.expr_clear,
                        alt='MC', afunc=self.memory_clear),
                 Button('MR', lfunc=self.memory_recall,
                        alt='MS', afunc=self.memory_set),
                 Button('M+', lfunc=self.memory_add,
                        alt='M-', afunc=self.memory_subtract),
                 Button(CHR_BACKSPACE, lfunc=self.backspace,
                        alt='AC', afunc=self.all_clear))
        make_row(Button('7', alt='('),
                 '8',
                 Button('9', alt=')'),
                 Button(CHR_DIVIDE, alt='1/x', afunc=lambda x: 1.0/x))
        make_row('4', '5', '6', CHR_MULTIPLY)
        make_row('1', '2', '3',
                 Button('-', alt='+/-', afunc=lambda x: -x))
        make_row('.', '0',
                 Button('=', lfunc=lambda x: x),  # Copy RESULT to EXPR
                 '+',
                 )

        self.memory = make_display_item()
        self.set_memory(None)
        main_box.add(self.memory)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

        ### for GTK:
        self.main_window._impl.native.connect('key-press-event', self.key_press_handler)
        self.main_window._impl.native.connect('key-release-event', self.key_release_handler)

    def update(self):
        self.result.value = compute(self.expr.value)

    def set_memory(self, value):
        self.mvalue = value
        if value is None:
            self.memory.value = 'MEM: <unset>'
        else:
            self.memory.value = 'MEM: %s' % (value,)

    def result_as_float(self):
        try:
            return float(self.result.value)
        except ValueError:
            return None

    def perform(self, func):
        new = func(self.result_as_float())
        if new is not None:
            self.expr.value = new
            self.update()
        # else: don't change the expression

    def expr_clear(self, *_):
        return ''

    def all_clear(self, *_):
        self.memory_clear()
        return ''

    def memory_set(self, value):
        self.set_memory(value)
        return None

    def memory_clear(self, *_):
        self.set_memory(None)
        return None

    def memory_recall(self, *_):
        return self.mvalue  # might be None

    def memory_add(self, value):
        if self.mvalue is None:
            self.set_memory(value)
        else:
            self.set_memory(float(self.mvalue) + value)
        return None

    def memory_subtract(self, value):
        if self.mvalue is None:
            self.set_memory(-value)
        else:
            self.set_memory(float(self.mvalue) - value)
        return None

    def add_character(self, c):
        if c in ALLOWED_CHR:
            self.expr.value += c
            self.update()

    def backspace(self, *_):
        self.expr.value = self.expr.value[:-1]
        self.update()

    def key_press_handler(self, window, event):
        print('PRESS:', repr(event.string), event.state, event.keyval)
        if len(event.string) == 1:
            if event.string == '\x1b':  # ESCAPE
                self.expr.value = ''
            elif event.string == '\r':
                # Operate like the "=" button. Copy result to expr.
                self.expr.value = self.result.value
            elif event.string == '\x08':  # BACKSPACE
                self.backspace()
                return
            elif event.string == '\x7f':  # ALT-BACKSPACE
                self.expr.value = ''
            elif event.string == 'q' or event.string == 'Q':
                self.exit()
                return
            else:
                self.add_character(event.string)
                return

            self.update()
        elif event.keyval in SHOW_ALT:
            # ROW, COLUMN, ORIGINAL, ALT
            for r, c, o, a in self.alts:
                #print('SWITCH:', r, c, o, a, self.buttons[r][c].label)
                self.buttons[r][c].label = a
        elif event.state & Gdk.ModifierType.SHIFT_MASK:
            print('SHIFT')
        elif event.state & Gdk.ModifierType.CONTROL_MASK:
            print('CONTROL')
        elif event.state & Gdk.ModifierType.MOD1_MASK:
            print('ALT')
        else:
            self.expr.value = '<unknown>'

    def key_release_handler(self, window, event):
        print('RELEASE:', repr(event.string), event.state, event.keyval)
        if event.keyval in SHOW_ALT:
            # ROW, COLUMN, ORIGINAL, ALT
            for r, c, o, a in self.alts:
                #print('RESTORE:', r, c, o, a, self.buttons[r][c].label)
                self.buttons[r][c].label = o


def compute(expr):
    if not expr:
        return ''
    expr = expr.replace(CHR_MULTIPLY, '*')
    expr = expr.replace(CHR_DIVIDE, '/')
    print('EVAL:', repr(expr))
    try:
        # Just use Python to evaluate this, but do it SAFE.
        return float(eval(expr, _EMPTY_NS, _EMPTY_NS))
    except:
        return '#EVAL'
_EMPTY_NS = { '__builtins__': {}, }


def make_display_item():
    label = toga.TextInput('something', readonly=True)
    label.style.padding = 5
    label.style.flex = 1
    return label


class Button(toga.Button):
    def __init__(self, original, *, alt=None, lfunc=None, afunc=None):
        super().__init__(original, on_press=self.click)

        self.style.padding = 5
        self.style.flex = 1

        ### GTK specific
        self._impl.native.set_focus_on_click(False)

        self.original = original
        self.alt = alt
        self.lfunc = lfunc
        self.afunc = afunc

    def click(self, widget):
        if self.label == self.original and self.lfunc:
            # Perform the (original) label function
            self.app.perform(self.lfunc)
        elif self.label == self.alt and self.afunc:
            # Perform the alternate function
            self.app.perform(self.afunc)
        else:
            # Simple insertion of the current label.
            self.app.add_character(self.label)


def main():
    return GJSCalculator()
