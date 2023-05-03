import pygame as pg
import sys
import os
import random
import pickle
import units, battle_fun
from base import *
from battle import *
from configs import *
from guide import *

def load_user():
    try:
        file = open("user.p", "rb")
    except FileNotFoundError:
        user = {"score":0,
                "all_units":["soldier", "bow_infantry", "shielded_sword_infantry", "elite_spear_infantry",
                             "light_cavalry", "king", "fire", "wind"],
                "guide":[0, 0, 0]}
        user["wear_units"] = user["all_units"].copy()
        write_user(user)
        return user
    else:
        data = pickle.load(file)
        return pickle.loads(data[::-1])

def write_user(user):
    data = pickle.dumps(user)[::-1]
    with open("user.p", "wb") as f:
        pickle.dump(data, f)

class Loading(Scene):
    def init(self):
        self.background = load_image("mainmenu.jpg").copy()
        self.background.blit(load_image("logo.png"), load_image("logo.png").get_rect(centerx=WIDTH//2, y=150)) 
        r = render(_("游戏提示：")+random.choice(GAMETIPS), size=16)
        self.background.blit(r, r.get_rect(centerx=WIDTH//2, y=HEIGHT-50))
        
        self.idx = 0
        self.assets = os.listdir(path("assets"))
        self.count = len(self.assets)
        
        self.progress_bar = pg.Surface((600, 25))
        self.pbar_rect = self.progress_bar.get_rect(centerx=WIDTH/2, y=400)
        pg.draw.rect(self.progress_bar, (255, 255, 0),
                     (0, 0, self.pbar_rect.width, self.pbar_rect.height), width=2)

    def onexit(self):
        sys.exit()
        
    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.screen.blit(self.progress_bar, self.pbar_rect)

        prog = self.idx / self.count
        pg.draw.rect(self.progress_bar, (255, 0, 0),
                     (2, 2, prog * (self.pbar_rect.width-4), self.pbar_rect.height-4))
        r = render(str(int(prog * 100)) + "% ", size=15)
        self.screen.blit(r, r.get_rect(center=self.pbar_rect.center))
        
    def update(self):
        asset = self.assets[self.idx]
        if asset.endswith(".png"):
            load_image(asset)
        elif asset.endswith(".ogg"):
            load_sound("assets/" + asset)

        self.idx += 1
        if self.idx >= self.count:
            self.quit_scene()
        
class SceneWithButtons(Scene):
    def init(self):
        self.click = False
        self.tooltip = None
        
        self.tip = None
        self.effect_sprites = pg.sprite.Group()
        self.buttons = pg.sprite.Group()
        self.cup_rect = load_image("cup.png").get_rect(x=5, y=5)
        self.mm = MusicManager()

    def do(self, func, *args):
        def f():
            self.click = False
            self.tip = None
            func(*args)
        return f
    
    def show_tip(self, text):
        self.tip = FadeOutText(text, size=20)
        self.tip.rect.y = 40

    def show_tooltip(self, pos, text, anchor="bottomright"):
        if text:
            tip = renders([(text[0], (255, 255, 255), 18),
                           (text[1], (255, 255, 255), 13)], bg=(0, 0, 0, 150))
            rect = eval(f"tip.get_rect({anchor}=pos)")
            self.tooltip = Static(rect.x, rect.y, tip, pgim=True)

    def onexit(self):
        self.click = False
        self.quit_scene()
        
    def events(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                play_sound("button_click")
                self.click = True
        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 1:
                self.click = False
            
    def update(self):
        self.mm.update()
        pos = pg.mouse.get_pos()
        
        for sprite in self.effect_sprites:
            sprite.animate()
            
        if self.tip:
            self.tip.update()
            if not self.tip.alive:
                self.tip = None

    def draw(self):
        self.tooltip = None
        
        pos = pg.mouse.get_pos()
        for button in self.buttons:
            if button.update(self.screen, self.click, pos):
                self.show_tooltip(pos, button.tooltip, anchor=button.anchor)

        if self.cup_rect.collidepoint(pos):
            self.show_tooltip(pos, (_("奖杯"), GAMETIPS[0]),
                              anchor="topleft")

        self.screen.blit(with_image_render([load_image("cup.png"),
                                            " "+str(int(self.user["score"]))]), (5, 5))

        self.effect_sprites.draw(self.screen)
        
        if self.tooltip:
            self.tooltip.draw(self.screen)
        if self.tip:
            self.screen.blit(self.tip.image, self.tip.rect)
        
class Credits(SceneWithButtons):
    def __init__(self, user):
        self.user = user
        super().__init__()
        
    def init(self):
        super().init()
        
        self.background = load_image("mainmenu.jpg")
        self.group = []
        self.speed = 2

        i = 0
        for text in CREDITS.split("\n"):
            if text == "\n":
                i += 2
                continue
            
            sprite = render(text)
            self.group.append([sprite, sprite.get_rect(centerx=WIDTH//2,
                                                       y=HEIGHT+i*50)])
            i += 1

        Button(self.buttons, (WIDTH - 42, HEIGHT - 42), "button_return.png",
               (_("返回"), _("点击回到主菜单")), self.do(self.quit_scene))
        
    def draw(self):
        self.screen.blit(self.background, (0, 0))
        for i, (sprite, rect) in enumerate(self.group):
            if rect.y < HEIGHT:
                self.screen.blit(sprite, rect)
                
            rect.y -= self.speed
            if rect.bottom < 0:
                self.group.pop(i)

        super().draw()

    def update(self):
        super().update()
        if len(self.group) == 0:
            self.onexit()

class Party(SceneWithButtons):
    def __init__(self, user, start_battle):
        self.all_battle = []
        for cls in dir(battle_fun):
            if cls.startswith("b_"):
                self.all_battle.append(eval("battle_fun." + cls))
                
        self.user = user
        self.start_battle = start_battle
        super().__init__()

    def _left(self):
        self.click = False
        self.active_choice -= 1
        if self.active_choice < 0:
            self.active_choice = len(self.all_battle) - 1

    def _right(self):
        self.click = False
        self.active_choice += 1
        self.active_choice = self.active_choice % len(self.all_battle)

    def events(self, event):
        super().events(event)
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_LEFT:
                self._left()
            elif event.key == pg.K_RIGHT:
                self._right()
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 4:
                self._left()
            elif event.button == 5:
                self._right()
                
    def init(self):
        super().init()

        self.background = load_image("mainmenu.jpg").copy()
        self.active_choice = 0
        
        pad = 30
        boardw = WIDTH - 2 * pad
        boardh = HEIGHT - 2 * pad
        board = pg.Surface((boardw, boardh)).convert_alpha()
        board.fill((0, 0, 0, 150))
        pg.draw.rect(board, (255, 255, 0), (0, 0, boardw, boardh), width=1)
        self.background.blit(board, (pad, pad))

        self.battle_icons = []
        self.battle_tips = []
        for cls in self.all_battle:
            icon = load_image(cls.__name__[2:] + "_icon.png")
            icon_rect = icon.get_rect(centerx=WIDTH//2, centery=HEIGHT//3)
            self.battle_icons.append((icon, icon_rect))

            text = cls.DOC
            r = renders([(text[0], (255, 255, 255), 22), (text[1], (255, 255, 255), 14)],
                        pady=15, bg=(0, 0, 0, 0))
            self.battle_tips.append((r, r.get_rect(centerx=WIDTH//2, centery=HEIGHT*2//3)))

        self.click_surf = pg.Surface(icon_rect.size).convert_alpha()
        self.click_surf.fill((0, 0, 0, 0))
        pg.draw.circle(self.click_surf, (0, 0, 0, 50), (icon_rect.width//2, icon_rect.height//2), icon_rect.width//2)
        self.click_rect = icon_rect
        
        Button(self.buttons, (WIDTH - 42, HEIGHT - 42), "button_return.png",
               (_("返回"), _("点击回到主菜单")), self.do(self.quit_scene))
        Button(self.buttons, (150, HEIGHT//2), "button_left.png",
               None, self._left)
        Button(self.buttons, (WIDTH - 150, HEIGHT//2), "button_right.png",
               None, self._right)

        if not self.user["guide"][1]:
            bs = self.buttons.sprites()
            Guide(self.draw, [
                (CENTERINFO, (WIDTH*0.25, HEIGHT*3//4),
                 _("派对模式中，您无需担心自己的奖杯"), _("因为派对模式不会记录您的输赢"),
                 _("您可以滚动鼠标自行查看派对模式的其他玩法")),
                ((self.click_rect, pg.mask.from_surface(self.battle_icons[0][0])),
                 (WIDTH*0.6, HEIGHT*3//4),
                 _("点击进入战斗")),
                ], sendevent=self.events)
            self.user["guide"][1] = 1
            
    def draw(self):
        pos = pg.mouse.get_pos()
        
        self.screen.blit(self.background, (0, 0))

        self.screen.blit(self.battle_icons[self.active_choice][0],
                         self.battle_icons[self.active_choice][1])
        self.screen.blit(self.battle_tips[self.active_choice][0],
                         self.battle_tips[self.active_choice][1])

        if self.click_rect.collidepoint(pos):
            self.screen.blit(self.click_surf, self.click_rect)
            if self.click:
                self.click = False
                self.start_battle(self.all_battle[self.active_choice], False)
                self.quit_scene()
        
        super().draw()
        
class UnitManager(SceneWithButtons):
    def __init__(self, user):
        self.user = user
        super().__init__()

    def init(self):
        super().init()
        
        self.background = load_image("mainmenu.jpg").copy()
        self.active_unit = None

        self.pad = pad = 30
        self.tipboardw = tipboardw = 340
        boardw = WIDTH - 3 * pad - tipboardw
        boardh = HEIGHT - 2 * pad
        board = pg.Surface((boardw, boardh)).convert_alpha()
        board.fill((0, 0, 0, 150))
        pg.draw.rect(board, (255, 255, 0), (0, 0, boardw, boardh), width=1)
        self.background.blit(board, (pad, pad))

        tipboard = pg.Surface((tipboardw, boardh)).convert_alpha()
        tipboard.fill((0, 0, 0, 150))
        pg.draw.rect(tipboard, (255, 255, 0), (0, 0, tipboardw, boardh), width=1)
        self.background.blit(tipboard, (boardw + 2 * pad, pad))

        self.tipboard_tip_pos = (boardw + 2 * pad, pad)

        self.column_c = 8
        new_units = []
        for i, (en_name, value) in enumerate(sys.stdout.all_units.items()):
            if en_name not in self.user["all_units"] and self.user["score"] >= value[0]:
                self.user["all_units"].append(en_name)
                new_units.append(en_name)

        sys.stdout.all_units = dict(sorted(sys.stdout.all_units.items(),
                                           key=lambda x: (1 if x[0] in self.user["all_units"] else 0,
                                                          get_unit_grade(x[0])[0]),
                                           reverse=True))
    
        self.all_units = sys.stdout.all_units
        self.unit_tipboard_tips = []
        self.unit_rects = []
        for i, (en_name, value) in enumerate(self.all_units.items()):
            row = i // self.column_c
            column = i % self.column_c

            icon = get_unit_icon(en_name)
            icon_rect = pg.Rect((column*85+pad+40, row*85+pad+40, 65, 65))
            if en_name in new_units:
                self.play_fade_effect(icon_rect.center, load_image("lock.png"),
                                      fadein=1, keep=1, fadeout=50)
                
            if en_name not in self.user["all_units"]:
                icon = pg.transform.grayscale(icon)
                icon.blit(load_image("lock.png"), (0, 0))                
            
            self.unit_tipboard_tips.append(self.get_unit_tipboard_tip(tipboardw, boardh, en_name, icon,
                                                                      en_name in self.user["all_units"]))
            self.unit_rects.append(icon_rect)
            self.background.blit(icon, icon_rect)

            self.background.blit(render(str(value[2]), size=11),
                                 (column*85+pad+100, row*85+pad+90))

        self.update_wear_units()
        write_user(self.user)

        Button(self.buttons, (WIDTH - 42, HEIGHT - 42), "button_return.png",
               (_("返回"), _("点击回到主菜单")), self.onexit)
        Button(self.buttons, (42, HEIGHT - 42), "button_random_units.png",
               (_("随机卡组"), _("点击随机生成士兵卡组")), self.random_units,
               anchor="bottomleft")

        if not self.user["guide"][2] and len(self.user["all_units"]) > 8:
            bs = self.buttons.sprites()
            Guide(self.draw, [
                (CENTERINFO, (WIDTH*0.25, HEIGHT*2//3),
                 _("您可以在军营管理士兵卡组"), _("点击兵种的图标可以卸下/装备该兵种"),
                 _("部分兵种在达到一定要求后才能解锁")),
                (bs[1].info, (WIDTH*0.15, HEIGHT*3//4),
                 _("点击这个按钮可以随机生成卡组（虽然这没有必要）")),
                ], clicklimit=False)
            self.user["guide"][2] = 1

    def get_unit_tip(self, cn_name, doc):
        tip = renders([(cn_name, (255, 255, 255), 18),
                       (doc, (255, 255, 255), 13)], bg=(0, 0, 0, 150))
        return tip

    def get_unit_tipboard_tip(self, w, h, en_name, icon, locked):
        tip = pg.Surface((w, h)).convert_alpha()
        tip.fill((0, 0, 0, 0))
        value = self.all_units[en_name]

        name_r = render(value[1], size=18 if LANGUAGE == "zh" else 14)
        grade_r = load_image("g_" + get_unit_grade(en_name)[1] + ".png")
        pad = 30
        tip.blit(icon, (pad, pad))
        tip.blit(name_r, name_r.get_rect(x=64 + 2 * pad, centery=15 + pad))
        tip.blit(grade_r, grade_r.get_rect(x=64 + 2 * pad, centery=50 + pad))

        if not locked:
            r = renders([(_("未解锁"), (200, 200, 200), 20),
                         (_("奖杯数达到%d后解锁")%value[0], (255, 255, 255), 14)], pady=20, bg=(0, 0, 0, 0))
            tip.blit(r, r.get_rect(centerx=w//2, y=200))
        else:
            dictionary = {_("类型"):(_("战斗单位") if value[4] == "soldier" else _("法术")),
                          _("消耗能量"):value[2],
                          _("冷却时间"):value[5]}
            if value[4] == "soldier":
                dictionary.update({_("速度"):value[6],
                                   _("血量"):value[8],
                                   _("破阵伤害"):value[7]})
            else:
                dictionary.update({_("范围"):"%dx%d"%value[6]})

            for i, (k, v) in enumerate(dictionary.items()):
                tip.blit(render(str(k), color=(210, 210, 210), size=16), (pad, i * 24 + 124))
                tip.blit(render(str(v), size=14), (pad + 165, i * 24 + 124))

            tip.blit(render(value[3], size=15, wraplength=self.tipboardw-2*pad), (pad, i*24+200))

            if value[-1]:
                pady = (i+1) * 24 + 280
                cn_name, _tip, cost, maxfrozen = value[-1]

                tip.blit(load_image(en_name + "_skill_icon.png"), (pad, pady))
                r = render(str(cost), size=11)
                tip.blit(r, r.get_rect(x=pad+50, y=pady+50))
                r = render(_("附加技能: ") + cn_name, size=16)
                tip.blit(r, r.get_rect(x=2*pad+55, centery=pady+25))

                tip.blit(render(value[3], size=15, wraplength=self.tipboardw-2*pad), (pad, pady+70))
        
        return tip

    def update_wear_units(self):
        self.wear_unit_rects = []
        for i, (en_name, value) in enumerate(self.all_units.items()):
            row = i // self.column_c
            column = i % self.column_c
            if en_name in self.user["wear_units"]:
                icon_rect = pg.Rect((column*85+self.pad+40, row*85+self.pad+40, 65, 65))
                self.wear_unit_rects.append(icon_rect)
                
    def random_units(self):
        self.user["wear_units"] = random.sample(self.user["all_units"], 8)
        self.update_wear_units()
        write_user(self.user)

    def onexit(self):
        if len(self.user["wear_units"]) != 8:
            self.show_tip(_("军队数量不足"))
        else:
            super().onexit()
            
    def draw(self):
        self.screen.blit(self.background, (0, 0))
        pos = pg.mouse.get_pos()

        for rect in self.wear_unit_rects:
            self.screen.blit(load_image("wore.png"), rect)
            
        for i, rect in enumerate(self.unit_rects):
            if rect.collidepoint(pos):
                self.active_unit = i
                if self.click:
                    self.click = False
                    en_name = tuple(self.all_units.keys())[i]
                    if rect in self.wear_unit_rects:
                        self.user["wear_units"].remove(en_name)
                        self.wear_unit_rects.remove(rect)
                        write_user(self.user)
                    else:
                        if en_name in self.user["all_units"]:
                            if len(self.user["wear_units"]) < 8:
                                self.user["wear_units"].append(en_name)
                                self.wear_unit_rects.append(rect)
                                write_user(self.user)
                            else:
                                self.show_tip(_("军队数量已达上限"))
                        else:
                            self.show_tip(_("未解锁"))
                            
                break
            
        if self.active_unit != None:
            self.screen.blit(self.unit_tipboard_tips[self.active_unit], self.tipboard_tip_pos)

        super().draw()

class Menu(SceneWithButtons):
    def __init__(self):
        setattr(sys.stdout, "all_units", {})
        for cls in dir(units):
            if cls.startswith("c_"):
                try:
                    eval(cls)(None, {})
                except TypeError as e:
                    try:
                        eval(cls)(None)
                    except AttributeError as e:
                        pass
                except AttributeError as e:
                    pass

        super().__init__()
        
    def init(self):
        super().init()
        
        pg.mouse.set_cursor(pg.cursors.Cursor((0, 0), load_image("cursor.png")))
        self.background = load_image("mainmenu.jpg")

        self.all_sprites = pg.sprite.Group()
        self.user = load_user()
        
        Button(self.buttons, (WIDTH*0.25, HEIGHT//2), "button_battle.png",
               (_("战地"), _("点击匹配对手")), self.do(self.start_battle))
        Button(self.buttons, (WIDTH*0.5, HEIGHT//2), "button_party.png",
               (_("派对 !"), _("点击参加更多玩法")), self.do(Party, self.user, self.start_battle))
        Button(self.buttons, (WIDTH*0.75, HEIGHT//2), "button_manager.png",
               (_("军营"), _("点击管理军队卡牌")), self.do(UnitManager, self.user))
        Button(self.buttons, (42, HEIGHT - 42), "button_log.png",
               (_("日志"), _("点击查看游戏日志信息，请及时向创作者反馈遇到的bug")),
               self.load_log, anchor="bottomleft")
        Button(self.buttons, (WIDTH - 116, HEIGHT - 42), "button_info.png",
               (_("信息"), _("点击查看游戏创作者及素材来源")), self.do(Credits, self.user))
        Button(self.buttons, (WIDTH - 42, HEIGHT - 42), "button_exit.png",
               (_("退出"), _("点击离开游戏")), sys.exit)

        self.ai_units = []
        for cn_name, v in sys.stdout.all_units.items():
            self.ai_units.append([cn_name, v[0]])

        if not self.user["guide"][0]:
            bs = self.buttons.sprites()
            g = [
                (CENTERINFO, (WIDTH*0.25, HEIGHT*2//3),
                 _("欢迎您，新玩家！"), _("在开始游戏之前，我们认为您需要一些教程")),
                (bs[0].info, (WIDTH*0.25, HEIGHT*2//3),
                 _("这里是战场，您可以在这里匹配对手")),
                ]
            Guide(self.draw, g)
            
            self.start_battle(battle=battle_fun.GuideBattle)
            self.user["guide"][0] = 1
            write_user(self.user)

    def __score_text(self, text):
        return load_image("cup.png"), "  " + text
    
    def _command_win(self, battle):
        score_before = self.user["score"]
        
        self.user["score"] += random.randint(6, 11) * battle.difficulty * 1000
        write_user(self.user)
        
        return self.__score_text("%d -> %d"%(score_before, self.user["score"]))

    def _command_lose(self, battle):
        score_before = self.user["score"]
        self.user["score"] -= random.randint(6, 11) * (0.01 - battle.difficulty) * 1000

        if self.user["score"] >= 0:
            write_user(self.user)
            
            return self.__score_text("%d -> %d"%(score_before, self.user["score"]))
        else:
            self.user["score"] = 0
            write_user(self.user)
            
            return self.__score_text("%d -> 0"%score_before)

    def _command_same(self, battle):
        return self.__score_text("%d -> %d"%(self.user["score"], self.user["score"]))
    
    def load_log(self):
        try:
            os.startfile(os.getcwd()+"/debug.log")
        except OSError:
            self.show_tip(_("无日志记录"))
            
    def start_battle(self, battle=Battle, score=True):
        if len(self.user["wear_units"]) != 8:
            self.show_tip(_("军队数量不足"))
            return

        r_units = []
        random.shuffle(self.ai_units)
        ai_cup = self.user["score"] + random.randint(-50, 200)
        if random.random() > 0.7:
            ai_cup += random.randint(-50, 500)
        if ai_cup < 0:
            ai_cup = 0
        for cn_name, cup in self.ai_units:
            if cup <= ai_cup:
                r_units.append(cn_name)
                if len(r_units) == 8:
                    break
        else:
            r_units = random.sample(list(sys.stdout.all_units), 8)
        
        a = ([self.user["score"], ai_cup],
             self.user["wear_units"],
             r_units,
             random.uniform(0.003, 0.01))
        if score:
            battle(*a, self._command_win, self._command_lose, self._command_same)
        else:
            battle(*a)
            
    def update(self):
        super().update()
        for sprite in self.all_sprites:
            sprite.animate()
    
    def draw(self):
        self.screen.blit(self.background, (0, 0))
        self.all_sprites.draw(self.screen)

        super().draw()
    
if __name__ == "__main__":
    pg.init()
    pg.display.set_mode((WIDTH, HEIGHT))
    Menu()
