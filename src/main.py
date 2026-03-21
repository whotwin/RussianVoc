"""Main KivyMD App entry point."""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.screenmanager import ScreenManager
from kivymd.uix.navigationdrawer import NavigationDrawer
from kivymd.uix.bottomnavigation import MDBottomNavigation
from kivymd.uix.bottomnavigation import BNBottomItem, BNLabel, BNTab
from kivymd.theming import ThemeManager

from src.config import config
from src.data.db import init_db_sync


class RussianFlashcardsApp(MDApp):
    theme_cls = ThemeManager()
    nav_drawer = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.theme_style = "Light" if config.theme == "light" else "Dark"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Orange"

    def build(self):
        """Build the application."""
        # Initialize database
        init_db_sync()

        # Setup screen manager
        sm = ScreenManager()

        # Import screens lazily to avoid import errors on desktop
        from src.ui.screens.home_screen import HomeScreen
        from src.ui.screens.study_screen import StudyScreen
        from src.ui.screens.dictionary_screen import DictionaryScreen
        from src.ui.screens.word_detail_screen import WordDetailScreen
        from src.ui.screens.plan_screen import PlanScreen
        from src.ui.screens.progress_screen import ProgressScreen

        # Add screens
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(StudyScreen(name="study"))
        sm.add_widget(DictionaryScreen(name="dictionary"))
        sm.add_widget(WordDetailScreen(name="word_detail"))
        sm.add_widget(PlanScreen(name="plan"))
        sm.add_widget(ProgressScreen(name="progress"))

        # Build navigation
        root = self.build_navigation(sm)
        return root

    def build_navigation(self, sm: ScreenManager):
        """Build bottom navigation bar."""
        from kivymd.uix.bottomnavigation import MDBottomNavigationBar, MDBottomNavigationItem

        # Use bottom navigation for mobile-friendly navigation
        bottom_nav = MDBottomNavigation()

        items = [
            ("home", "Home", "home-circle"),
            ("study", "Study", "book-open-variant"),
            ("dictionary", "Dictionary", "book-search"),
            ("plan", "Plan", "chart-bar"),
            ("progress", "Progress", "chart-line"),
        ]

        for screen_name, label, icon in items:
            item = MDBottomNavigationItem(
                name=screen_name,
                text=label,
                icon=icon,
            )
            item.add_widget(sm.get_screen(screen_name))
            bottom_nav.add_widget(item)

        return bottom_nav

    def on_start(self):
        """Called when app starts."""
        # Start notification scheduler
        try:
            from src.services.notification_service import start_scheduler
            start_scheduler()
        except Exception as e:
            print(f"Notification scheduler start failed: {e}")

    def on_pause(self):
        """Called when app is paused."""
        return True

    def on_resume(self):
        """Called when app resumes."""
        pass

    def toggle_theme(self):
        """Toggle between light and dark theme."""
        if self.theme_cls.theme_style == "Light":
            self.theme_cls.theme_style = "Dark"
            config.theme = "dark"
        else:
            self.theme_cls.theme_style = "Light"
            config.theme = "light"
        config.save()


if __name__ == "__main__":
    RussianFlashcardsApp().run()
