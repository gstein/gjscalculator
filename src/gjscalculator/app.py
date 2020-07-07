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

# Keys to clear the expression
CLEAR_EXPR = {
    '\x1b',  # ESCAPE
    '\x7f',  # ALT-BACKSPACE
    }

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

        row, self.expr = make_display_item('INPUT')
        main_box.add(row)

        row, self.result = make_display_item('RESULT')
        main_box.add(row)

        self.have_alts = [ ]

        def make_row(*labels):
            # place the buttons along a single row
            row = toga.Box(style=Pack(direction=ROW))
            btns = [ ]
            for l in labels:
                if isinstance(l, Button):
                    btn = l
                else:
                    btn = Button(l)
                btns.append(btn)
                row.add(btn)
                if btn.alt:
                    self.have_alts.append(btn)
            main_box.add(row)

        make_row(Button('C', lfunc=lambda x: '',
                        alt='MC', afunc=self.memory_clear),
                 Button('MR', lfunc=lambda x: self.mvalue,
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

        row, self.memory = make_display_item('MEMORY')
        self.set_memory(None)
        main_box.add(row)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

        ### for GTK:
        self.main_window._impl.native.connect('key-press-event', self.key_press_handler)
        self.main_window._impl.native.connect('key-release-event', self.key_release_handler)

    def set_expr(self, new):
        self.expr.value = str(new)
        self.result.value = compute(self.expr.value)

    def set_memory(self, value):
        self.mvalue = value
        self.memory.value = value or ''

    def result_as_float(self):
        try:
            return float(self.result.value)
        except ValueError:
            return None

    def perform(self, func):
        new = func(self.result_as_float())
        if new is not None:
            self.set_expr(new)
        # else: don't change the expression

    def all_clear(self, *_):
        self.memory_clear()
        return ''

    def memory_set(self, value):
        self.set_memory(value)
        return None

    def memory_clear(self, *_):
        self.set_memory(None)
        return None

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
            self.set_expr(self.expr.value + c)

    def backspace(self, *_):
        self.set_expr(self.expr.value[:-1])

    def key_press_handler(self, window, event):
        print('PRESS:', repr(event.string), event.state, event.keyval)
        if len(event.string) == 1:
            if event.string in CLEAR_EXPR:
                self.set_expr('')
            elif event.string == '\r':
                # Operate like the "=" button. Copy result to expr.
                self.set_expr(self.result.value)
            elif event.string == '\x08':  # BACKSPACE
                self.backspace()
            elif event.string == 'q' or event.string == 'Q':
                self.exit()
            else:
                self.add_character(event.string)
        elif event.keyval in SHOW_ALT:
            for btn in self.have_alts:
                btn.label = btn.alt
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
            for btn in self.have_alts:
                btn.label = btn.original


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


def make_display_item(label):
    row = toga.Box(style=Pack(direction=ROW))
    label = toga.Label(label)
    label.style.padding = 5
    label.style.flex = 1
    label.style.text_align = 'right'
    label.style.font_weight = 'bold'
    row.add(label)
    value = toga.TextInput('something', readonly=True)
    value.style.padding = 5
    value.style.flex = 5
    row.add(value)
    return row, value


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
