"""Progress statistics screen."""
import asyncio
from kivy.properties import NumericProperty, ListProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem
from kivymd.uix.progressbar import MDProgressBar


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
        self.is_loading = True
        try:
            from src.data.user_progress import get_streak, get_review_stats
            from src.data.db import get_db

            streak, longest, _ = await get_streak()
            self.current_streak = streak
            self.longest_streak = longest

            weekly = await get_review_stats(7)
            self.weekly_stats = weekly

            monthly = await get_review_stats(30)
            self.monthly_stats = monthly

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

            self._populate_weekly()
        except Exception as e:
            print(f"Stats load error: {e}")
        finally:
            self.is_loading = False

    def _populate_weekly(self):
        lst = self.ids.get("weekly_list")
        if not lst:
            return
        lst.clear_widgets()
        if not self.weekly_stats:
            lst.add_widget(OneLineListItem(text="No reviews this week yet"))
            return
        for stat in self.weekly_stats:
            date_str = stat.get("review_date", "")
            total = stat.get("total", 0)
            correct = stat.get("correct", 0)
            pct = int(correct / total * 100) if total > 0 else 0
            lst.add_widget(
                TwoLineListItem(
                    text=date_str,
                    secondary_text=f"{total} reviewed — {pct}% correct",
                )
            )
