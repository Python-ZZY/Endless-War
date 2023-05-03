import pygame as pg
import math
from configs import *
from base import *

CENTER = pg.Rect(0, 0, 0, 0)
CENTER.center = (WIDTH//2, HEIGHT//2)
CENTERINFO = (CENTER, None)

class Guide(Scene):
    def __init__(self, draw, guide, clicklimit=True, sendevent=False):
        self.draw_func = draw
        self.clicklimit = clicklimit
        self.sendevent = sendevent
        self.mm = MusicManager()

        self.guide = []
        
        self.fade_pos = 1
        self.fade_incr = 0.1
        self.index = 0
        self.last_update_fade = 0
        self.bg_mask = pg.mask.Mask((WIDTH, HEIGHT), fill=True)
        
        for i, ((rect, mask), tip_pos, *texts) in enumerate(guide):
            for text in texts:
                self.guide.append((vec(rect.topleft), mask, tip_pos, text))
            if i == (len(guide) - 1) and self.clicklimit:
                if mask == None:
                    self.clicklimit = False
                    continue
                self.click_tip = load_image("click_tip.png")
                if (cy := (rect.y + mask.get_size()[1]/2)) < HEIGHT // 2:
                    self.click_tip = pg.transform.flip(self.click_tip, False, True)
                    y = cy + mask.get_size()[1]/2 + 30
                else:
                    y = cy - mask.get_size()[1]/2 - load_image("click_tip.png").get_height() - 30
                self.clicklimit = (rect.x+mask.get_size()[0]//2-load_image("click_tip.png").get_width()//2,
                                   y)

        self.guide.append([False])
        self.now_area, self.next_area = self.guide[self.index][0], self.guide[self.index][0]
        self.update_fade()
                
        super().__init__()

    def update_index(self):
        self.now_area, self.next_area = self.guide[self.index][0], self.guide[self.index+1][0]
        if self.next_area == False:
            if (self.clicklimit and self.guide[self.index][1].overlap(pg.Mask((1, 1), fill=True),
                                                                      vec(pg.mouse.get_pos())-self.now_area)) or \
                                                                      (not self.clicklimit):
                self.quit_scene()
                if self.sendevent:
                    self.sendevent(pg.Event(pg.MOUSEBUTTONDOWN, button=1, pos=pg.mouse.get_pos()))
            else:
                self.index -= 1
                self.fade_pos = 1
        else:
            play_sound("button_click")
            
    def update_fade(self):
        try:
            fg_pos = self.now_area.lerp(self.next_area, self.fade_pos)
        except TypeError as e:
            raise ValueError(str(self.next_area)+" "+str(self.fade_pos)) from e
        self.fg = self.bg_mask.copy()
        if m := self.guide[self.index][1]:
            self.fg.invert()
            self.fg.draw(m, fg_pos)
            self.fg.invert()
        self.fg = self.fg.to_surface(setcolor=(0, 0, 0, 150), unsetcolor=(0, 0, 0, 0))
        self.fg.blit(render(self.guide[self.index][3], size=17, wraplength=350),
                     self.guide[self.index][2])

    def onexit(self):
        self.events(pg.Event(pg.MOUSEBUTTONDOWN, button=1))
    
    def events(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.fade_pos == 1:
                self.fade_pos = 0
                self.update_index()
                self.index += 1
            
    def draw(self):
        self.draw_func()
        self.screen.blit(self.fg, (0, 0))
        if self.clicklimit and self.index == len(self.guide)-2:
            self.screen.blit(self.click_tip, (self.clicklimit[0],
                                              self.clicklimit[1]+3*math.sin(pg.time.get_ticks()**0.5)))

    def update(self):
        self.mm.update()
        now = pg.time.get_ticks()

        if self.fade_pos != 1:
            if now - self.last_update_fade > 20:
                self.last_update_fade = now
                self.fade_pos += self.fade_incr
                if self.fade_pos > 1:
                    self.fade_pos = 1
                self.update_fade()
