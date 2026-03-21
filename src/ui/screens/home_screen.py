"""Home screen showing today's review and streak."""
import asyncio
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.chip import MDChip
from kivymd.uix.circularprogressbar import MDCircularProgressBar


class HomeScreen(MDScreen):
    due_count = NumericProperty(0)
    current_streak = NumericProperty(0)
    longest_streak = NumericProperty(0)
    today_reviewed = NumericProperty(0)
    daily_goal = NumericProperty(20)
    progress_percent = NumericProperty(0)
    is_loading = BooleanProperty(True)

    def on_enter(self):
        """Load data when screen is entered."""
        asyncio.create_task(self.load_data())

    async def load_data(self):
        """Load home screen data."""
        self.is_loading = True
        try:
            from src.data.user_progress import get_due_cards, get_streak

            due = await get_due_cards(limit=100)
            self.due_count = len(due)

            streak, longest, _ = await get_streak()
            self.current_streak = streak
            self.longest_streak = longest

            # Load config
            from src.config import config
            self.daily_goal = config.daily_goal

            # Calculate today's progress
            self.today_reviewed = min(self.due_count, self.daily_goal)
            self.progress_percent = min(100, int((self.today_reviewed / self.daily_goal) * 100))

        except Exception as e:
            print(f"Error loading home data: {e}")
        finally:
            self.is_loading = False

    def go_to_study(self):
        """Navigate to study screen."""
        self.manager.current = "study"

    def go_to_dictionary(self):
        """Navigate to dictionary screen."""
        self.manager.current = "dictionary"

    def go_to_plan(self):
        """Navigate to plan screen."""
        self.manager.current = "plan"

    def go_to_progress(self):
        """Navigate to progress screen."""
        self.manager.current = "progress"

    def start_study(self):
        """Start a study session."""
        if self.due_count > 0:
            self.go_to_study()
        else:
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text="No cards due today! Great job!").open()
