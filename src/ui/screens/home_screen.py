"""Home screen showing today's review and streak."""
import asyncio
from datetime import date
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivymd.uix.screen import MDScreen


class HomeScreen(MDScreen):
    due_count = NumericProperty(0)
    current_streak = NumericProperty(0)
    longest_streak = NumericProperty(0)
    today_reviewed = NumericProperty(0)
    daily_goal = NumericProperty(20)
    progress_percent = NumericProperty(0)
    is_loading = BooleanProperty(True)

    def on_enter(self):
        asyncio.create_task(self.load_data())

    async def load_data(self):
        self.is_loading = True
        try:
            from src.data.user_progress import get_due_cards, get_streak
            from src.data.db import get_db
            from src.config import config

            due = await get_due_cards(limit=100)
            self.due_count = len(due)

            streak, longest, _ = await get_streak()
            self.current_streak = streak
            self.longest_streak = longest

            self.daily_goal = config.daily_goal

            # Actual reviews done today
            today = date.today().isoformat()
            async with get_db() as db:
                async with db.execute(
                    "SELECT COUNT(*) as cnt FROM review_history WHERE date(reviewed_at) = ?",
                    (today,),
                ) as cursor:
                    row = await cursor.fetchone()
                    self.today_reviewed = row["cnt"] if row else 0

            self.progress_percent = min(100, int((self.today_reviewed / max(1, self.daily_goal)) * 100))
        except Exception as e:
            print(f"Error loading home data: {e}")
        finally:
            self.is_loading = False

    def go_to_study(self):
        self.app.switch_tab("study")

    def go_to_dictionary(self):
        self.app.switch_tab("dictionary")

    def go_to_plan(self):
        self.app.switch_tab("plan")

    def go_to_progress(self):
        self.app.switch_tab("progress")

    def start_study(self):
        if self.due_count > 0:
            self.go_to_study()
        else:
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text="No cards due! Add words from the dictionary.").open()
