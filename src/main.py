"""Main KivyMD App entry point."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivymd.app import MDApp
from kivymd.uix.screenmanager import ScreenManager
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.theming import ThemeManager
from kivy.lang import Builder

from src.config import config
from src.data.db import init_db_sync


# Load all KV files
KV_FILES = [
    "src/ui/screens/home.kv",
    "src/ui/screens/study.kv",
    "src/ui/screens/dictionary.kv",
    "src/ui/screens/word_detail.kv",
    "src/ui/screens/plan.kv",
    "src/ui/screens/progress.kv",
]
for kv in KV_FILES:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", kv)
    if os.path.exists(path):
        Builder.load_file(path)


class RussianFlashcardsApp(MDApp):
    theme_cls = ThemeManager()
    bottom_nav = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = "Light" if config.theme == "light" else "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Orange"

    def build(self):
        init_db_sync()

        from src.ui.screens.home_screen import HomeScreen
        from src.ui.screens.study_screen import StudyScreen
        from src.ui.screens.dictionary_screen import DictionaryScreen
        from src.ui.screens.word_detail_screen import WordDetailScreen
        from src.ui.screens.plan_screen import PlanScreen
        from src.ui.screens.progress_screen import ProgressScreen

        self.bottom_nav = MDBottomNavigation()

        items = [
            ("home", "Home", "home-circle"),
            ("study", "Study", "book-open-variant"),
            ("dictionary", "Dictionary", "book-search"),
            ("plan", "Plan", "chart-bar"),
            ("progress", "Progress", "chart-line"),
        ]

        for screen_name, label, icon in items:
            item = MDBottomNavigationItem(name=screen_name, text=label, icon=icon)
            self.bottom_nav.add_widget(item)

        # Add screens to their nav items by name
        self.bottom_nav.get_screen("home").add_widget(HomeScreen(name="home"))
        self.bottom_nav.get_screen("study").add_widget(StudyScreen(name="study"))
        self.bottom_nav.get_screen("dictionary").add_widget(DictionaryScreen(name="dictionary"))
        self.bottom_nav.get_screen("plan").add_widget(PlanScreen(name="plan"))
        self.bottom_nav.get_screen("progress").add_widget(ProgressScreen(name="progress"))

        # WordDetailScreen in its own nav item
        wd_item = MDBottomNavigationItem(name="word_detail", text="Detail", icon="book")
        wd_item.add_widget(WordDetailScreen(name="word_detail"))
        self.bottom_nav.add_widget(wd_item)

        return self.bottom_nav

    def switch_tab(self, tab_name: str):
        """Switch to a tab by name."""
        if self.bottom_nav:
            self.bottom_nav.switch_tab(tab_name)

    def on_start(self):
        try:
            from src.services.notification_service import start_scheduler
            start_scheduler()
        except Exception as e:
            print(f"Notification scheduler start failed: {e}")

    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def toggle_theme(self):
        if self.theme_cls.theme_style == "Light":
            self.theme_cls.theme_style = "Dark"
            config.theme = "dark"
        else:
            self.theme_cls.theme_style = "Light"
            config.theme = "light"
        config.save()
