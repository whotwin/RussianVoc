"""CEFR plan selection screen."""
import asyncio
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.snackbar import Snackbar


LEVEL_COLORS = {
    "A1": (0.298, 0.686, 0.314, 1),
    "A2": (0.545, 0.765, 0.290, 1),
    "B1": (1.0, 0.596, 0.0, 1),
    "B2": (0.957, 0.263, 0.212, 1),
}


class PlanScreen(MDScreen):
    level_cards = ListProperty([])
    is_loading = BooleanProperty(True)

    def on_enter(self):
        asyncio.create_task(self.load_plans())

    async def load_plans(self):
        self.is_loading = True
        try:
            from src.data.schedule import get_word_count_by_level
            from src.core.cefr_levelizer import CEFR_DESCRIPTIONS

            cards = []
            for level in ["A1", "A2", "B1", "B2"]:
                info = CEFR_DESCRIPTIONS.get(level, {})
                count = await get_word_count_by_level(level)
                cards.append({
                    "level": level,
                    "name": f"{level} — {info.get('name', '')}",
                    "name_ru": info.get("name_ru", ""),
                    "description": info.get("description_ru") or info.get("description", ""),
                    "word_count": count,
                    "color": LEVEL_COLORS.get(level, (0.5, 0.5, 0.5, 1)),
                    "estimated_weeks": info.get("estimated_weeks", 0),
                })
            self.level_cards = cards
            self._populate_list()
        except Exception as e:
            print(f"Plan load error: {e}")
        finally:
            self.is_loading = False

    def _populate_list(self):
        lst = self.ids.get("plan_list")
        if not lst:
            return
        lst.clear_widgets()
        for card in self.level_cards:
            level_card = MDCard(
                size_hint_y=None,
                height="180dp",
                radius="12dp",
                padding="16dp",
                md_bg_color=card["color"],
                on_touch_up=lambda x, y, lvl=card["level"]: self.select_plan(lvl),
            )
            content = MDBoxLayout(orientation="vertical", spacing="4dp")
            content.add_widget(MDLabel(
                text=card["name"],
                font_style="H5",
                bold=True,
                color=(1, 1, 1, 1),
            ))
            content.add_widget(MDLabel(
                text=card["name_ru"],
                font_style="Subtitle2",
                color=(1, 1, 1, 0.8),
            ))
            content.add_widget(MDLabel(
                text=f"{card['word_count']} words",
                font_style="Body2",
                color=(1, 1, 1, 0.9),
            ))
            content.add_widget(MDLabel(
                text=f"~{card['estimated_weeks']} weeks",
                font_style="Caption",
                color=(1, 1, 1, 0.7),
            ))
            level_card.add_widget(content)
            lst.add_widget(level_card)

    def select_plan(self, level: str):
        asyncio.create_task(self.activate_plan(level))

    async def activate_plan(self, level: str):
        try:
            from src.config import config
            from src.data.db import get_db

            config.active_plan = level
            config.save()

            async with get_db() as db:
                await db.execute(
                    """INSERT OR REPLACE INTO study_plans (cefr_level, started_at)
                       VALUES (?, CURRENT_TIMESTAMP)
                       ON CONFLICT(cefr_level) DO UPDATE SET started_at = CURRENT_TIMESTAMP""",
                    (level,),
                )
                await db.commit()

            Snackbar(text=f"Plan '{level}' activated!").open()
            self.app.switch_tab("home")
        except Exception as e:
            Snackbar(text=f"Error: {e}").open()

    def refresh_data(self):
        asyncio.create_task(self._refresh_data())

    async def _refresh_data(self):
        try:
            from src.services.data_importer import seed_sample_data
            count = await seed_sample_data()
            Snackbar(text=f"Loaded {count} words").open()
            await self.load_plans()
        except Exception as e:
            Snackbar(text=f"Import error: {e}").open()
