from functools import lru_cache
import pygame as pg
import os
import random
import sys

import gettext

os.environ["SDL_IME_SHOW_UI"] = "1"
pg.mixer.pre_init()
pg.mixer.init()

WIDTH = 1200
HEIGHT = 650

def path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.normpath(os.path.join(base_path, relative_path))

def load_anm(name):
    anms = []
    num = 1
    base_path = path("assets/"+name)

    if "{}" not in base_path:
        return [base_path]
    
    while True:
        pth = base_path.format(num)
        
        if not os.path.exists(pth):
            break

        anms.append(pth)  
        num += 1

    return anms

@lru_cache(300)
def load_image(name, scale=None, flip=None):
    try:
        if "\\" not in name:
            surf = pg.image.load(path("assets/"+name))
        else:
            surf = pg.image.load(name)
    except TypeError:
        return name

    if scale:
        surf = pg.transform.scale(surf, scale)
    if flip:
        surf = pg.transform.flip(surf, *flip)
        
    return surf

def load_images(name, **kw):
    try:
        return [load_image(anm, **kw) for anm in load_anm(name)]
    except TypeError:
        return [name]

@lru_cache(1)
def load_font(size, name="fnt"):
    return pg.font.Font(path("assets/"+name+".ttf"), size)

@lru_cache(256)
def render(text, color=(255, 255, 255), size=19, wraplength=WIDTH):
    return load_font(size).render(text, True, color, None, wraplength)
                
def with_image_render(texts, color=(255, 255, 255), size=19, wraplength=WIDTH):
    if isinstance(texts, str):
        return render(texts, color, size)
    
    rs = []
    w, h = 0, 0
    for r in texts:
        if isinstance(r, pg.Surface):
            rs.append(r)
        else:
            r = render(r, color, size, wraplength)
            rs.append(r)
        w += r.get_width()
        h = max((h, r.get_height()))

    surf = pg.Surface((w, h)).convert_alpha()
    surf.fill((0, 0, 0, 0))
    w = 0
    for r in rs:
        surf.blit(r, (w, 0))
        w += r.get_width()

    return surf
    
def renders(texts, pady=5, bg=(0, 0, 0, 0), r=render):
    try:
        wsizes = [load_font(size).size(text)[0] for text, _, size in texts]
        hsizes = [load_font(size).size("")[1]+pady for _, _, size in texts]
    except TypeError as e:
        raise ValueError(texts) from e
    
    surf = pg.Surface((max(wsizes), sum(hsizes))).convert_alpha()
    surf.fill(bg)
    
    for i, (text, color, size) in enumerate(texts):
        surf.blit(r(text, color, size), ((surf.get_size()[0]-wsizes[i])//2, sum(hsizes[:i])))

    return surf

@lru_cache()
def load_sound(name):
    return pg.mixer.Sound(path(name))

def play_sound(name, filetype="ogg"):
    load_sound("assets/"+name+"."+filetype).play()

class MusicManager:
    def __init__(self, music=path("assets/bgm{}.ogg"), music_formats=["1", "2"]):
        self.music = music
        self.music_formats = music_formats
        self.idx = 0
        self.running = True
        random.shuffle(self.music_formats)

    def update(self):
        if not pg.mixer.music.get_busy() and self.running:
            pg.mixer.music.load(self.music.format(self.music_formats[self.idx]))
            pg.mixer.music.play()

            self.idx += 1
            if self.idx == len(self.music_formats):
                self.idx = 0

    def stop(self):
        self.running = False
        pg.mixer.music.fadeout(500)

LANGUAGE = "en" if pg.system.get_pref_locales()[0]["language"] != "zh" else "zh"
t = gettext.translation(LANGUAGE, path("locale/"), languages=[LANGUAGE], fallback=True)
t.install(LANGUAGE)
_ = t.gettext

vec = pg.Vector2

APPNAME = _("战争风云")
VERSION = "Alpha 1.4"
CREDITS = f"""
战争风云  ENDLESS WAR

版本 VERSION: {VERSION}

游戏作者: Python-ZZY (pythonzzy@foxmail.com)
Created by Python-ZZY

itch: https://python-zzy-china.itch.io/

github: https://github.com/Python-ZZY/

贡献者: WuxiaScrub (素材/游戏设计)
Contributor: WuxiaScrub (Game Assets/Game Design)
itch: https://wuxia-scrub.itch.io/

此游戏的卡组设计仿照SUPERCELL的《皇室战争》游戏
The game's character design is modeled after SUPERCELL's Clash Royale game

主要素材来源如下网站，感谢游戏素材的提供者
Most assets comes from the following websites. Thank you to the creators of the assets.
https://opengameart.org/
https://game-icons.net/
https://www.aigei.com/
https://sanderfrenken.github.io/Universal-LPC-Spritesheet-Character-Generator/

更多版权信息如下:
More credits:
Stephen "Redshrike" Challener, William.Thompsonj
[LPC] Siege Weapons by bluecarrot16 (https://opengameart.org/content/lpc-siege-weapons)
https://www.aigei.com/view/70413.html
https://www.aigei.com/view/73194.html

BGM:
orcs-victorious (opengamearg.org)
battle-music (soundcloud.com/alexandr-zhelanov)
spooky-enchantment (soundimage.org)

素材源于网络
如有侵权行为请联系作者
Game assets come from the Internet.
If your credit is required, please contact the creator!!

此游戏使用Python + Pygame制作
Made with Python + Pygame

感谢游玩！
Thanks for playing!
""".replace("\n\n", "\n"*8)
GAMETIPS = [
    _("战斗胜利会获得一定奖杯，失败会扣除一定奖杯（派对模式除外）"),
    _("部分兵种具有附带技能，无需派出该兵种即可使用"),
    _("投石车、攻城弩、黄金加农炮只能攻击距离较远的目标"),
    _("法师类兵种血量较低，但狂暴后很厉害"),
    _("使用飓风将攻击距离较远的兵种卷到栅栏处，可以使栅栏对其造成伤害"),
    _("法术无法伤害栅栏"),
    _("按P键可以暂停战斗"),
    ]
