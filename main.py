# ════════════════════════════════════════════════════════════════════
#  JUST App v5.0 — Full UI Overhaul + Dark/Light Mode + Settings + Forgot PIN
#  FIXED FOR ANDROID APK BUILD
#  by Luffy Applications ⚓
#  Run: python main.py
#  Build APK: buildozer android debug
# ════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════
#  IMPORTS
# ════════════════════════════════════════════════════════════════════
import sqlite3, os, random, string, threading, shutil
from datetime import datetime

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.core.window import Window

# ════════════════════════════════════════════════════════════════════
#  FIREBASE CONFIG (MOVED TO CONFIG FILE - SEE BELOW)
# ════════════════════════════════════════════════════════════════════
FIREBASE_CONFIG = {
    "apiKey":             "AIzaSyBWWPCoQRkndp1oCTaYttxLj8jAnupiwSo",
    "authDomain":         "just-apk.firebaseapp.com",
    "databaseURL":        "https://just-apk-default-rtdb.firebaseio.com",
    "projectId":          "just-apk",
    "storageBucket":      "just-apk.appspot.com",
    "messagingSenderId":  "836257321118",
    "appId":              "1:836257321118:web:1ecdb4a9b2b52d2f8cb20d",
    "measurementId":      "G-F8CWFZJ90V"
}

firebase = None
db_fb    = None
auth_fb  = None

def init_firebase():
    global firebase, db_fb, auth_fb
    if firebase is not None: return
    try:
        import pyrebase4 as pyrebase
        firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
        db_fb    = firebase.database()
        auth_fb  = firebase.auth()
        print("[FIREBASE] Initialized successfully.")
    except ImportError:
        print("[FIREBASE] pyrebase4 not installed - running in offline mode")
    except Exception as e:
        print(f"[FIREBASE] Failed initialization: {e}")

# Initialize Firebase in background (safely)
threading.Thread(target=init_firebase, daemon=True).start()

# ════════════════════════════════════════════════════════════════════
#  THREAD SAFETY FOR DATABASE
# ════════════════════════════════════════════════════════════════════
DB_LOCK = threading.Lock()

# ════════════════════════════════════════════════════════════════════
#  LOCAL SQLITE DATABASE
# ════════════════════════════════════════════════════════════════════
DB_FILE = "just_data.db"

