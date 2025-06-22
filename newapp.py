import kivy
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

import joblib
from info import getGenres, get_location, get_weather
from load import clean, mod, le
import dataManager
from dataManager import update, submit, remove

import numpy as np

import logging
from kivy.logger import Logger

Logger.setLevel(logging.ERROR)


class childApp(GridLayout):
    def __init__(self, **kwargs):
        super(childApp, self).__init__()
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

    def click_me(self, instance):
        title = self.s_Title.text
        notes = self.s_Notes.text

        clean_entry = [clean(notes)]
        # predicts probabilities
        pred_proba = mod.predict_proba(clean_entry)
        # gets top probaility
        pred_index = np.argmax(pred_proba, axis=1)
        emotion = le.inverse_transform(pred_index)[0]

        self.s_Main_Emotion.text = emotion
        submit(notes, title)


class parentApp(App):
    def build(self):
        return childApp()
if __name__ == '__main__':
    parentApp().run()