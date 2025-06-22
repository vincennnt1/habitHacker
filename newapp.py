import kivy
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.graph import Graph, BarPlot
from collections import Counter
import csv

import joblib
import json
from info import getGenres, get_location, get_weather
from load import clean, mod, le
import dataManager
from dataManager import update, submit, remove, get_recent_entries

import numpy as np

import logging
from kivy.logger import Logger

Logger.setLevel(logging.ERROR)

def count_emotions_from_csv(filename="user_info.csv"):
    emotion_counts = Counter()
    try:
        with open(filename, newline='', encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sentiment = row.get(" sentiment", "").strip()
                if sentiment:
                    emotion_counts[sentiment] += 1
        return dict(emotion_counts)
    except Exception as e:
        print(f"Error reading file: {e}")

class EmotionBarGraphScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        title = Label(text="Emotion Frequency", font_size='24sp', size_hint_y=None, height=50)
        layout.add_widget(title)

        # Dummy emotion counts for example
        emotion_counts = count_emotions_from_csv()
        emotions = list(emotion_counts.keys())
        counts = list(emotion_counts.values())
        max_count = max(counts) if counts else 1

        graph = Graph(
            xlabel='Emotions',
            ylabel='Count',
            x_ticks_major=1,
            y_ticks_major=1,
            y_grid_label=True,
            x_grid_label=True,
            padding=50,
            x_grid=True,
            y_grid=True,
            xmin=0,
            xmax=len(emotions) + 1,
            ymin=0,
            ymax=max_count + 1,
            size_hint_y=0.7
        )

        plot = BarPlot(color=[0.2, 0.6, 0.9, 1], bar_width=15)
        # Important: points must be a list of (x, y) tuples
        plot.points = [(i + 1, counts[i]) for i in range(len(counts))]

        graph.add_plot(plot)

        layout.add_widget(graph)

        # Add labels for emotions below the graph
        labels_layout = BoxLayout(size_hint_y=None, height=30, spacing=10, padding=10)
        for i in range(len(emotions)):
            lbl = Label(text=f"{i + 1}. {emotions[i].capitalize()}", size_hint_x=None, width=80)
            labels_layout.add_widget(lbl)
        layout.add_widget(labels_layout)

        back_btn = Button(text="Back", size_hint_y=None, height=50)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'entry'))
        layout.add_widget(back_btn)

        self.add_widget(layout)

class LogScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)
        self.title = Label(text="Past Entries", font_size='24sp', size_hint_y=None, height=40)
        self.layout.add_widget(self.title)

        # Container to hold all entry rows
        self.entries_container = BoxLayout(orientation='vertical', spacing=5, size_hint_y=None)
        self.entries_container.bind(minimum_height=self.entries_container.setter('height'))

        # ScrollView to scroll the entries
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.entries_container)
        self.layout.add_widget(scroll)

        # Back button
        back_button = Button(text="Back", size_hint_y=None, height=50)
        back_button.bind(on_press=self.go_back)
        self.layout.add_widget(back_button)

        self.add_widget(self.layout)

    def on_pre_enter(self):
        self.load_entries()

    def load_entries(self):
        self.entries_container.clear_widgets()

        entries = get_recent_entries()

        for entry in entries:
            if entry[0] == "id":
                text = "Title | Date | Weather | Genre | Entry | Feeling"
            # Format the entry text (skip columns 0 and 4)
            else:
                text = " | ".join([val for i, val in enumerate(entry) if i != 0 and i != 4])

            # Horizontal layout for the entry text + delete button
            row = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)

            # Label with entry text
            lbl = Label(text=text, halign='left', valign='middle', size_hint_x=0.85)
            lbl.bind(size=lbl.setter('text_size'))

            # Delete button
            if entry[0] != "id":
                btn = Button(text="Delete", size_hint_x=0.15)

                entry_id = entry[0]
                btn.bind(on_press=lambda inst, eid=entry_id: self.delete_entry(eid))

            row.add_widget(lbl)
            if entry[0] != "id":
                row.add_widget(btn)

            self.entries_container.add_widget(row)

    def delete_entry(self, entry_id):
        remove(entry_id)
        self.load_entries()

    def go_back(self, instance):
        self.manager.current = 'entry'

