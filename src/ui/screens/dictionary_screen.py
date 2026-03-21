"""Dictionary search screen."""
import asyncio
from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.searchbar import MDSearchBar
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.chip import MDChip
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.snackbar import Snackbar


class DictionaryScreen(MDScreen):
    search_query = StringProperty("")
    search_results = ListProperty([])
    is_searching = BooleanProperty(False)
    selected_level = StringProperty("")

    def on_enter(self):
        """Load initial dictionary view."""
        asyncio.create_task(self.load_all_words())

    async def load_all_words(self):
        """Load all words for initial display."""
        self.is_searching = True
        try:
            from src.data.vocabulary import get_words_by_level, search_words

            if self.selected_level:
                words = await get_words_by_level(self.selected_level, limit=50)
            else:
                words = await get_words_by_level("A1", limit=50)
                words_a2 = await get_words_by_level("A2", limit=30)
                words.extend(words_a2)

            self.search_results = [
                {
                    "id": w.id,
                    "lemma": w.lemma,
                    "stressed": w.lemma_stressed,
                    "pos": w.pos,
                    "cefr": w.cefr_level,
                }
                for w in words
            ]
        except Exception as e:
            print(f"Dictionary load error: {e}")
        finally:
            self.is_searching = False

    async def do_search(self, query: str):
        """Search for words."""
        if not query or len(query) < 1:
            await self.load_all_words()
            return

        self.search_query = query
        self.is_searching = True
        try:
            from src.data.vocabulary import search_words

            words = await search_words(
                query, limit=30, cefr_level=self.selected_level if self.selected_level else None
            )
            self.search_results = [
                {
                    "id": w.id,
                    "lemma": w.lemma,
                    "stressed": w.lemma_stressed,
                    "pos": w.pos,
                    "cefr": w.cefr_level,
                }
                for w in words
            ]
        except Exception as e:
            print(f"Search error: {e}")
        finally:
            self.is_searching = False

    def on_search(self, query: str):
        """Handle search input."""
        asyncio.create_task(self.do_search(query))

    def select_level(self, level: str):
        """Filter by CEFR level."""
        if self.selected_level == level:
            self.selected_level = ""
        else:
            self.selected_level = level
        asyncio.create_task(self.load_all_words())

    def show_word_detail(self, word_id: int):
        """Show detailed word view."""
        self.manager.get_screen("word_detail").load_word(word_id)
        self.manager.current = "word_detail"
