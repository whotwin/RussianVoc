"""Progress bar widget."""
from kivy.properties import NumericProperty, StringProperty
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.label import MDLabel


class StudyProgressBar(MDProgressBar):
    goal = NumericProperty(20)
    current = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max = 100
        self.value = 0

    def set_progress(self, current: int, goal: int):
        """Update progress bar."""
        self.goal = goal
        self.current = current
        if goal > 0:
            self.value = min(100, int((current / goal) * 100))
        else:
            self.value = 0
