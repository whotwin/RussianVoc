"""CEFR plan selection screen."""
import asyncio
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.chip import MDChip
from kivymd.uix.snackbar import Snackbar


class PlanScreen(MDScreen):
    level_cards = ListProperty([])
    is_loading = BooleanProperty(True)

    def on_enter(self):
        asyncio.create_task(self.load_plans())

    async def load_plans(self):
        """Load CEFR plan information."""
        self.is_loading = True
        try:
            from src.data.vocabulary import get_word_count_by_level
            from src.core.cefr_levelizer import CEFR_DESCRIPTIONS

            cards = []
            for level in ["A1", "A2", "B1", "B2"]:
                info = CEFR_DESCRIPTIONS.get(level, {})
                count = await get_word_count_by_level(level)
                cards.append({
                    "level": level,
                    "name": info.get("name", level),
                    "name_ru": info.get("name_ru", ""),
                    "description": info.get("description", ""),
                    "description_ru": info.get("description_ru", ""),
                    "word_count": count,
                    "color": info.get("color", "#607D8B"),
                    "estimated_weeks": info.get("estimated_weeks", 0),
                })
            self.level_cards = cards
        except Exception as e:
            print(f"Plan load error: {e}")
        finally:
            self.is_loading = False

    def select_plan(self, level: str):
        """Select a CEFR level plan."""
        asyncio.create_task(self.activate_plan(level))

    async def activate_plan(self, level: str):
        """Activate a study plan."""
        try:
            from src.config import config
            from src.data.db import get_db

            config.active_plan = level
            config.save()

            # Initialize plan in database
            async with get_db() as db:
                await db.execute(
                    """INSERT OR REPLACE INTO study_plans (cefr_level, started_at)
                       VALUES (?, CURRENT_TIMESTAMP)
                       ON CONFLICT(cefr_level) DO UPDATE SET started_at = CURRENT_TIMESTAMP""",
                    (level,),
                )
                await db.commit()

            Snackbar(text=f"Plan '{level}' activated!").open()
            self.manager.current = "home"
        except Exception as e:
            Snackbar(text=f"Error: {e}").open()

    def refresh_data(self):
        """Refresh data from openrussian-data."""
        asyncio.create_task(self._refresh_data())

    async def _refresh_data(self):
        try:
            from src.services.data_importer import seed_sample_data
            count = await seed_sample_data()
            Snackbar(text=f"Loaded {count} sample words").open()
            await self.load_plans()
        except Exception as e:
            Snackbar(text=f"Import error: {e}").open()
