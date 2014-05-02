from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.properties import ObjectProperty
from os.path import isfile

from kivy.lang import Builder

Builder.load_file("editor.kv")


class LevelEditorWidget(Widget):
    def export_level(self, path):
        out = "level boats={} flys={} energy={} ".format(
            self.sidebar.level_settings.boats_count.text,
            self.sidebar.level_settings.flys_count.text,
            self.sidebar.level_settings.energy_count.text)
        # get level size
        max_x = 0
        max_y = 0
        children = self.level.children
        for c in children:
            x = int(round(c.center_x / dp(100), 0))
            if x > max_x:
                max_x = x
            y = int(round(c.y / dp(100), 0))
            if y > max_y:
                max_y = y
        out += "size={},{}\n".format(max_x + 1, max_y + 1)
        # add the objects
        for c in self.level.children:
            extra_opts = " "
            if type(c) == WaterLilyPH:
                tp = "waterlily"
            elif type(c) == StoneLilyPH:
                tp = "stonelily"
            elif type(c) == SwitchLilyPH:
                if c.options.controlled:
                    tp = "switchlily"
                    extra_opts += "controlled={}".format(
                        c.options.controlled.id)
                else:
                    tp = "stonelily"
            elif type(c) == StartPH:
                tp = "start"
            elif type(c) == EndPH:
                tp = "end"
            else:
                continue
            x = int(round(c.center_x / dp(100), 0))
            y = int(round(c.y / dp(100), 0))
            id = c.id
            s = "{} pos={},{} id={}".format(tp, x, y, id)
            out += s + extra_opts + "\n"
        # Add the player frog
        out += "frog id=player jump_img={} sit_img={} player=True place=start\n"\
            .format(
                self.level.start.frog.jump_img,
                self.level.start.frog.sit_img)
        # Add the other frogs
        for frog in [c for c in self.level.children
                     if type(c) == FrogPH]:
            out += "frog jump_img={} sit_img={} place={}\n".format(
                frog.jump_img, frog.sit_img, frog.place)
        print out
        f = open(path, "w")
        f.write(out)
        f.close()

    def next_level_name(self):
        i = 1
        LOOP = True
        while LOOP:
            if not isfile("levels/custom_level_%d3.txt" % i):
                return "levels/custom_level_%03d.txt" % i
            i += 1


class LevelScatter(Scatter):
    def __init__(self, **kwargs):
        super(LevelScatter, self).__init__(**kwargs)
        self.build_standard()

    def on_transform_with_touch(self, touch):
        if self.x > 0:
            self.x = 0
        if self.y > 0:
            self.y = 0

    def calculate_line_points(self):
        points = []
        for i in range(0, 50):
            if i % 2:
                points.extend([i * dp(100), dp(5000),
                               i * dp(100), 0])
            else:
                points.extend([i * dp(100), 0,
                               i * dp(100), dp(5000)])
        points.extend([0, 0])
        for i in range(0, 50):
            if i % 2:
                points.extend([dp(5000), i * dp(100),
                               0, i * dp(100)])
            else:
                points.extend([0, i * dp(100),
                               dp(5000), i * dp(100)])
        return points

    def add_widget(self, widget, index=0):
        """Override to set object ids"""
        if type(widget) in [WaterLilyPH,
                            StoneLilyPH,
                            SwitchLilyPH]:
            widget.id = "object_%03d" %\
                self.app.editor.object_count
            self.app.editor.object_count += 1
        super(LevelScatter, self).add_widget(widget, index)

    def build_standard(self):
        self.clear_widgets()
        self.start = StartPH(id="start")
        self.add_widget(self.start)
        self.end = EndPH(id="end")
        self.add_widget(self.end)


class ToolBar(Widget):
    pass


class SideBar(Widget):
    pass


class BackgroundPH(Image):
    pass


