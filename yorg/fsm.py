from random import shuffle, randint
from direct.gui.OnscreenText import OnscreenText
from yaml import load
from yyagl.racing.race.race import RaceSinglePlayer, RaceServer, RaceClient
from yyagl.racing.race.raceprops import RaceProps
from yyagl.racing.driver.driver import Driver, DriverProps
from yyagl.gameobject import Fsm
from yyagl.racing.season.season import SingleRaceSeason
from yyagl.engine.gui.menu import MenuArgs
from menu.menu import YorgMenu
from menu.exitmenu.menu import ExitMenu
from menu.ingamemenu.menu import InGameMenu
import sys
import os


class _Fsm(Fsm):

    def __init__(self, mdt):
        Fsm.__init__(self, mdt)
        self.defaultTransitions = {
            'Menu': ['Race', 'Exit'],
            'Race': ['Ranking', 'Menu', 'Exit'],
            'Ranking': ['Tuning', 'Exit'],
            'Tuning': ['Menu', 'Race', 'Exit'],
            'Exit': ['Exit']}
        self.load_txt = None
        self.preview = None
        self.cam_tsk = None
        self.cam_node = None
        self.ranking_texts = None
        self.send_tsk = None
        self.cam_pivot = None
        self.ready_clients = None
        self.curr_load_txt = None
        self.__menu = None
        self.race = None
        self.__exit_menu = None

    def enterMenu(self):
        eng.log_mgr.log('entering Menu state')
        self.__menu = YorgMenu()
        self.mdt.audio.menu_music.play()
        for file_ in os.listdir('.'):
            if file_.endswith('.bam'):
                curr_version = eng.logic.version
                file_version = file_[:-4].split('_')[-1]
                if curr_version != file_version:
                    eng.log_mgr.log('removing ' + file_)
                    os.remove(file_)
        if game.logic.season:
            game.logic.season.logic.detach(game.event.on_season_end)
            game.logic.season.logic.detach(game.event.on_season_cont)

    def exitMenu(self):
        eng.log_mgr.log('exiting Menu state')
        self.__menu.destroy()
        self.mdt.audio.menu_music.stop()

    def enterRace(self, track_path='', car_path='', drivers='', skills=''):
        eng.log_mgr.log('entering Race state')
        base.ignore('escape-up')
        if 'save' not in game.options.dct:
            game.options['save'] = {}
        game.options['save']['track'] = track_path[7:]
        game.options['save']['car'] = car_path
        game.options['save']['drivers'] = drivers
        game.options.store()
        keys = self.mdt.options['settings']['keys']
        joystick = self.mdt.options['settings']['joystick']
        menu_args = MenuArgs(
            'assets/fonts/Hanken-Book.ttf', (.75, .75, .25, 1),
            (.75, .75, .75, 1), .1, (-4.6, 4.6, -.32, .88), (0, 0, 0, .2),
            'assets/images/loading/%s%s.jpg' % (track_path[7:], randint(1, 4)),
            'assets/sfx/menu_over.wav', 'assets/sfx/menu_clicked.ogg', '',
            (.75, .25, .25, 1))
        sounds = {
            'engine': 'assets/sfx/engine.ogg',
            'brake': 'assets/sfx/brake.ogg',
            'crash': 'assets/sfx/crash.ogg',
            'crash_hs': 'assets/sfx/crash_high_speed.ogg',
            'lap': 'assets/sfx/lap.ogg',
            'landing': 'assets/sfx/landing.ogg'}
        if eng.server.is_active:
            self.race = RaceServer(keys, joystick, sounds)
        elif eng.client.is_active:
            self.race = RaceClient(keys, joystick, sounds)
        else:
            wheel_names = [['EmptyWheelFront', 'EmptyWheelFront.001',
                            'EmptyWheelRear', 'EmptyWheelRear.001'],
                           ['EmptyWheel', 'EmptyWheel.001', 'EmptyWheel.002',
                            'EmptyWheel.003']]
            wheel_gfx_names = ['wheelfront', 'wheelrear', 'wheel']
            wheel_gfx_names = ['assets/models/cars/%s/' + elm
                               for elm in wheel_gfx_names]
            tuning = self.mdt.logic.season.logic.tuning.logic.tunings[car_path]

            def get_driver(car):
                for driver in drivers:
                    if driver[2] == car:
                        return driver
            driver_engine, driver_tires, driver_suspensions = \
                skills[get_driver(car_path)[0] - 1]
            drivers_dct = {}
            for driver in drivers:
                d_s = skills[get_driver(driver[2])[0] - 1]
                driver_props = DriverProps(
                    str(driver[0]), d_s[0], d_s[1], d_s[2])
                drv = Driver(driver_props)
                drivers_dct[driver[2]] = drv
            with open('assets/models/%s/track.yml' % track_path) as track_file:
                track_conf = load(track_file)
                music_name = track_conf['music']
            music_path = 'assets/music/%s.ogg' % music_name
            corner_names = ['topleft', 'topright', 'bottomright', 'bottomleft']
            corner_names = ['Minimap' + crn for crn in corner_names]
            col_dct = {
                'kronos': (0, 0, 1, 1),
                'themis': (1, 0, 0, 1),
                'diones': (1, 1, 1, 1),
                'iapeto': (1, 1, 0, 1)}
            with open('assets/models/%s/track.yml' % track_path) as track_file:
                track_cfg = load(track_file)
                camera_vec = track_cfg['camera_vector']
                shadow_src = track_cfg['shadow_source']
                laps = track_cfg['laps']

            def sign_cb(parent):
                thanks = open('assets/thanks.txt').readlines()
                shuffle(thanks)
                text = '\n\n'.join(thanks[:3])
                txt = OnscreenText(text, parent=parent, scale=.2,
                                   fg=(0, 0, 0, 1), pos=(.245, 0))
                bounds = lambda: txt.getTightBounds()
                while bounds()[1][0] - bounds()[0][0] > .48:
                    scale = txt.getScale()[0]
                    txt.setScale(scale - .01, scale - .01)
                bounds = txt.getTightBounds()
                height = bounds[1][2] - bounds[0][2]
                txt.setZ(.06 + height / 2)
            race_props = RaceProps(
                keys, joystick, sounds, (.75, .75, .25, 1), (.75, .75, .75, 1),
                'assets/fonts/Hanken-Book.ttf',
                'assets/models/cars/%s/capsule', 'Capsule',
                'assets/models/cars', 'assets/models/cars/%s/phys.yml',
                wheel_names, tuning.engine, tuning.tires, tuning.suspensions,
                'Road', 'assets/models/cars/%s/car',
                ['assets/models/cars/%s/cardamage1',
                 'assets/models/cars/%s/cardamage2'], wheel_gfx_names,
                'assets/particles/sparks.ptf', drivers_dct,
                game.options['development']['shaders'], music_path,
                'assets/models/%s/collision' % track_path, ['Road', 'Offroad'],
                ['Wall'], ['Goal', 'Slow', 'Respawn', 'PitStop'],
                corner_names, ['Waypoints', 'Waypoint', 'prev'],
                game.options['development']['show_waypoints'],
                game.options['development']['weapons'],
                ['Weaponboxs', 'EmptyWeaponboxAnim'], 'Start', track_path[7:],
                track_path, 'track', 'Empty', 'Anim', 'omni',
                sign_cb, 'EmptyNameBillboard4Anim',
                'assets/images/minimaps/%s.png' % track_path[7:],
                'assets/images/minimaps/car_handle.png', col_dct, camera_vec,
                shadow_src, laps, 'assets/models/weapons/rocket/rocket',
                'assets/models/weapons/bonus/WeaponboxAnim', 'Anim',
                ['kronos', 'themis', 'diones', 'iapeto'],
                game.options['development']['ai'], InGameMenu,
                menu_args, 'assets/images/drivers/driver%s_sel.png',
                'assets/images/cars/%s_sel.png',
                ['https://www.facebook.com/sharer/sharer.php?u=ya2.it/yorg',
                 'https://twitter.com/share?text=I%27ve%20achieved%20{time}'
                 '%20in%20the%20{track}%20track%20on%20Yorg%20by%20%40ya2tech'
                 '%21&hashtags=yorg',
                 'https://plus.google.com/share?url=ya2.it/yorg',
                 'https://www.tumblr.com/widgets/share/tool?url=ya2.it'],
                'assets/images/icons/%s_png.png', 'Respawn', 'PitStop',
                'Wall', 'Goal', 'Bonus', ['Road', 'Offroad'],
                ['kronos', 'themis', 'diones', 'iapeto'], car_path)
            #todo compute the grid
            self.race = RaceSinglePlayer(race_props)
            # use global template args
        eng.log_mgr.log('selected drivers: ' + str(drivers))
        self.race.logic.drivers = drivers
        track_name_transl = track_path[7:]
        track_dct = {
            'desert': _('desert'),
            'mountain': _('mountain')}
        if track_path[7:] in track_dct:
            track_name_transl = track_dct[track_path[7:]]
        singlerace = game.logic.season.__class__ == SingleRaceSeason
        self.race.fsm.demand(
            'Loading', track_path, car_path, [], drivers,
            ['prototype', 'desert'], track_name_transl, singlerace,
            ['kronos', 'themis', 'diones', 'iapeto'],
            'assets/images/cars/%s_sel.png',
            'assets/images/drivers/driver%s_sel.png',
            game.options['settings']['joystick'],
            game.options['settings']['keys'], menu_args,
            'assets/sfx/countdown.ogg')
        self.race.event.attach(self.on_race_loaded)

    def on_race_loaded(self):
        self.race.event.detach(self.on_race_loaded)
        self.race.gui.results.attach(self.on_race_step)

    def on_race_step(self, race_ranking):
        self.race.gui.results.detach(self.on_race_step)
        ranking = game.logic.season.logic.ranking
        tuning = game.logic.season.logic.tuning
        from yyagl.racing.season.season import SingleRaceSeason
        if game.logic.season.__class__ != SingleRaceSeason:
            for car in ranking.logic.ranking:
                ranking.logic.ranking[car] += race_ranking[car]
            game.options['save']['ranking'] = ranking.logic.ranking
            game.options['save']['tuning'] = tuning.logic.tunings
            game.options.store()
            game.fsm.demand('Ranking')
        else:
            game.fsm.demand('Menu')

    def exitRace(self):
        eng.log_mgr.log('exiting Race state')
        self.race.destroy()
        base.accept('escape-up', self.demand, ['Exit'])

    def enterRanking(self):
        game.logic.season.logic.ranking.gui.show()
        to_tun = lambda task: game.fsm.demand('Tuning')
        taskMgr.doMethodLater(10, to_tun, 'tuning')

    def exitRanking(self):
        game.logic.season.logic.ranking.gui.hide()

    def enterTuning(self):
        game.logic.season.logic.tuning.gui.show()

    def exitTuning(self):
        game.logic.season.logic.tuning.gui.hide()

    def enterExit(self):
        if not game.options['development']['show_exit']:
            sys.exit()
        self.__exit_menu = ExitMenu()

    def exitExit(self):
        self.__exit_menu.destroy()
