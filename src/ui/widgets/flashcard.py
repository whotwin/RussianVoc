"""Flashcard widget with flip animation."""
from kivy.properties import StringProperty, BooleanProperty
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDIconButton


class FlashCard(MDCard):
    front_text = StringProperty("")
    back_text = StringProperty("")
    is_flipped = BooleanProperty(False)
    show_answer = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elevation = 4
        self.radius = [16, 16, 16, 16]

    def flip(self):
        """Flip the card with animation."""
        if self.is_flipped:
            return

        self.is_flipped = True
        anim = Animation(
            pos_hint={"center_x": 0.5, "center_y": 0.5},
            duration=0.15,
        )
        anim &= Animation(opacity=0, duration=0.15)
        anim.start(self)

        def on_complete(*args):
            self.show_answer = True
            anim2 = Animation(opacity=1, duration=0.15)
            anim2.start(self)

        self.schedule_once(on_complete, 0.15)

    def reset(self):
        """Reset card to front."""
        self.is_flipped = False
        self.show_answer = False
        self.opacity = 1