class PHScatter(Scatter):
    """Base class for placeholders"""
    current_touch = None
    option_type = None
    options = None

    def __init__(self, **kwargs):
        super(PHScatter, self).__init__(**kwargs)
        if self.option_type is not None:
            self.options = self.option_type(obj=self)

    def on_transform_with_touch(self, touch):
        self.current_touch = touch
        self.app.editor.select.center = self.center
        if not self.moved:
            self.parent.add_widget(type(self)(pos=self.parent.pos))
            self.moved = True
            self.parent.remove_widget(self)
            self.app.editor.level.add_widget(self)
            self.center_x = touch.pos[0]
            self.center_y = touch.pos[1]

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super(PHScatter, self).on_touch_down(touch)
        self.app.editor.select.center = self.center
        if not self.app.editor.sidebar.object_content.children\
           == [self.options]:
            self.app.editor.sidebar.object_content.clear_widgets()
            if self.options:
                self.options.top = self.app.editor.\
                                   sidebar.object_content.top
                self.options.x = self.app.editor.\
                                 sidebar.object_content.x
                self.options.width = self.app.editor.\
                             sidebar.object_content.width
                self.app.editor.sidebar.object_content.add_widget(
                    self.options)
        return super(PHScatter, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch == self.current_touch:
            self.current_touch = None
            if self.app.editor.delete.collide_point(*self.center):
                for f in [frog for frog in self.parent.children
                          if type(frog) == FrogPH]:
                    if f.place == self.id:
                        self.app.editor.level.remove_widget(f)
                self.app.editor.level.remove_widget(self)
                return True
            x = int(round(self.center_x / dp(100), 0))
            y = int(round(self.y / dp(100), 0))
            center_x = dp(100) * x
            y = dp(100) * y
            # Loop until a free place was found
            LOOP = True
            while LOOP:
                for child in self.parent.children:
                    if child.center_x == center_x and\
                       y == child.y and child != self:
                        x += 1
                        center_x = dp(100) * x
                        break
                else:
                    LOOP = False
            self.center_x = center_x
            self.y = y
            self.app.editor.select.center = self.center
            return True
        return super(PHScatter, self).on_touch_up(touch)


class WaterLilyPH(PHScatter):
    """Waterlily placeholder for the level editor"""
    pass


class StoneLilyPH(PHScatter):
    """Stonelily placeholder"""
    pass


class SwitchLilyOptions(Widget):
    controlled = ObjectProperty(None, allownone=True)
    last_controlled = ObjectProperty(None, allownone=True)
    obj = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(SwitchLilyOptions, self).__init__(**kwargs)
        self.bind(controlled=self.on_controlled_change)

    def on_controlled_change(self, instance, value):
        if self.last_controlled:
            self.last_controlled.source = self.std_img
        self.last_controlled = value
        if value:
            self.std_img = value.source
            value.source = self.controlled_img


class SwitchLilyPH(PHScatter):
    """Switchlily placeholder"""
    option_type = SwitchLilyOptions


class BasePH(PHScatter):
    def on_transform_with_touch(self, touch):
        self.current_touch = touch

    def on_touch_up(self, touch):
        if touch == self.current_touch:
            self.current_touch = None
            x = int(round(self.center_x / dp(100), 0))
            y = int(round(self.y / dp(100), 0))
            center = (dp(100) * x, dp(100) * y + dp(50))
            # Loop until a free place was found
            LOOP = True
            while LOOP:
                for child in self.parent.children:
                    if child.center == center and child != self:
                        x += 1
                        center = (dp(100) * x, dp(100) * y)
                        break
                else:
                    LOOP = False
            self.center = center
            return True
        return super(PHScatter, self).on_touch_up(touch)


class StartPH(BasePH):
    pass


class EndPH(BasePH):
    pass


class FrogPH(PHScatter):
    def on_touch_up(self, touch):
        if touch == self.current_touch:
            self.current_touch = None
            if self.app.editor.delete.collide_point(*touch.pos):
                self.app.editor.level.remove_widget(self)
                return True
            x = int(round(self.center_x / dp(100), 0))
            y = int(round(self.y / dp(100), 0))
            center_x = dp(100) * x
            y = dp(100) * y
            # Loop until a free place was found
            LOOP = True
            for child in self.parent.children:
                if child.center_x == center_x and\
                   y == child.y and child != self and\
                   type(child) != FrogPH and\
                   type(child) != StartPH:
                    for frog in [c for c in self.parent.children
                                 if type(c) == FrogPH]:
                        if frog.place == child.id and frog != self:
                            break
                    else:
                        child.bind(pos=self.on_parent_pos)
                        self.center = child.center
                        self.place = child.id
                        break
            else:
                self.parent.remove_widget(self)
            return True
        return super(PHScatter, self).on_touch_up(touch)

    def on_parent_pos(self, instance, value):
        if instance.id == self.place:
            self.center = instance.center


class NumericInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        if substring.isdigit():
            return super(NumericInput, self)\
                .insert_text(substring, from_undo=from_undo)

    def on_focus(self, instance, value):
        if not value:
            if self.text.strip() == "":
                self.insert_text("0")
        super(NumericInput, self).on_focus(instance, value)


class SelectButton(Button):
    binded = False
    selected = ObjectProperty(None, allownone=True)

    def __init__(self, **kwargs):
        super(SelectButton, self).__init__(**kwargs)

    def on_press(self):
        self.selecting = True
        if not self.binded:
            self.app.editor.level.bind(on_touch_down=
                                       self.on_touch_select)

    def on_touch_select(self, instance, touch):
        if self.selecting:
            self.selecting = False
            for o in self.app.editor.level.children:
                if type(o) in [WaterLilyPH,
                               StoneLilyPH,
                               SwitchLilyPH] and o.collide_point(
                                   *touch.pos
                               ) and o not in self.ignore:
                    self.selected = o
                    return True
            self.selected = None
        return super(SelectButton, self).on_touch_up(touch)
