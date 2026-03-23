"""Dictionary search screen."""
import asyncio
from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.chip import MDChip
from kivymd.uix.snackbar import Snackbar
from kivy.uix.textinput import TextInput


class DictionaryScreen(MDScreen):
    search_query = StringProperty("")
    search_results = ListProperty([])
    is_searching = BooleanProperty(False)
    selected_level = StringProperty("")

    def on_enter(self):
        asyncio.create_task(self.load_all_words())

    def on_kv_post(self, base_widget):
        """Called after KV rules are applied."""
        self.results_list = self.ids.get("results_list")
        super().on_kv_post(base_widget)

    async def load_all_words(self):
        self.is_searching = True
        try:
            from src.data.schedule import get_words_by_level

            if self.selected_level:
                words = await get_words_by_level(self.selected_level, limit=50)
            else:
                words_a1 = await get_words_by_level("A1", limit=30)
                words_a2 = await get_words_by_level("A2", limit=20)
                words = words_a1 + words_a2

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
            self._update_list()
        except Exception as e:
            print(f"Dictionary load error: {e}")
        finally:
            self.is_searching = False

    async def do_search(self, query: str):
        if not query or len(query) < 2:
            await self.load_all_words()
            return

        self.search_query = query
        self.is_searching = True
        try:
            from src.data.schedule import search_words

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
            self._update_list()
        except Exception as e:
            print(f"Search error: {e}")
        finally:
            self.is_searching = False

    def on_search(self, query: str):
        asyncio.create_task(self.do_search(query))

    def select_level(self, level: str):
        if self.selected_level == level:
            self.selected_level = ""
        else:
            self.selected_level = level
        asyncio.create_task(self.load_all_words())

    def show_word_detail(self, word_id: int):
        self.app.switch_tab("word_detail")
        self.app.bottom_nav.ids.tab_manager.get_screen("word_detail").load_word(word_id)

    def _update_list(self):
        """Populate the MDList with search results."""
        lst = self.ids.get("results_list")
        if not lst:
            return
        lst.clear_widgets()
        for item in self.search_results:
            btn = OneLineListItem(
                text=f"{item['stressed']} — {item.get('pos', '')}",
                secondary_text=f"[{item['cefr']}]",
                on_release=lambda x, wid=item["id"]: self.show_word_detail(wid),
            )
            lst.add_widget(btn)
        if not self.search_results:
            lst.add_widget(
                OneLineListItem(text="No words found. Try a different search.")
            )
