"""Word detail screen showing full word info."""
import asyncio
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.table import MDTable, MDTableCell
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.snackbar import Snackbar


class WordDetailScreen(MDScreen):
    lemma = StringProperty("")
    stressed = StringProperty("")
    pos = StringProperty("")
    cefr = StringProperty("")
    translations = ListProperty([])
    examples = ListProperty([])
    declensions = ListProperty([])
    conjugations = ListProperty([])
    is_loading = BooleanProperty(True)
    current_word_id = 0

    async def load_word(self, word_id: int):
        """Load word details."""
        self.current_word_id = word_id
        self.is_loading = True
        try:
            from src.data.vocabulary import get_word_detail

            detail = await get_word_detail(word_id)
            if detail:
                self.lemma = detail.word.lemma
                self.stressed = detail.word.lemma_stressed
                self.pos = detail.word.pos
                self.cefr = detail.word.cefr_level
                self.translations = [t.translation for t in detail.translations]
                self.examples = [(e.russian_stressed, e.english) for e in detail.examples]
                self.declensions = [
                    {
                        "case": d.case_name,
                        "number": d.number,
                        "form": d.form_stressed,
                    }
                    for d in detail.declensions
                ]
                self.conjugations = [
                    {
                        "tense": c.tense,
                        "person": c.person,
                        "number": c.number,
                        "form": c.form_stressed,
                    }
                    for c in detail.conjugations
                ]
        except Exception as e:
            print(f"Word detail error: {e}")
        finally:
            self.is_loading = False

    def play_audio(self):
        """Play TTS audio for word."""
        asyncio.create_task(self._play_audio())

    async def _play_audio(self):
        try:
            from src.core.audio_service import AudioService
            path = await AudioService.generate_audio(self.stressed)
            if path:
                from kivy.core.audio import SoundLoader
                sound = SoundLoader.load(str(path))
                if sound:
                    sound.play()
            else:
                Snackbar(text="Audio not available").open()
        except Exception as e:
            Snackbar(text=f"Audio error: {e}").open()

    def add_to_study(self):
        """Add word to study plan."""
        asyncio.create_task(self._add_to_study())

    async def _add_to_study(self):
        try:
            from src.data.user_progress import UserProgress, save_progress

            progress = UserProgress(word_id=self.current_word_id)
            await save_progress(progress)
            Snackbar(text=f"'{self.lemma}' added to your study plan").open()
        except Exception as e:
            Snackbar(text=f"Error: {e}").open()