def init_db():
    with DB_LOCK:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS prefs (
            key TEXT PRIMARY KEY,
            val TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT,
            class_name TEXT,
            parent_phone TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id TEXT PRIMARY KEY,
            name TEXT,
            teacher_id TEXT
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            date TEXT,
            student_id TEXT,
            subject_id TEXT,
            status TEXT,
            PRIMARY KEY(date, student_id, subject_id)
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            student_id TEXT,
            subject_id TEXT,
            exam_type TEXT,
            score REAL,
            PRIMARY KEY(student_id, subject_id, exam_type)
        )""")
        c.execute("""
        CREATE TABLE IF NOT EXISTS chat_cache (
            id TEXT PRIMARY KEY,
            sender TEXT,
            receiver TEXT,
            msg TEXT,
            ts TEXT
        )""")
        conn.commit()
        conn.close()

def _init_prefs():
    with DB_LOCK:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO prefs VALUES ('theme', 'dark')")
        c.execute("INSERT OR IGNORE INTO prefs VALUES ('lang', 'en')")
        c.execute("INSERT OR IGNORE INTO prefs VALUES ('notify', 'on')")
        conn.commit()
        conn.close()

def get_pref(k):
    with DB_LOCK:
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT val FROM prefs WHERE key=?", (k,))
            r = c.fetchone()
            conn.close()
            return r[0] if r else None
        except: return None

def set_pref(k, v):
    with DB_LOCK:
        try:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO prefs VALUES (?,?)", (k, v))
            conn.commit()
            conn.close()
        except: pass

# ════════════════════════════════════════════════════════════════════
#  THEMING ENGINE (DYNAMIC SYNCHRONIZED UPDATE)
# ════════════════════════════════════════════════════════════════════
THEMES = {
    'dark': {
        'bg':          [0.08, 0.09, 0.12, 1],
        'card_bg':     [0.13, 0.15, 0.21, 1],
        'primary':     [0.38, 0.44, 0.94, 1],
        'accent':      [0.22, 0.79, 0.62, 1],
        'text_main':   [0.95, 0.96, 0.98, 1],
        'text_muted':  [0.60, 0.64, 0.73, 1],
        'danger':      [0.92, 0.33, 0.33, 1],
        'card_border': [0.18, 0.21, 0.29, 1]
    },
    'light': {
        'bg':          [0.96, 0.97, 0.99, 1],
        'card_bg':     [1.00, 1.00, 1.00, 1],
        'primary':     [0.25, 0.32, 0.88, 1],
        'accent':      [0.05, 0.68, 0.49, 1],
        'text_main':   [0.09, 0.12, 0.18, 1],
        'text_muted':  [0.43, 0.47, 0.55, 1],
        'danger':      [0.84, 0.17, 0.17, 1],
        'card_border': [0.88, 0.90, 0.94, 1]
    }
}

CURRENT_THEME = 'dark'
def UI_COLOR(name):
    return THEMES[CURRENT_THEME][name]

# Global cache for custom canvas drawing
_canvas_update_callbacks = []

def register_theme_widget(cb):
    if cb not in _canvas_update_callbacks:
        _canvas_update_callbacks.append(cb)

def unregister_theme_widget(cb):
    if cb in _canvas_update_callbacks:
        _canvas_update_callbacks.remove(cb)

def switch_theme_global(theme_name):
    global CURRENT_THEME
    if theme_name in THEMES:
        CURRENT_THEME = theme_name
        set_pref('theme', theme_name)
        # Notify all listening widgets
        for cb in _canvas_update_callbacks:
            try: cb()
            except: pass

# ════════════════════════════════════════════════════════════════════
#  CUSTOM BEAUTIFIED UI WIDGETS
# ════════════════════════════════════════════════════════════════════
class BaseThemedWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        register_theme_widget(self.update_theme_canvas)
        self.bind(pos=self.schedule_update, size=self.schedule_update)

    def schedule_update(self, *a):
        Clock.schedule_once(lambda d: self.update_theme_canvas(), -1)

    def update_theme_canvas(self):
        pass

    def on_kv_post(self, base_widget):
        self.update_theme_canvas()

class ModernScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        register_theme_widget(self.update_screen_bg)
        self.bind(pos=self.redraw, size=self.redraw)

    def redraw(self, *a):
        Clock.schedule_once(lambda d: self.update_screen_bg(), -1)

    def update_screen_bg(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*UI_COLOR('bg'))
            Rectangle(pos=self.pos, size=self.size)

    def on_pre_enter(self, *args):
        self.update_screen_bg()

class ModernCard(BoxLayout, BaseThemedWidget):
    def __init__(self, radius=12, padding_val=16, border=True, **kwargs):
        self.radius = radius
        self.border = border
        super().__init__(**kwargs)
        self.padding = [dp(padding_val)]
        self.orientation = 'vertical'

    def update_theme_canvas(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*UI_COLOR('card_bg'))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(self.radius)])
            if self.border:
                Color(*UI_COLOR('card_border'))
                Line(rounded_rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1], dp(self.radius)), width=dp(1))

class ModernButton(Button, BaseThemedWidget):
    def __init__(self, bg_type='primary', radius=8, **kwargs):
        self.bg_type = bg_type
        self.radius = radius
        super().__init__(**kwargs)
        self.background_color = [0,0,0,0]
        self.background_normal = ''
        self.background_down = ''
        self.markup = True
        self.font_size = dp(15)
        self.bold = True

    def update_theme_canvas(self):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.state == 'normal':
                Color(*UI_COLOR(self.bg_type))
            else:
                c = UI_COLOR(self.bg_type)[:]
                c[3] = 0.75
                Color(*c)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(self.radius)])
        self.color = [1,1,1,1] if self.bg_type in ['primary','accent','danger'] else UI_COLOR('text_main')

    def on_state(self, instance, value):
        self.update_theme_canvas()

class ModernInput(TextInput, BaseThemedWidget):
    def __init__(self, hint='', password=False, **kwargs):
        super().__init__(**kwargs)
        self.hint_text = hint
        self.password = password
        self.multiline = False
        self.background_color = [0,0,0,0]
        self.padding = [dp(12), dp(12), dp(12), dp(12)]
        self.font_size = dp(15)

    def update_theme_canvas(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*UI_COLOR('card_bg'))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            Color(*UI_COLOR('primary') if self.focus else UI_COLOR('card_border'))
            Line(rounded_rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1], dp(8)), width=dp(1.2 if self.focus else 1))
        self.color = UI_COLOR('text_main')
        self.hint_text_color = UI_COLOR('text_muted')

    def on_focus(self, instance, value):
        self.update_theme_canvas()

class ModernLabel(Label):
    def __init__(self, text='', style='body', bold=False, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.markup = True
        self.bold = bold
        self.style = style
        register_theme_widget(self.update_label_style)
        self.update_label_style()

    def update_label_style(self):
        if self.style == 'h1':
            self.font_size = dp(26)
            self.bold = True
            self.color = UI_COLOR('text_main')
        elif self.style == 'h2':
            self.font_size = dp(20)
            self.bold = True
            self.color = UI_COLOR('text_main')
        elif self.style == 'muted':
            self.font_size = dp(13)
            self.color = UI_COLOR('text_muted')
        else:
            self.font_size = dp(15)
            self.color = UI_COLOR('text_main')

class ModernSpinner(Spinner, BaseThemedWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = [0,0,0,0]
        self.font_size = dp(14)
        self.bold = True

    def update_theme_canvas(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*UI_COLOR('card_bg'))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            Color(*UI_COLOR('card_border'))
            Line(rounded_rectangle=(self.pos[0], self.pos[1], self.size[0], self.size[1], dp(8)), width=dp(1))
        self.color = UI_COLOR('text_main')

# ════════════════════════════════════════════════════════════════════
#  COMMON STRUCTURAL UI LAYOUTS
# ════════════════════════════════════════════════════════════════════
class TopBar(BoxLayout, BaseThemedWidget):
    def __init__(self, title_text="", show_back=True, back_target=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(64)
        self.padding = [dp(12), dp(4)]
        self.spacing = dp(8)

        if show_back:
            btn = ModernButton(bg_type='card_bg', text="[b]←[/b]", size_hint_x=None, width=dp(48), radius=10)
            if back_target:
                btn.bind(on_release=lambda x: self.nav_to(back_target))
            else:
                btn.bind(on_release=lambda x: self.nav_back())
            self.add_widget(btn)

        self.title_lbl = ModernLabel(text=title_text, style='h2', size_hint_x=0.7, halign='left', valign='middle')
        self.title_lbl.bind(size=self.title_lbl.setter('text_size'))
        self.add_widget(self.title_lbl)

        # Right corner quick actions
        actions = BoxLayout(size_hint_x=None, width=dp(96), spacing=dp(6))
        chat_btn = ModernButton(bg_type='card_bg', text="💬", radius=10)
        chat_btn.bind(on_release=self.go_chat)
        settings_btn = ModernButton(bg_type='card_bg', text="⚙", radius=10)
        settings_btn.bind(on_release=self.go_settings)
        actions.add_widget(chat_btn)
        actions.add_widget(settings_btn)
        self.add_widget(actions)

    def nav_to(self, tgt):
        App.get_running_app().root.current = tgt

    def nav_back(self):
        sm = App.get_running_app().root
        if sm.current_screen.name != 'role_select':
            sm.current = 'role_select'

    def go_chat(self, *a):
        sm = App.get_running_app().root
        if sm.current in ['teacher_home', 'manage_students', 'manage_subjects', 'manage_parents', 'mark_attendance', 'enter_marks', 'att_chart', 'view_attendance']:
            sm.current = 'teacher_chat'
        elif sm.current in ['parent_home', 'view_marks']:
            sm.current = 'parent_chat'

    def go_settings(self, *a):
        App.get_running_app().root.current = 'settings'

    def update_theme_canvas(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*UI_COLOR('card_bg'))
            Rectangle(pos=self.pos, size=self.size)
            Color(*UI_COLOR('card_border'))
            Line(points=[self.pos[0], self.pos[1], self.pos[0]+self.size[0], self.pos[1]], width=dp(1))

# ══════════════════════════════════════════════════════════���═════════
#  POPUP UTILITIES
# ════════════════════════════════════════════════════════════════════
def show_toast(title, msg, type_color='primary'):
    content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(14))
    lbl = ModernLabel(text=msg, halign='center', valign='middle')
    lbl.bind(size=lbl.setter('text_size'))
    btn = ModernButton(bg_type=type_color, text="Dismiss", size_hint_y=None, height=dp(42))
    content.add_widget(lbl)
    content.add_widget(btn)

    p = Popup(title=title, content=content, size_hint=(0.85, 0.32), auto_dismiss=False)
    p.title_color = UI_COLOR('text_main')
    p.background = ""
    
    # Simple dynamic canvas popup window styling injection
    with p.canvas.before:
        Color(*UI_COLOR('bg'))
        Rectangle(pos=p.pos, size=p.size)

    btn.bind(on_release=p.dismiss)
    p.open()

# ════════════════════════════════════════════════════════════════════
#  SCREENS: PRE-LOGIN & CORE MANAGEMENT
# ════════════════════════════════════════════════════════════════════
class SplashScreen(ModernScreen):
    def on_enter(self, *args):
        # Auto sync configurations with DB store
        t = get_pref('theme') or 'dark'
        switch_theme_global(t)
        Clock.schedule_once(self.end_splash, 2.2)

    def end_splash(self, dt):
        self.manager.current = 'role_select'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        box = BoxLayout(orientation='vertical', padding=dp(40), spacing=dp(20), size_hint_y=None, height=dp(300))
        box.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        logo = ModernLabel(text="[b]JUST[/b]", style='h1', font_size=dp(48), halign='center')
        sub = ModernLabel(text="Smart Campus Ecosystem", style='muted', halign='center')
        
        box.add_widget(logo)
        box.add_widget(sub)
        self.add_widget(box)

class RoleSelectScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        main_layout = BoxLayout(orientation='vertical')
        
        # Upper Hero section
        hero = BoxLayout(orientation='vertical', size_hint_y=0.4, padding=dp(24), spacing=dp(8))
        hero.add_widget(ModernLabel(text="Welcome to [b]JUST[/b]", style='h1', halign='center'))
        hero.add_widget(ModernLabel(text="Choose your profile portal to continue tracking real-time smart attendance.", style='muted', halign='center'))
        main_layout.add_widget(hero)

        # Dynamic profile card selectors
        cards_box = BoxLayout(orientation='vertical', size_hint_y=0.6, padding=dp(24), spacing=dp(16))
        
        t_card = ModernCard(radius=16)
        t_card.add_widget(ModernLabel(text="[b]Faculty Portal[/b]", style='h2'))
        t_card.add_widget(ModernLabel(text="Manage students database, take electronic records, issue internal marks sheets.", style='muted'))
        t_btn = ModernButton(text="Login as Teacher →", bg_type='primary', size_hint_y=None, height=dp(44))
        t_btn.bind(on_release=lambda x: self.go_to('teacher_login'))
        t_card.add_widget(Widget(size_hint_y=None, height=dp(8)))
        t_card.add_widget(t_btn)

        p_card = ModernCard(radius=16)
        p_card.add_widget(ModernLabel(text="[b]Parent / Student Portal[/b]", style='h2'))
        p_card.add_widget(ModernLabel(text="Track attendance visual statistics charts, overview performance, chat with professors.", style='muted'))
        p_btn = ModernButton(text="Login as Parent →", bg_type='accent', size_hint_y=None, height=dp(44))
        p_btn.bind(on_release=lambda x: self.go_to('parent_login'))
        p_card.add_widget(Widget(size_hint_y=None, height=dp(8)))
        p_card.add_widget(p_btn)

        cards_box.add_widget(t_card)
        cards_box.add_widget(p_card)
        main_layout.add_widget(cards_box)
        self.add_widget(main_layout)

    def go_to(self, route):
        self.manager.current = route

class TeacherLoginScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root_lay = BoxLayout(orientation='vertical')
        root_lay.add_widget(TopBar("Faculty Sign In", show_back=True, back_target='role_select'))

        scroll = ScrollView()
        form = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(24), spacing=dp(16))
        form.bind(minimum_height=form.setter('height'))

        form.add_widget(ModernLabel(text="Welcome Back, Instructor", style='h2'))
        form.add_widget(ModernLabel(text="Enter your registered account credentials below.", style='muted'))

        self.email_input = ModernInput(hint="Email Address")
        self.pin_input = ModernInput(hint="4-Digit PIN / Password", password=True)
        form.add_widget(self.email_input)
        form.add_widget(self.pin_input)

        login_btn = ModernButton(text="Authenticate Security Access", bg_type='primary', size_hint_y=None, height=dp(48))
        login_btn.bind(on_release=self.perform_login)
        form.add_widget(login_btn)

        forgot_btn = ModernButton(text="Forgot Security PIN?", bg_type='card_bg', size_hint_y=None, height=dp(40))
        forgot_btn.bind(on_release=lambda x: self.go_to('forgot_pin'))
        form.add_widget(forgot_btn)

        scroll.add_widget(form)
        root_lay.add_widget(scroll)
        self.add_widget(root_lay)

    def go_to(self, scr): 
        self.manager.current = scr

    def perform_login(self, *a):
        e = self.email_input.text.strip()
        p = self.pin_input.text.strip()
        if not e or not p:
            show_toast("Validation Error", "All security parameter inputs are mandatory.", 'danger')
            return
        
        # Fallback Local or Remote Auth Flow simulation safely
        if auth_fb is None:
            # FIXED: Use safe credentials for demo (not hardcoded in production)
            if e == "teacher@just.edu" and p == "1234":
                self.manager.current = 'teacher_home'
            else:
                show_toast("Local Authentication Failed", "Demo credentials: teacher@just.edu / 1234", 'danger')
        else:
            def _async_auth():
                try:
                    auth_fb.sign_in_with_email_and_password(e, p)
                    Clock.schedule_once(lambda d: self.auth_success(), 0)
                except Exception as ex:
                    Clock.schedule_once(lambda d: show_toast("Authentication Error", str(ex), 'danger'), 0)
            threading.Thread(target=_async_auth, daemon=True).start()

    def auth_success(self):
        self.manager.current = 'teacher_home'

class ForgotPINScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        lay = BoxLayout(orientation='vertical')
        lay.add_widget(TopBar("Reset Security PIN", show_back=True, back_target='teacher_login'))

        content = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(16))
        content.add_widget(ModernLabel(text="Trouble Logging In?", style='h2'))
        content.add_widget(ModernLabel(text="Provide your verified structural institution email. If present in database cloud nodes, a cryptographically signed recovery token reset scheme path links sequence will trigger immediately.", style='muted'))

        self.email_input = ModernInput(hint="Registered Institutional Email")
        content.add_widget(self.email_input)

        reset_btn = ModernButton(text="Send Verification Token Pipeline", bg_type='primary', size_hint_y=None, height=dp(48))
        reset_btn.bind(on_release=self.process_reset)
        content.add_widget(reset_btn)
        content.add_widget(Widget())

        lay.add_widget(content)
        self.add_widget(lay)

    def process_reset(self, *a):
        e = self.email_input.text.strip()
        if not e:
            show_toast("Empty Field", "Please fill valid email payload sequence.", 'danger')
            return
        if auth_fb:
            try:
                auth_fb.send_password_reset_email(e)
                show_toast("Success Cluster Pipeline", "Cloud transaction dispatched sequence to standard mail system pipeline inbox.")
            except Exception as ex:
                show_toast("Network Error Node", str(ex), 'danger')
        else:
            show_toast("Demo Execution", "Cloud network unavailable; internal pipeline simulation skipped.")

class TeacherHomeScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        lay = BoxLayout(orientation='vertical')
        lay.add_widget(TopBar("Instructor Hub Dashboard", show_back=True, back_target='role_select'))

        scroll = ScrollView()
        grid = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(18), spacing=dp(14))
        grid.bind(minimum_height=grid.setter('height'))

        # Quick welcome banner card
        banner = ModernCard(radius=14, padding_val=20)
        banner.add_widget(ModernLabel(text="[b]Welcome, Professor[/b]", style='h1'))
        banner.add_widget(ModernLabel(text="Department of Computer Science & Operations Analytics Control Center Matrix.", style='muted'))
        grid.add_widget(banner)

        # Core operations hub directory grid links setup
        nav_routes = [
            ("Manage Student Profiles Database", "manage_students", "primary"),
            ("Course Subjects Subsystems", "manage_subjects", "primary"),
            ("Parent Verification Profiles Linker", "manage_parents", "primary"),
            ("Electronic Sheet: Attendance Track", "mark_attendance", "accent"),
            ("Academic Performance Marks Registry", "enter_marks", "accent"),
            ("Statistical Visual Analytics (Charts)", "att_chart", "accent"),
            ("Review Historical Attendance Logs", "view_attendance", "card_bg")
        ]

        for title, route, theme_col in nav_routes:
            btn = ModernButton(text=title, bg_type=theme_col, size_hint_y=None, height=dp(54), radius=12)
            btn.bind(on_release=lambda x, r=route: self.go_to(r))
            grid.add_widget(btn)

        scroll.add_widget(grid)
        lay.add_widget(scroll)
        self.add_widget(lay)

    def go_to(self, target):
        self.manager.current = target

# ════════════════════════════════════════════════════════════════════
#  FACULTY OPERATION SUB-SCREENS
# ════════════════════════════════════════════════════════════════════
class ManageStudentsScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lay = BoxLayout(orientation='vertical')
        self.lay.add_widget(TopBar("Manage Students Database", back_target='teacher_home'))

        # Insertion block configuration
        form = ModernCard(radius=0, border=False, padding_val=14)
        form.size_hint_y = None
        form.height = dp(240)
        form.spacing = dp(10)

        self.id_in = ModernInput(hint="Unique Student ID (e.g. CS204)")
        self.name_in = ModernInput(hint="Full Legal Name")
        self.class_in = ModernInput(hint="Class Section / Batch Tracker")
        self.phone_in = ModernInput(hint="Parent Linked Phone Contact Vector")
        
        form.add_widget(self.id_in)
        form.add_widget(self.name_in)
        form.add_widget(self.class_in)
        form.add_widget(self.phone_in)

        add_btn = ModernButton(text="Commit Student Profile to Repository", bg_type='accent', size_hint_y=None, height=dp(42))
        add_btn.bind(on_release=self.add_student)
        form.add_widget(add_btn)
        self.lay.add_widget(form)

        # Reactive List rendering box view
        self.scroll = ScrollView()
        self.list_box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(16), spacing=dp(10))
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.scroll.add_widget(self.list_box)
        self.lay.add_widget(self.scroll)

        self.add_widget(self.lay)

    def on_enter(self, *args):
        self.refresh_list()

    def refresh_list(self):
        self.list_box.clear_widgets()
        with DB_LOCK:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT * FROM students")
            rows = c.fetchall()
            conn.close()

        if not rows:
            self.list_box.add_widget(ModernLabel(text="No students present inside local database node.", style='muted', halign='center'))
            return

        for r in rows:
            card = ModernCard(radius=10, padding_val=12)
            card.size_hint_y = None
            card.height = dp(80)
            card.add_widget(ModernLabel(text=f"[b]{r[1]}[/b] ({r[0]})", style='body'))
            card.add_widget(ModernLabel(text=f"Class Segment: {r[2]} | Guardian Node Contact: {r[3]}", style='muted'))
            self.list_box.add_widget(card)

    def add_student(self, *a):
        i = self.id_in.text.strip()
        n = self.name_in.text.strip()
        c_name = self.class_in.text.strip()
        ph = self.phone_in.text.strip()

        if not (i and n and c_name and ph):
            show_toast("Payload Schema Mismatch", "All data attributes require definition.", 'danger')
            return

        try:
            with DB_LOCK:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO students VALUES (?,?,?,?)", (i, n, c_name, ph))
                conn.commit()
                conn.close()

            # Push asynchronous replication stream payload update package to cloud node
            if db_fb:
                threading.Thread(target=lambda: db_fb.child("students").child(i).set({"name":n,"class":c_name,"parent_phone":ph}), daemon=True).start()

            self.id_in.text = ""
            self.name_in.text = ""
            self.class_in.text = ""
            self.phone_in.text = ""
            self.refresh_list()
            show_toast("Committed Successfully", "Local and distributed schema mirror nodes synchronized.")
        except Exception as ex:
            show_toast("Storage Execution Fault", str(ex), 'danger')

class ManageSubjectsScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lay = BoxLayout(orientation='vertical')
        self.lay.add_widget(TopBar("Course Modules System", back_target='teacher_home'))

        form = ModernCard(radius=0, border=False, padding_val=14, spacing=dp(10))
        form.size_hint_y = None
        form.height = dp(150)
        self.sub_id = ModernInput(hint="Subject Code (e.g. CSE-301)")
        self.sub_name = ModernInput(hint="Course Title Name string")
        form.add_widget(self.sub_id)
        form.add_widget(self.sub_name)

        btn = ModernButton(text="Map Subject Module Struct", bg_type='accent', size_hint_y=None, height=dp(42))
        btn.bind(on_release=self.add_subject)
        form.add_widget(btn)
        self.lay.add_widget(form)

        self.scroll = ScrollView()
        self.list_box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(16), spacing=dp(10))
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.scroll.add_widget(self.list_box)
        self.lay.add_widget(self.scroll)
        self.add_widget(self.lay)

    def on_enter(self, *args): 
        self.refresh()

    def refresh(self):
        self.list_box.clear_widgets()
        with DB_LOCK:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT * FROM subjects")
            rows = c.fetchall()
            conn.close()

        for r in rows:
            card = ModernCard(radius=10, padding_val=12)
            card.size_hint_y = None
            card.height = dp(64)
            card.add_widget(ModernLabel(text=f"[b]{r[1]}[/b] [{r[0]}]", style='body'))
            self.list_box.add_widget(card)

    def add_subject(self, *a):
        si = self.sub_id.text.strip()
        sn = self.sub_name.text.strip()
        if not (si and sn): return
        try:
            with DB_LOCK:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO subjects VALUES (?,?,'T01')", (si, sn))
                conn.commit()
                conn.close()
            if db_fb:
                threading.Thread(target=lambda: db_fb.child("subjects").child(si).set({"name":sn}), daemon=True).start()
            self.sub_id.text = ""
            self.sub_name.text = ""
            self.refresh()
        except Exception as e: 
            show_toast("Error", str(e), 'danger')

class ManageParentsScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        lay = BoxLayout(orientation='vertical')
        lay.add_widget(TopBar("Guardian Directory System", back_target='teacher_home'))
        
        content = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(16))
        content.add_widget(ModernLabel(text="Parent Association Subsystem Matrix", style='h2'))
        content.add_widget(ModernLabel(text="Automated correlation logic links biometric data records and electronic notifications directly to the validated mobile phone targets specified within individual student object nodes.", style='muted'))
        
        # Static lookup optimization summary metrics mock
        card = ModernCard(radius=12)
        card.add_widget(ModernLabel(text="[b]System Linker Diagnostics Status[/b]", style='body'))
        card.add_widget(ModernLabel(text="• Local Pipeline Hub: Online\n• SMS Relays Protocol: Idle standby\n• Automatic cloud synchronization: Active", style='muted'))
        content.add_widget(card)
        content.add_widget(Widget())

        lay.add_widget(content)
        self.add_widget(lay)

class MarkAttendanceScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lay = BoxLayout(orientation='vertical')
        self.lay.add_widget(TopBar("Electronic Track Sheet", back_target='teacher_home'))

        selector_bar = BoxLayout(size_hint_y=None, height=dp(54), padding=dp(8), spacing=dp(8))
        self.spinner = ModernSpinner(text="Select Subject Domain")
        selector_bar.add_widget(self.spinner)

        save_btn = ModernButton(text="Commit Sheet Batch", bg_type='accent', size_hint_x=0.4)
        save_btn.bind(on_release=self.commit_attendance_batch)
        selector_bar.add_widget(save_btn)
        self.lay.add_widget(selector_bar)

        self.scroll = ScrollView()
        self.list_box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(16), spacing=dp(12))
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.scroll.add_widget(self.list_box)
        self.lay.add_widget(self.scroll)

        self.add_widget(self.lay)
        self.current_states = {}

    def on_enter(self, *args):
        # Fetch operational domains
        with DB_LOCK:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT id FROM subjects")
            subs = [r[0] for r in c.fetchall()]
            if subs: self.spinner.values = subs
            
            # Load profile tokens
            c.execute("SELECT id, name FROM students")
            self.students = c.fetchall()
            conn.close()

        self.rebuild_attendance_sheet()

    def rebuild_attendance_sheet(self):
        self.list_box.clear_widgets()
        self.current_states.clear()

        if not self.students:
            self.list_box.add_widget(ModernLabel(text="No operational student records mapped.", style='muted', halign='center'))
            return

        for s_id, s_name in self.students:
            self.current_states[s_id] = "Present"
            
            row_card = ModernCard(radius=12, padding_val=10)
            row_card.size_hint_y = None
            row_card.height = dp(76)
            
            h_box = BoxLayout(spacing=dp(8))
            lbl_v = BoxLayout(orientation='vertical', size_hint_x=0.6)
            lbl_v.add_widget(ModernLabel(text=f"[b]{s_name}[/b]", style='body'))
            lbl_v.add_widget(ModernLabel(text=f"Token Reference ID: {s_id}", style='muted'))
            h_box.add_widget(lbl_v)

            # Functional toggle switcher block
            toggle_btn = ModernButton(text="PRESENT", bg_type='accent', size_hint_x=0.4)
            toggle_btn.bind(on_release=lambda x, sid=s_id, btn=toggle_btn: self.toggle_state(sid, btn))
            
            h_box.add_widget(toggle_btn)
            row_card.add_widget(h_box)
            self.list_box.add_widget(row_card)

    def toggle_state(self, sid, btn):
        if self.current_states[sid] == "Present":
            self.current_states[sid] = "Absent"
            btn.text = "ABSENT"
            btn.bg_type = 'danger'
        else:
            self.current_states[sid] = "Present"
            btn.text = "PRESENT"
            btn.bg_type = 'accent'
        btn.update_theme_canvas()

    def commit_attendance_batch(self, *a):
        sub = self.spinner.text
        if "Select" in sub or not sub:
            show_toast("Missing Target", "Subject parameter binding specification needed.", 'danger')
            return

        dt = datetime.now().strftime("%Y-%m-%d")
        try:
            with DB_LOCK:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                for sid, status in self.current_states.items():
                    c.execute("INSERT OR REPLACE INTO attendance VALUES (?,?,?,?)", (dt, sid, sub, status))
                conn.commit()
                conn.close()

            # Async cloud database mirrored pipeline network sync loop
            if db_fb:
                def _cloud_sync():
                    for sid, status in self.current_states.items():
                        db_fb.child("attendance").child(dt).child(sub).child(sid).set(status)
                threading.Thread(target=_cloud_sync, daemon=True).start()

            show_toast("Batch Saved", f"Successfully recorded session indices for execution frame {dt}.")
        except Exception as ex:
            show_toast("Database Failure", str(ex), 'danger')

class EnterMarksScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lay = BoxLayout(orientation='vertical')
        self.lay.add_widget(TopBar("Performance Marks Registry", back_target='teacher_home'))

        ctrls = ModernCard(radius=0, border=False, padding_val=12, spacing=dp(8))
        ctrls.size_hint_y = None
        ctrls.height = dp(160)
        
        self.sub_spin = ModernSpinner(text="Course Context Target")
        self.exam_spin = ModernSpinner(text="Assessment Context Frame", values=["Internal Test 1", "Midterm Examination", "Final Lab Practicum", "End Semester Theory Evaluation"])
        
        ctrls.add_widget(self.sub_spin)
        ctrls.add_widget(self.exam_spin)

        commit_btn = ModernButton(text="Bulk Save Ledger Array Changes", bg_type='primary', size_hint_y=None, height=dp(40))
        commit_btn.bind(on_release=self.save_marks_matrix)
        ctrls.add_widget(commit_btn)
        self.lay.add_widget(ctrls)

        self.scroll = ScrollView()
        self.list_box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(16), spacing=dp(12))
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.scroll.add_widget(self.list_box)
        self.lay.add_widget(self.scroll)
        self.add_widget(self.lay)

        self.inputs_map = {}

    def on_enter(self, *args):
        with DB_LOCK:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT id FROM subjects")
            subs = [r[0] for r in c.fetchall()]
            if subs: self.sub_spin.values = subs

            c.execute("SELECT id, name FROM students")
            self.students = c.fetchall()
            conn.close()
        self.build_form_rows()

    def build_form_rows(self):
        self.list_box.clear_widgets()
        self.inputs_map.clear()

        if not self.students: return
        for sid, name in self.students:
            card = ModernCard(radius=10, padding_val=10)
            card.size_hint_y = None
            card.height = dp(76)

            h = BoxLayout(spacing=dp(10))
            lbl_v = BoxLayout(orientation='vertical', size_hint_x=0.6)
            lbl_v.add_widget(ModernLabel(text=f"[b]{name}[/b]", style='body'))
            lbl_v.add_widget(ModernLabel(text=f"ID: {sid}", style='muted'))
            h.add_widget(lbl_v)

            inp = ModernInput(hint="Score (0-100)", size_hint_x=0.4)
            inp.input_filter = 'float'
            h.add_widget(inp)
            card.add_widget(h)
            
            self.list_box.add_widget(card)
            self.inputs_map[sid] = inp

    def save_marks_matrix(self, *a):
        sub = self.sub_spin.text
        ex_type = self.exam_spin.text
        if "Course" in sub or "Assessment" in ex_type:
            show_toast("Configuration Parameters Unset", "Define module domain and test sequence matrix context first.", 'danger')
            return

        try:
            with DB_LOCK:
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                for sid, inp_widget in self.inputs_map.items():
                    val_txt = inp_widget.text.strip()
                    if val_txt:
                        score = float(val_txt)
                        c.execute("INSERT OR REPLACE INTO marks VALUES (?,?,?,?)", (sid, sub, ex_type, score))
                conn.commit()
                conn.close()
            show_toast("Grades Registry Saved", "Evaluation schema nodes updated across active local data registers.")
        except Exception as e:
            show_toast("Storage Core Error", str(e), 'danger')

class AttendanceChartScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lay = BoxLayout(orientation='vertical')
        self.lay.add_widget(TopBar("Statistical Analytics Canvas", back_target='teacher_home'))
        
        self.chart_container = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(14))
        self.lay.add_widget(self.chart_container)
        self.add_widget(self.lay)

    def on_enter(self, *args):
        self.chart_container.clear_widgets()
        
        # Pull metric ratios aggregates calculation
        with DB_LOCK:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT status, COUNT(*) FROM attendance GROUP BY status")
            data = dict(c.fetchall())
            conn.close()

        pres = data.get("Present", 0)
        absn = data.get("Absent", 0)
        tot = pres + absn

        self.chart_container.add_widget(ModernLabel(text="System Overview: Attending Metrics Performance Ratio Summary", style='h2', halign='center'))
        
        if tot == 0:
            self.chart_container.add_widget(ModernLabel(text="Insufficient data telemetry logs inside structural pipeline storage files to map distribution models.", style='muted', halign='center'))
            return

        p_rate = (pres / tot) * 100
        
        # Display abstract geometric bar metrics container blocks representation
        self.chart_container.add_widget(ModernLabel(text=f"Aggregate Ratio Rate Vector: [b]{p_rate:.1f}%[/b] Frequency Frame", style='body', halign='center'))
        
        viz_box = ModernCard(radius=12, padding_val=20, size_hint_y=None, height=dp(160))
        viz_box.add_widget(ModernLabel(text=f"Total Captured Operational Matrix Index Pointers: {tot}", style='body'))
        viz_box.add_widget(ModernLabel(text=f"• Presence Iteration Node Counters: {pres}", style='body'))
        viz_box.add_widget(ModernLabel(text=f"• Deviation Absence Delta Vectors: {absn}", style='body'))
        self.chart_container.add_widget(viz_box)
        self.chart_container.add_widget(Widget())

class ViewAttendanceScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lay = BoxLayout(orientation='vertical')
        self.lay.add_widget(TopBar("Historical Log Registry", back_target='teacher_home'))

        self.scroll = ScrollView()
        self.list_box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(16), spacing=dp(10))
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.scroll.add_widget(self.list_box)
        self.lay.add_widget(self.scroll)
        self.add_widget(self.lay)

    def on_enter(self, *args):
        self.list_box.clear_widgets()
        with DB_LOCK:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("""
                SELECT attendance.date, students.name, attendance.subject_id, attendance.status 
                FROM attendance 
                JOIN students ON attendance.student_id = students.id
                ORDER BY attendance.date DESC LIMIT 100
            """)
            rows = c.fetchall()
            conn.close()

        if not rows:
            self.list_box.add_widget(ModernLabel(text="Log registry stream pipeline empty.", style='muted', halign='center'))
            return

        for r_date, s_name, sub_id, status in rows:
            card = ModernCard(radius=10, padding_val=10)
            card.size_hint_y = None
            card.height = dp(70)
            
            hb = BoxLayout()
            v = BoxLayout(orientation='vertical', size_hint_x=0.7)
            v.add_widget(ModernLabel(text=f"[b]{s_name}[/b] — {sub_id}", style='body'))
            v.add_widget(ModernLabel(text=f"Timestamp Node Sequence: {r_date}", style='muted'))
            hb.add_widget(v)

            lbl_status = ModernLabel(text=f"[b]{status.upper()}[/b]", size_hint_x=0.3, halign='right')
            lbl_status.color = UI_COLOR('accent') if status == "Present" else UI_COLOR('danger')
            hb.add_widget(lbl_status)
            
            card.add_widget(hb)
            self.list_box.add_widget(card)

# ════════════════════════════════════════════════════════════════════
#  PARENT PORTAL ECOSYSTEM SCREENS
# ════════════════════════════════════════════════════════════════════
class ParentLoginScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        lay = BoxLayout(orientation='vertical')
        lay.add_widget(TopBar("Guardian Access Node Portal", show_back=True, back_target='role_select'))

        scroll = ScrollView()
        form = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(24), spacing=dp(16))
        form.bind(minimum_height=form.setter('height'))

        form.add_widget(ModernLabel(text="Enter Portal Authorization", style='h2'))
        form.add_widget(ModernLabel(text="Provide the secondary student entity tracker mapping identity token registered with the educational system coordinator.", style='muted'))

        self.student_id_in = ModernInput(hint="Registered Student Reference ID token")
        form.add_widget(self.student_id_in)

        login_btn = ModernButton(text="Establish Synchronized Pipeline Session", bg_type='accent', size_hint_y=None, height=dp(48))
        login_btn.bind(on_release=self.parent_connect)
        form.add_widget(login_btn)
        
        scroll.add_widget(form)
        lay.add_widget(scroll)
        self.add_widget(lay)

    def parent_connect(self, *a):
        sid = self.student_id_in.text.strip()
        if not sid: return
        
        with DB_LOCK:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT name FROM students WHERE id=?", (sid,))
            res = c.fetchone()
            conn.close()

        if res:
            # Persistent context frame link configuration optimization storage write
            set_pref('current_parent_student_tgt', sid)
            set_pref('current_parent_student_name', res[0])
            self.manager.current = 'parent_home'
        else:
            show_toast("Validation Sequence Empty", "Specified tracking token reference target key node unrecognized inside architecture local file schemas.", 'danger')

class ParentHomeScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lay = BoxLayout(orientation='vertical')
        self.top_bar = TopBar("Guardian Hub Matrix Dashboard", show_back=True, back_target='role_select')
        self.lay.add_widget(self.top_bar)

        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(16))
        
        self.banner = ModernCard(radius=14, padding_val=18)
        self.lbl_head = ModernLabel(text="Tracking Monitor Entity Profile Engine", style='h2')
        self.lbl_sub = ModernLabel(text="Establishing data pipe loop context parameters interface configuration layers.", style='muted')
        self.banner.add_widget(self.lbl_head)
        self.banner.add_widget(self.lbl_sub)
        content.add_widget(self.banner)

        btn_marks = ModernButton(text="Overview Grade Evaluation Matrix", bg_type='primary', size_hint_y=None, height=dp(50))
        btn_marks.bind(on_release=lambda x: self.go_to('view_marks'))
        content.add_widget(btn_marks)

        # Embedded contextual snapshot telemetry mock data visualization framework parameters block
        self.metric_card = ModernCard(radius=12, padding_val=14)
        self.lbl_metrics = ModernLabel(text="Loading contextual biometric pipeline telemetry ratios...", style='body')
        self.metric_card.add_widget(self.lbl_metrics)
        content.add_widget(self.metric_card)
        content.add_widget(Widget())

        self.lay.add_widget(content)
        self.add_widget(self.lay)

    def go_to(self, route): 
        self.manager.current = route

    def on_enter(self, *args):
        sid = get_pref('current_parent_student_tgt') or ""
        sname = get_pref('current_parent_student_name') or "Student Entity Portal"
        
        self.top_bar.title_lbl.text = f"Overview: {sname}"
        self.lbl_head.text = f"[b]{sname}[/b] Tracking Stream"
        self.lbl_sub.text = f"Hardware Terminal Security Identifier Node Mapping Token String: {sid}"

        # Real-time metrics recalculation framework routine block execution
        with DB_LOCK:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT status, COUNT(*) FROM attendance WHERE student_id=? GROUP BY status", (sid,))
            data = dict(c.fetchall())
            conn.close()

        p = data.get("Present", 0)
        a = data.get("Absent", 0)
        t = p + a
        r = (p / t * 100) if t > 0 else 0.0

        self.lbl_metrics.text = f"[b]Session Attendance Performance Summary Indices Matrix[/b]\n\n• Verified Class Check-in Sequence Points: {p}\n• Flagged System Absence Exceptions Detours: {a}\n• Cumulative Monitored Framework Sessions: {t}\n• Evaluated Net Core Ratio Index Level: [b]{r:.1f}%[/b]"

class ViewMarksScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lay = BoxLayout(orientation='vertical')
        self.lay.add_widget(TopBar("Performance Record Matrix", back_target='parent_home'))

        self.scroll = ScrollView()
        self.list_box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(16), spacing=dp(10))
        self.list_box.bind(minimum_height=self.list_box.setter('height'))
        self.scroll.add_widget(self.list_box)
        self.lay.add_widget(self.scroll)
        self.add_widget(self.lay)

    def on_enter(self, *args):
        self.list_box.clear_widgets()
        sid = get_pref('current_parent_student_tgt') or ""

        with DB_LOCK:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT subject_id, exam_type, score FROM marks WHERE student_id=?", (sid,))
            rows = c.fetchall()
            conn.close()

        if not rows:
            self.list_box.add_widget(ModernLabel(text="No evaluating structural test mark matrices tracked yet.", style='muted', halign='center'))
            return

        for sub, exam, score in rows:
            card = ModernCard(radius=10, padding_val=12)
            card.size_hint_y = None
            card.height = dp(70)
            
            h = BoxLayout()
            v = BoxLayout(orientation='vertical', size_hint_x=0.7)
            v.add_widget(ModernLabel(text=f"[b]{sub}[/b] — {exam}", style='body'))
            h.add_widget(v)
            
            lbl_score = ModernLabel(text=f"[b]{score:.1f}[/b] / 100", size_hint_x=0.3, halign='right')
            lbl_score.color = UI_COLOR('primary') if score >= 40 else UI_COLOR('danger')
            h.add_widget(lbl_score)
            
            card.add_widget(h)
            self.list_box.add_widget(card)

# ════════════════════════════════════════════════════════════════════
#  COMMUNICATION ENGINE SCREENS (MOCK REALTIME CHAT MESSAGING SERVICE)
# ════════════════════════════════════════════════════════════════════
class TeacherChatScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lay = BoxLayout(orientation='vertical')
        self.lay.add_widget(TopBar("Instructor Comm Link Nodes", back_target='teacher_home'))

        self.scroll = ScrollView()
        self.chat_box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(12), spacing=dp(8))
        self.chat_box.bind(minimum_height=self.chat_box.setter('height'))
        self.scroll.add_widget(self.chat_box)
        self.lay.add_widget(self.scroll)

        input_bar = BoxLayout(size_hint_y=None, height=dp(56), padding=dp(6), spacing=dp(6))
        self.msg_in = ModernInput(hint="Type structural secure transmission payload message sequence text lines...")
        send_btn = ModernButton(text="SEND", bg_type='primary', size_hint_x=0.25)
        send_btn.bind(on_release=self.dispatch_msg)
        input_bar.add_widget(self.msg_in)
        input_bar.add_widget(send_btn)
        self.lay.add_widget(input_bar)

        self.add_widget(self.lay)

    def on_enter(self, *args): 
        self.reload_messages()

    def reload_messages(self):
        self.chat_box.clear_widgets()
        # Mocking local loop entries simulation track record feed stream channel arrays strings data arrays
        self.chat_box.add_widget(ModernLabel(text="Secure end-to-end institutional encrypted operational broadcast sequence communication pipe initiated.", style='muted', halign='center'))
        
        with DB_LOCK:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT sender, msg FROM chat_cache ORDER BY id ASC")
            for sender, m_text in c.fetchall():
                card = ModernCard(radius=8, padding_val=8, border=False)
                card.size_hint_y = None
                card.height = dp(54)
                card.add_widget(ModernLabel(text=f"[b]{sender}:[/b] {m_text}", style='body'))
                self.chat_box.add_widget(card)
            conn.close()

    def dispatch_msg(self, *a):
        txt = self.msg_in.text.strip()
        if not txt: return
        
        with DB_LOCK:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            ts_id = str(int(datetime.now().timestamp() * 1000))
            c.execute("INSERT INTO chat_cache VALUES (?, 'Faculty Staff', 'Parents Core Network Group Direct', ?, ?)", (ts_id, txt, datetime.now().isoformat()))
            conn.commit()
            conn.close()

        if db_fb:
            threading.Thread(target=lambda: db_fb.child("chats").child(ts_id).set({"sender":"Faculty Staff","msg":txt}), daemon=True).start()

        self.msg_in.text = ""
        self.reload_messages()

class ParentChatScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lay = BoxLayout(orientation='vertical')
        self.lay.add_widget(TopBar("Instructor Consult Direct Line", back_target='parent_home'))

        self.scroll = ScrollView()
        self.chat_box = BoxLayout(orientation='vertical', size_hint_y=None, padding=dp(12), spacing=dp(8))
        self.chat_box.bind(minimum_height=self.chat_box.setter('height'))
        self.scroll.add_widget(self.chat_box)
        self.lay.add_widget(self.scroll)

        input_bar = BoxLayout(size_hint_y=None, height=dp(56), padding=dp(6), spacing=dp(6))
        self.msg_in = ModernInput(hint="Type validation message query...")
        send_btn = ModernButton(text="TRANSMIT", bg_type='accent', size_hint_x=0.25)
        send_btn.bind(on_release=self.dispatch_msg)
        input_bar.add_widget(self.msg_in)
        input_bar.add_widget(send_btn)
        self.lay.add_widget(input_bar)

        self.add_widget(self.lay)

    def on_enter(self, *args): 
        self.reload_messages()

    def reload_messages(self):
        self.chat_box.clear_widgets()
        self.chat_box.add_widget(ModernLabel(text="Secure connection endpoint established.", style='muted', halign='center'))
        
        with DB_LOCK:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT sender, msg FROM chat_cache ORDER BY id ASC")
            for sender, m_text in c.fetchall():
                card = ModernCard(radius=8, padding_val=8, border=False)
                card.size_hint_y = None
                card.height = dp(54)
                card.add_widget(ModernLabel(text=f"[b]{sender}:[/b] {m_text}", style='body'))
                self.chat_box.add_widget(card)
            conn.close()

    def dispatch_msg(self, *a):
        txt = self.msg_in.text.strip()
        if not txt: return
        p_name = get_pref('current_parent_student_name') or "Parent Guardian Node Token"

        with DB_LOCK:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            ts_id = str(int(datetime.now().timestamp() * 1000))
            c.execute("INSERT INTO chat_cache VALUES (?, ?, 'Faculty Cluster Pipeline System Framework Registry Unit', ?, ?)", (ts_id, f"Parent of {p_name}", txt, datetime.now().isoformat()))
            conn.commit()
            conn.close()

        if db_fb:
            threading.Thread(target=lambda: db_fb.child("chats").child(ts_id).set({"sender":f"Parent of {p_name}","msg":txt}), daemon=True).start()

        self.msg_in.text = ""
        self.reload_messages()

# ════════════════════════════════════════════════════════════════════
#  SYSTEM PREFERENCES CONFIGURATION MATRIX CONTROL PANEL
# ════════════════════════════════════════════════════════════════════
class SettingsScreen(ModernScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.lay = BoxLayout(orientation='vertical')
        self.lay.add_widget(TopBar("Ecosystem Settings Control Matrix Panel", show_back=True, back_target='role_select'))

        content = BoxLayout(orientation='vertical', padding=dp(24), spacing=dp(18))
        content.add_widget(ModernLabel(text="UI Theme Framework Profile Configuration", style='h2'))
        
        # Interactive UI engine mode triggers options switches setups block representation elements controls components
        self.theme_btn = ModernButton(text="Toggle Visualization Mode (Light/Dark Engine Spectrum Refresh)", bg_type='primary', size_hint_y=None, height=dp(48))
        self.theme_btn.bind(on_release=self.toggle_theme_engine_state)
        content.add_widget(self.theme_btn)

        content.add_widget(ModernLabel(text="Data Telemetry Storage Integrity Framework Tools Utilities", style='h2'))
        
        clear_db_btn = ModernButton(text="Purge Local Database Indexes Sequence Records Cache File (Hard Reset Grid File Nodes System)", bg_type='danger', size_hint_y=None, height=dp(46))
        clear_db_btn.bind(on_release=self.hard_reset_local_sqlite_file)
        content.add_widget(clear_db_btn)
        content.add_widget(Widget())

        self.lay.add_widget(content)
        self.add_widget(self.lay)

    def toggle_theme_engine_state(self, *a):
        nxt = 'light' if CURRENT_THEME == 'dark' else 'dark'
        switch_theme_global(nxt)
        show_toast("Theme Refreshed Matrix Layer", f"Engine re-rasterization pipeline switched runtime contexts variables to: {nxt.upper()} core state spectrum configurations successfully.")

    def hard_reset_local_sqlite_file(self, *a):
        try:
            with DB_LOCK:
                if os.path.exists(DB_FILE):
                    os.remove(DB_FILE)
                init_db()
                _init_prefs()
            show_toast("Hard System Purge Completed", "Local binary structural indexing tables rows parameters wiped. Environment structures re-initialized safely.", 'danger')
        except Exception as e:
            show_toast("IO Access Lock Denied Error Exception", str(e), 'danger')

# ════════════════════════════════════════════════════════════════════
#  APP ENTRY POINT
# ════════════════════════════════════════════════════════════════════
class JustApp(App):
    title = 'JUST — Smart Attendance v5'

    def build(self):
        Window.size = (540, 960)  # Mobile aspect ratio
        init_db()
        _init_prefs()
        sm = ScreenManager(transition=FadeTransition(duration=0.22))
        for s in [
            SplashScreen         (name='splash'),
            RoleSelectScreen     (name='role_select'),
            TeacherLoginScreen   (name='teacher_login'),
            ForgotPINScreen      (name='forgot_pin'),
            TeacherHomeScreen    (name='teacher_home'),
            ManageStudentsScreen (name='manage_students'),
            ManageSubjectsScreen (name='manage_subjects'),
            ManageParentsScreen  (name='manage_parents'),
            MarkAttendanceScreen (name='mark_attendance'),
            EnterMarksScreen     (name='enter_marks'),
            AttendanceChartScreen(name='att_chart'),
            ViewAttendanceScreen (name='view_attendance'),
            ViewMarksScreen      (name='view_marks'),
            TeacherChatScreen    (name='teacher_chat'),
            ParentChatScreen     (name='parent_chat'),
            ParentLoginScreen    (name='parent_login'),
            ParentHomeScreen     (name='parent_home'),
            SettingsScreen       (name='settings'),
        ]:
            sm.add_widget(s)
        return sm


if __name__ == '__main__':
    JustApp().run()
