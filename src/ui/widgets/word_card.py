"""Word card widget for dictionary list."""
from kivy.properties import StringProperty
from kivymd.uix.list import OneLineAvatarListItem, ILeftBody
from kivymd.uix.chip import MDChip
from kivymd.uix.label import MDLabel


class WordListItem(OneLineAvatarListItem):
    lemma = StringProperty("")
    stressed = StringProperty("")
    pos = StringProperty("")
    cefr = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = self.stressed


class POSLabel(MDChip):
    """Part of speech chip."""

    def __init__(self, pos: str = "", **kwargs):
        super().__init__(**kwargs)
        self.text = pos
        self.mode = "outlined"
        self.height = "24dp"
        self.font_size = "10sp"


class CEFRLabel(MDChip):
    """CEFR level chip."""

    def __init__(self, level: str = "", **kwargs):
        super().__init__(**kwargs)
        self.text = level
        self.mode = "flat"
        self.height = "24dp"
        self.font_size = "10sp"
        colors = {
            "A1": "#4CAF50",
            "A2": "#8BC34A",
            "B1": "#FF9800",
            "B2": "#F44336",
        }
        if level in colors:
            self.md_bg_color = colors[level]
            self.text_color = [1, 1, 1, 1]
