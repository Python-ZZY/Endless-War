import pygame as pg
import sys
from menu import Loading, Menu
from configs import *

class Stderr:
    def write(self, s, error=""):
        with open("debug.log", "a") as f:
            f.write(error + s)

if __name__ == "__main__":
    try:
        import pyi_splash
        pyi_splash.close()
    except:
        pass
    
    pg.init()
    pg.mixer.set_num_channels(16)
    pg.display.set_caption(APPNAME)
    pg.display.set_icon(load_image("icon.ico"))
    pg.display.set_mode((WIDTH, HEIGHT), pg.SCALED, vsync=1)
    sys.stderr = Stderr()

    _loading = True
    if _loading:
        Loading()
    Menu()
