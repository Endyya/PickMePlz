import random as rd
import numpy as np
import matplotlib as mpl
from matplotlib.pyplot import viridis

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp, mm
from kivy.graphics import Canvas, Ellipse, Color, Line, Rectangle
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.properties import StringProperty, DictProperty


class Touch(Widget):
    def __init__(self, color = (0, 0, 0, 1), spacing = dp(2), progress = 0.01,
                 identifier = -1, *args, **kwargs):

        # store touch parameters
        self._id = identifier
        self._touch_pos = kwargs['pos']
        self._spacing = spacing
        self._progress = progress
        self._event = None
        self._color = color

        # correct the position to fit the touched area
        kwargs['pos'] = self.correct_pos(pos = kwargs['pos'],
                                         size = kwargs['size'])

        # make the widget
        super().__init__(*args, **kwargs)

        # initialize the canvas
        self._draw()

    def remove(self):
        if self.event is not None:
            self.event.cancel()
        with self.canvas:
            self.canvas.clear()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self._draw()

    @property
    def event(self):
        return self._event

    @event.setter
    def event(self, value):
        self._event = value

    @property
    def touch_pos(self):
        return self._touch_pos

    @touch_pos.setter
    def touch_pos(self, value):
        self._touch_pos = value
        self._draw()

    @property
    def spacing(self):
        return self._spacing

    @property
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = value
        self._draw()

    @staticmethod
    def correct_pos(pos, size):
        """ 
        Return the position of a widget which center is the position given
        """
        new_pos = pos[0] - size[0] / 2, pos[1] - size[1] / 2
        return new_pos

    def _draw(self):
        with self.canvas:
            self.canvas.clear()
            Color(*self.color)
            width = dp(5)
            Line(circle = (*self.touch_pos, self.size[0] / 2, 0,
                           3.6 * min(100, self.progress)),
                 cap = 'round', joint = 'round', width = width, pos = self.pos,
                 size = (self.size[0] - width / 2, self.size[1] / 2))
            small_size = (self.size[0] - 2 * width - 2 * self.spacing,
                          self.size[1] - 2 * width - 2 * self.spacing)
            small_pos = self.correct_pos(self.touch_pos, small_size)
            Ellipse(pos = small_pos, size = small_size)

    def forward(self, dt):
        self.progress += 1

class PickLayout(FloatLayout):


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._touchs = {}
        self.check_event = Clock.schedule_interval(self.pickaplayer, 0.2)
        self._standby = False
        self.standby_trigger = None

    @property
    def standby(self):
        return self._standby

    @standby.setter
    def standby(self, value):

        # if the standby trigger exists and standby goes into false state
        if self.standby_trigger is not None and not value:
            self.standby_trigger()
            self.standby_trigger = None
        self.standby_trigger = None

    def pickaplayer(self, dt):
        endtime = len(self._touchs) > 1
        for touch in self._touchs.values():
            endtime = endtime and touch.progress >= 100
        if endtime:
            choosen_player_id = rd.choice(list(self._touchs.keys()))
            for player_id in self._touchs.keys():
                if player_id != choosen_player_id:
                    self._touchs[player_id].remove()
            self._touchs = {choosen_player_id: self._touchs[choosen_player_id]}
            self.standby = True
            self.choosen_player_id = choosen_player_id

    def on_touch_down(self, touch):
        # use the parent method
        super().on_touch_down(touch)

        # remove standby mode
        self.standby = False

        # reset progress of all existing touchs
        for tk in self._touchs.keys():
            t = self._touchs[tk]
            t.progress = min(t.progress, 70)

        # create the new touch
        new_touch = Touch(pos = touch.pos,
                          size_hint = (None, None),
                          size = (dp(110), dp(110)),
                          spacing = mm(1),
                          identifier = touch.id)
        self.add_widget(new_touch)
        self._touchs[touch.id] = new_touch
        new_touch.event = Clock.schedule_interval(new_touch.forward, 0.01)

        # update colorscale
        count_touchs = len(self._touchs.keys())
        indexes = list(np.linspace(0, 255, count_touchs, dtype = int))
        indexes = indexes[1:]
        indexes.append(0)
        indexes = indexes[::-1]
        color_scale = [mpl.cm.viridis.colors[i] for i in indexes]
        for k, touch in enumerate(self._touchs.values()):
            touch.color = color_scale[k]

    def on_touch_move(self, touch):
        # use the parent method
        super().on_touch_move(touch)

        # move the widget
        try:
            self._touchs[touch.id].touch_pos = touch.pos
        except KeyError:
            print('This touch does not exist anymore')

    def on_touch_up(self, touch):
        # use the parent method
        super().on_touch_up(touch)

        # remove the touch if it still exists and standby mode is of
        try:
            if self.standby and touch.id == self.choosen_player_id:
                self.standby_trigger = Clock.create_trigger(
                    lambda x: self.remove_touch(self.choosen_player_id))
            else:
                self.remove_touch(touch.id)
        except KeyError:
            print('Key error')

    def remove_touch(self, touch_id):
        self._touchs[touch_id].remove()
        del self._touchs[touch_id]

class PickMePlzApp(App):
    pass

PickMePlzApp().run()
            
