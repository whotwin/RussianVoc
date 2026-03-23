"""Word detail screen showing full word info."""
import asyncio
from kivy.properties import StringProperty, ListProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.tab import MDTabs
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem
from kivymd.uix.chip import MDChip
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.label import MDLabel
from kivymd.uix.scrollview import MDScrollView


CASE_SHORT_NAMES = {
    "nomn": "Им",
    "gent": "Род",
    "datv": "Дат",
    "accs": "Вин",
    "ablt": "Твор",
    "loct": "Пред",
}


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
        self.current_word_id = word_id
        self.is_loading = True
        try:
            from src.data.schedule import get_word_detail

            detail = await get_word_detail(word_id)
            if detail:
                self.lemma = detail.word.lemma
                self.stressed = detail.word.lemma_stressed
                self.pos = detail.word.pos
                self.cefr = detail.word.cefr_level
                self.translations = [t.translation for t in detail.translations]
                self.examples = [(e.russian_stressed, e.english) for e in detail.examples]
                self.declensions = [
                    {"case": d.case_name, "number": d.number, "form": d.form_stressed}
                    for d in detail.declensions
                ]
                self.conjugations = [
                    {"tense": c.tense, "person": c.person, "number": c.number, "form": c.form_stressed}
                    for c in detail.conjugations
                ]
                self._populate_lists()
        except Exception as e:
            print(f"Word detail error: {e}")
        finally:
            self.is_loading = False

    def _populate_lists(self):
        """Populate tab lists."""
        # Translations
        translations_list = self.ids.get("translations_list")
        if translations_list:
            translations_list.clear_widgets()
            for t in self.translations:
                translations_list.add_widget(
                    OneLineListItem(text=t)
                )
            if not self.translations:
                translations_list.add_widget(
                    OneLineListItem(text="No translations available")
                )

        # Forms (declensions + conjugations)
        forms_list = self.ids.get("forms_list")
        if forms_list:
            forms_list.clear_widgets()
            if self.declensions:
                forms_list.add_widget(MDLabel(
                    text="[b]Declension[/b]", markup=True,
                    size_hint_y=None, height="32dp"
                ))
                # Group by case
                cases = {}
                for d in self.declensions:
                    case = CASE_SHORT_NAMES.get(d["case"], d["case"])
                    if case not in cases:
                        cases[case] = {}
                    cases[case][d["number"]] = d["form"]

                for case, numbers in cases.items():
                    sing = numbers.get("singular") or numbers.get("sing") or "—"
                    plur = numbers.get("plural") or numbers.get("plur") or "—"
                    forms_list.add_widget(
                        TwoLineListItem(text=case, secondary_text=f"Sg: {sing} | Pl: {plur}")
                    )

            if self.conjugations:
                forms_list.add_widget(MDLabel(
                    text="[b]Conjugation[/b]", markup=True,
                    size_hint_y=None, height="32dp"
                ))
                # Group by tense
                tenses = {}
                for c in self.conjugations:
                    tense_key = c["tense"]
                    if tense_key not in tenses:
                        tenses[tense_key] = []
                    tenses[tense_key].append(c)

                tense_names = {"pres": "Present", "past": "Past", "futr": "Future"}
                person_names = {"1per": "1st", "2per": "2nd", "3per": "3rd"}
                number_names = {"sing": "Sg", "plur": "Pl"}

                for tense, forms in tenses.items():
                    tname = tense_names.get(tense, tense)
                    forms_list.add_widget(MDLabel(
                        text=f"[b]{tname}[/b]", markup=True,
                        size_hint_y=None, height="24dp"
                    ))
                    for f in forms:
                        pname = person_names.get(f["person"], f["person"])
                        nname = number_names.get(f["number"], f["number"])
                        forms_list.add_widget(
                            OneLineListItem(
                                text=f"{pname} {nname}: {f['form']}",
                                size_hint_y=None, height="36dp"
                            )
                        )

            if not self.declensions and not self.conjugations:
                forms_list.add_widget(
                    OneLineListItem(text="No forms available for this word type")
                )

        # Examples
        examples_list = self.ids.get("examples_list")
        if examples_list:
            examples_list.clear_widgets()
            for ru, en in self.examples:
                examples_list.add_widget(
                    TwoLineListItem(text=ru, secondary_text=en)
                )
            if not self.examples:
                examples_list.add_widget(
                    OneLineListItem(text="No examples available")
                )

    def play_audio(self):
        if not self.stressed:
            return
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

    def go_back(self):
        """Return to the dictionary screen."""
        self.app.switch_tab("dictionary")
        asyncio.create_task(self._add_to_study())

    async def _add_to_study(self):
        try:
            from src.data.user_progress import UserProgress, save_progress

            progress = UserProgress(word_id=self.current_word_id)
            await save_progress(progress, quality=None)
            Snackbar(text=f"'{self.lemma}' added to your study plan").open()
        except Exception as e:
            Snackbar(text=f"Error: {e}").open()
