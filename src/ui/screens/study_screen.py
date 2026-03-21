"""Flashcard study screen with flip animation and quality rating."""
import asyncio
from dataclasses import dataclass
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.snackbar import Snackbar


@dataclass
class CardSession:
    word_id: int
    lemma: str
    stressed: str
    translation: str
    quality: int = -1  # -1 = not answered yet

    def is_answered(self) -> bool:
        return self.quality >= 0


class StudyScreen(MDScreen):
    current_card = None  # type: CardSession | None
    cards_remaining = NumericProperty(0)
    cards_done = NumericProperty(0)
    is_flipped = BooleanProperty(False)
    is_loading = BooleanProperty(True)
    russian_text = StringProperty("")
    translation_text = StringProperty("")
    session: list[CardSession] = None
    session_index = 0

    def on_enter(self):
        asyncio.create_task(self.load_session())

    async def load_session(self):
        """Load today's review session."""
        self.is_loading = True
        try:
            from src.data.user_progress import get_due_cards
            from src.data.vocabulary import get_word_by_id, get_word_detail

            due = await get_due_cards(limit=20)
            self.session = []
            for prog in due:
                word = await get_word_by_id(prog.word_id)
                if word:
                    detail = await get_word_detail(prog.word_id)
                    translation = detail.get_primary_translation() if detail else ""
                    self.session.append(CardSession(
                        word_id=word.id,
                        lemma=word.lemma,
                        stressed=word.lemma_stressed,
                        translation=translation or "",
                    ))

            self.session_index = 0
            self.cards_remaining = len(self.session)
            self.cards_done = 0

            if self.session:
                self.show_card(self.session[0])
            else:
                self.russian_text = "🎉"
                self.translation_text = "No cards due today!"
        except Exception as e:
            print(f"Study load error: {e}")
        finally:
            self.is_loading = False

    def show_card(self, card: CardSession):
        """Display a card."""
        self.current_card = card
        self.russian_text = card.stressed
        self.translation_text = card.translation
        self.is_flipped = False

    def flip_card(self):
        """Flip the current card to show answer."""
        if self.current_card and not self.is_flipped:
            self.is_flipped = True
            # Animate the flip
            card = self.ids.flashcard_card
            anim = Animation(duration=0.3)
            card.opacity = 0.5
            def complete(*args):
                card.opacity = 1
            Clock.schedule_once(complete, 0.15)

    def rate_card(self, quality: int):
        """Rate the current card (0-5)."""
        if not self.current_card:
            return

        self.current_card.quality = quality
        asyncio.create_task(self.save_review(quality))
        self.cards_done += 1
        self.next_card()

    async def save_review(self, quality: int):
        """Save the review result using SM-2."""
        try:
            from src.data.user_progress import (
                get_progress_for_word,
                apply_sm2,
                save_progress,
                update_streak,
            )

            progress = await get_progress_for_word(self.current_card.word_id)
            if progress is None:
                from src.data.user_progress import UserProgress
                progress = UserProgress(word_id=self.current_card.word_id)

            progress = apply_sm2(quality, progress)
            await save_progress(progress)
            await update_streak()
        except Exception as e:
            print(f"Error saving review: {e}")

    def next_card(self):
        """Move to the next card in session."""
        self.session_index += 1
        if self.session_index < len(self.session):
            self.show_card(self.session[self.session])
            self.cards_remaining = len(self.session) - self.session_index
        else:
            self.finish_session()

    def finish_session(self):
        """Session complete."""
        Snackbar(text=f"Session complete! {self.cards_done} cards reviewed.").open()
        self.manager.current = "home"

    def play_audio(self):
        """Play TTS audio for current word."""
        if not self.current_card:
            return
        asyncio.create_task(self._play_audio_async(self.current_card.stressed))

    async def _play_audio_async(self, text: str):
        try:
            from src.core.audio_service import AudioService
            path = await AudioService.generate_audio(text)
            if path:
                from kivy.core.audio import SoundLoader
                sound = SoundLoader.load(str(path))
                if sound:
                    sound.play()
        except Exception as e:
            print(f"Audio error: {e}")
