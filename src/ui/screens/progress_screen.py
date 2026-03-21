"""Progress statistics screen."""
import asyncio
from kivy.properties import NumericProperty, ListProperty, BooleanProperty, StringProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.chip import MDChip


class ProgressScreen(MDScreen):
    current_streak = NumericProperty(0)
    longest_streak = NumericProperty(0)
    total_reviewed = NumericProperty(0)
    accuracy = NumericProperty(0)
    weekly_stats = ListProperty([])
    monthly_stats = ListProperty([])
    is_loading = BooleanProperty(True)

    def on_enter(self):
        asyncio.create_task(self.load_stats())

    async def load_stats(self):
        """Load progress statistics."""
        self.is_loading = True
        try:
            from src.data.user_progress import get_streak, get_review_stats
            from src.data.db import get_db

            # Streak
            streak, longest, _ = await get_streak()
            self.current_streak = streak
            self.longest_streak = longest

            # Weekly stats
            weekly = await get_review_stats(7)
            self.weekly_stats = weekly

            # Monthly stats
            monthly = await get_review_stats(30)
            self.monthly_stats = monthly

            # Total and accuracy
            async with get_db() as db:
                async with db.execute(
                    """SELECT COUNT(*) as total,
                              SUM(CASE WHEN quality >= 3 THEN 1 ELSE 0 END) as correct
                       FROM review_history"""
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        self.total_reviewed = row["total"] or 0
                        correct = row["correct"] or 0
                        if self.total_reviewed > 0:
                            self.accuracy = int((correct / self.total_reviewed) * 100)

        except Exception as e:
            print(f"Stats load error: {e}")
        finally:
            self.is_loading = False