class MoodSummaryScreen(Screen):
    def __init__(self, mood_data, **kwargs):
        super().__init__(**kwargs)

        # Main vertical layout
        self.layout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # Title label
        title = Label(text="Mood Indicators", font_size='24sp', size_hint_y=None, height=50)
        self.layout.add_widget(title)

        # Container grid for mood boxes (2 columns)
        container = GridLayout(cols=2, spacing=20, padding=20, size_hint_y=None)
        container.bind(minimum_height=container.setter('height'))

        for mood, details in mood_data.items():
            if mood == "ENTRIES_NUM":
                continue

            # Each mood box is a vertical BoxLayout with spacing and padding
            mood_box = BoxLayout(orientation='vertical', spacing=10, padding=10, size_hint_y=None)
            mood_box.bind(minimum_height=mood_box.setter('height'))

            # Add mood title label
            title_lbl = Label(
                text=mood.capitalize(),
                font_size='17sp',
                bold=True,
                size_hint_y=None,
                halign='center'
            )
            title_lbl.bind(texture_size=lambda lbl, ts: setattr(lbl, 'height', ts[1] + 10))
            title_lbl.text_size = (self.width, None)  # enable wrapping if needed
            mood_box.add_widget(title_lbl)

            # Add "Top Weather" section header
            mood_box.add_widget(Label(text="Top Weather:", font_size='16sp', bold=True, size_hint_y=None, height=30))

            # Weather items labels
            weather_items = sorted(details.get("weather", {}).items(), key=lambda x: x[1], reverse=True)[:2]
            for weather, count in weather_items:
                if count <= 0:
                    continue
                text = f"• {weather.capitalize()} — {count} entr{'y' if count == 1 else 'ies'}"
                lbl = Label(text=text, font_size='14sp', size_hint_y=None, halign='left')
                lbl.bind(texture_size=lambda lbl, ts: setattr(lbl, 'height', ts[1] + 8))
                lbl.text_size = (self.width, None)
                mood_box.add_widget(lbl)

            # Add "Top Genres" section header
            mood_box.add_widget(Label(text="Top Genres:", font_size='16sp', bold=True, size_hint_y=None, height=30))

            # Genre items labels
            genre_items = sorted(details.get("genres", {}).items(), key=lambda x: x[1], reverse=True)[:2]
            for genre, count in genre_items:
                if count <= 0:
                    continue
                genre_name = ' '.join(word.capitalize() for word in genre.split())
                text = f"• {genre_name} — {count} entr{'y' if count == 1 else 'ies'}"
                lbl = Label(text=text, font_size='14sp', size_hint_y=None, halign='left')
                lbl.bind(texture_size=lambda lbl, ts: setattr(lbl, 'height', ts[1] + 8))
                lbl.text_size = (self.width, None)
                mood_box.add_widget(lbl)

            container.add_widget(mood_box)

        # ScrollView containing the container grid
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(container)
        self.layout.add_widget(scroll)

        # Back button
        back_btn = Button(text="Back", size_hint_y=None, height=50)
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'entry'))
        self.layout.add_widget(back_btn)

        self.add_widget(self.layout)

class childApp(GridLayout):
    def __init__(self, screen_manager=None, **kwargs):
        super(childApp, self).__init__(**kwargs)
        self.screen_manager = screen_manager
        self.cols = 2

        self.add_widget(Label(text="Title"))
        self.s_Title = TextInput(multiline=False)
        self.add_widget(self.s_Title)

        self.add_widget(Label(text="Notes"))
        self.s_Notes = TextInput(multiline=False)
        self.add_widget(self.s_Notes)

        self.add_widget(Label(text="Main Emotion"))
        self.s_Main_Emotion = TextInput(multiline=False)
        self.add_widget(self.s_Main_Emotion)

        self.press = Button(text="Click me")
        self.press.bind(on_press=self.click_me)
        self.add_widget(self.press)

        self.listButton = Button(text="All Entries")
        self.listButton.bind(on_press=self.entryClick)
        self.add_widget(self.listButton)

        self.emotButton = Button(text="Mood Indicators")
        self.emotButton.bind(on_press=self.moodClick)
        self.add_widget(self.emotButton)

        self.graphButton = Button(text="Mood Graph")
        self.graphButton.bind(on_press=self.graphClick)
        self.add_widget(self.graphButton)

    def click_me(self, instance):
        title = self.s_Title.text
        notes = self.s_Notes.text

        clean_entry = [clean(notes)]
        pred_proba = mod.predict_proba(clean_entry)
        pred_index = np.argmax(pred_proba, axis=1)
        emotion = le.inverse_transform(pred_index)[0]

        self.s_Main_Emotion.text = emotion
        submit(notes, title)

    def entryClick(self, instance):
        if self.screen_manager:
            self.screen_manager.current = 'logs'

    def moodClick(self, instance):
        if self.screen_manager:
            self.screen_manager.current = 'mood_summary'
    
    def graphClick(self, instance):
        if self.screen_manager:
            self.screen_manager.current = 'emotion_graph'
        

class parentApp(App):
    def build(self):
        sm = ScreenManager()

        entry_screen = Screen(name='entry')
        entry_screen.add_widget(childApp(screen_manager=sm))
        sm.add_widget(entry_screen)

        log_screen = LogScreen(name='logs')
        sm.add_widget(log_screen)

        with open("user.json", "r", encoding="utf-8") as f:
            mood_data = json.load(f)
        mood_screen = MoodSummaryScreen(mood_data, name='mood_summary')
        sm.add_widget(mood_screen)

        emotion_screen = EmotionBarGraphScreen(name='emotion_graph')
        sm.add_widget(emotion_screen)

        return sm
if __name__ == '__main__':
    parentApp().run()