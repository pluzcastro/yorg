from direct.gui.DirectButton import DirectButton
from racing.game.engine.gui.page import Page, PageGui
from .carpage import CarPage, CarPageServer
from .netmsgs import NetMsgs


class TrackPageGui(PageGui):

    def build_page(self):
        menu_gui = self.menu.gui

        menu_data = [
            ('Desert', self.on_track, ['desert']),
            ('Prototype', self.on_track, ['prototype'])]
        self.widgets += [
            DirectButton(text=menu[0], pos=(0, 1, .4-i*.28), command=menu[1],
                         extraArgs=menu[2], **menu_gui.btn_args)
            for i, menu in enumerate(menu_data)]
        PageGui.build_page(self)

    def on_track(self, track):
        self.menu.track = track
        self.menu.logic.push_page(CarPage(self.menu))

    def destroy(self):
        if hasattr(self.menu, 'track'):
            del self.menu.track
        PageGui.destroy(self)


class TrackPageGuiServer(TrackPageGui):

    def on_track(self, track):
        self.menu.track = track
        self.menu.logic.push_page(CarPageServer(self.menu))
        eng.server.send([NetMsgs.track_selected, track])


class TrackPage(Page):
    gui_cls = TrackPageGui


class TrackPageServer(Page):
    gui_cls = TrackPageGuiServer
