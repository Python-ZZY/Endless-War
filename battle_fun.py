import pygame as pg
import random
from configs import *
from battle import *
from guide import *

all_battle_list = {}

class GuideBattle(Battle):
    def init(self):
        super().init()
        self.l_money = self.r_money = 15
        self.unit_icons[0].frozen_to = 0
        self.update_pbar()

        w = WIDTH
        n = pg.time.get_ticks()
        Guide(self.draw, [
            ([pg.Rect(0, 0, 0, 0),
              pg.Mask((w//3, self.action_bar_height), fill=1)],
             (100, self.action_bar_height+30),
             _("这里是操作区，您可以选择士兵并派出他们")),
            ([pg.Rect(w//3, 0, 0, 0),
              pg.Mask((w//3, self.action_bar_height), fill=1)],
             (w//3+100, self.action_bar_height+30),
             _("这里显示对局的提示信息")),
            ([pg.Rect(w//3, 20, 0, 0),
              pg.Mask((w//3, load_image("bar.png").get_height()//2), fill=1)],
             (w//3+100, self.action_bar_height),
             _("红条指示血量，当士兵攻过对方的阵线底部将会对敌方造成伤害")),
            ([pg.Rect(w//3, 20+load_image("bar.png").get_height()//2, 0, 0),
              pg.Mask((w//3, load_image("bar.png").get_height()//2), fill=1)],
             (w//3+100, self.action_bar_height),
             _("蓝条指示能量，派出士兵将会消耗能量")),
            ([pg.Rect(w//3, self.action_bar_height//2, 0, 0),
              pg.Mask((w//3, self.action_bar_height//2), fill=1)],
             (w//3+100, self.action_bar_height),
             _("部分兵种具有附带技能，不要忘记使用！")),
            ([pg.Rect(0, 0, 0, 0),
              pg.Mask((w//3, self.action_bar_height), fill=1)],
             (100, self.action_bar_height+30),
             _("每个士兵卡牌右下角的数字提示士兵所需的能量")),
            ([pg.Rect(40, 11, 0, 0),
              pg.Mask((65, 65), fill=1)],
             (100, self.action_bar_height+30),
             _("现在，尝试选中一位士兵！")),
            ], sendevent=self.events)
        self.time_offset += pg.time.get_ticks() - n

        n = pg.time.get_ticks()
        Guide(self.draw, [
            ([pg.Rect(0, self.action_bar_height+self.roadheight*2, 0, 0),
              pg.Mask((w, self.roadheight*2), fill=1)],
             (100, self.action_bar_height*2+self.roadheight*2+30),
             _("非常好！现在选择一条道路派出士兵（注意士兵是不能走到别的道路上的）")),
            ], sendevent=self.events)
        self.time_offset += pg.time.get_ticks() - n

        self.showguide = 0
        self.start_guide_time = pg.time.get_ticks()

    def update(self):
        super().update()

        if self.showguide == 0 and pg.time.get_ticks() - self.start_guide_time > 3000:
            n = pg.time.get_ticks()
            Guide(self.draw, [
                (CENTERINFO,
                 (100, self.action_bar_height*2+self.roadheight*2+30),
                 _("您可以滚动鼠标或使用方向键滚动地图")),
                ([self.minimap_rect,
                  pg.mask.Mask(self.minimap_rect.size, fill=1)],
                 (self.minimap_rect.x-100, self.minimap_rect.y-50),
                 _("也可以直接在小地图上选中区域"), _("尝试让士兵突破对方的阵线")),
                ], clicklimit=False)
            t = pg.time.get_ticks() - n
            self.time_offset += t
            self.start_guide_time += t
            self.showguide += 1
        elif self.showguide == 1 and pg.time.get_ticks() - self.start_guide_time > 10000:
            n = pg.time.get_ticks()
            Guide(self.draw, [
                (CENTERINFO,
                 (100, self.action_bar_height*2+self.roadheight*2+30),
                 _("游戏进行时，您可以随时按下P键暂停游戏")),
                ], clicklimit=False)
            t = pg.time.get_ticks() - n
            self.time_offset += t
            self.start_guide_time += t
            self.showguide += 1
    
class fallingSpellBattle(Battle):
    def init(self):
        super().init()
        self.last_falling = 0
        self.count = 10

    def getdelta(self):
        return 8000 - pg.math.clamp(self.period, 0, 2) * 2000
    
    def update(self):
        super().update()
        now = self.timer
        
        if now - self.last_falling > self.getdelta():
            self.last_falling = now
            
            for i in range(self.count):
                spell = random.choice(self.all_spells)
                self.add_spell(spell, "l", (random.randint(0, self.background_width),
                                             random.randint(self.action_bar_height, HEIGHT)))
                self.add_spell(spell, "r", (random.randint(0, self.background_width),
                                             random.randint(self.action_bar_height, HEIGHT)))

class fallingSoldierBattle(Battle):
    def init(self):
        super().init()
        self.last_falling = 0
        self.order = ["l", "r"]

    def getdelta(self):
        return 10000 - pg.math.clamp(self.period, 0, 2) * 2000
        
    def update(self):
        super().update()
        now = self.timer
        
        if now - self.last_falling > self.getdelta():
            self.last_falling = now
            soldier = random.choice(self.all_soldiers)
            
            for i in range(self.maxroad+1):
                self.add_soldier(soldier, self.order[0], i)
                self.add_soldier(soldier, self.order[1], i)
            self.order = self.order[::-1]

class b_barricade_battle(Battle):
    DOC = (_("层层设防模式"), _("战场上栅栏数量增加"))
    def init(self):
        super().init()
        for i in range(self.maxroad//2+1):
            unit = self.add_soldier("barricade", "l", road=i*2+1, startswith="cs_")
            unit.health = unit.maxhealth = 220
            self.barricades.add(unit)
            self.soldiers[i*2].add(unit)
            unit.moveto("centerx", 500)
            
            unit = self.add_soldier("barricade", "r", road=i*2+1, startswith="cs_")
            unit.health = unit.maxhealth = 220
            self.barricades.add(unit)
            self.soldiers[i*2].add(unit)
            unit.moveto("centerx", self.background_width-500)

            camp = "l" if i % 2 == 0 else "r"
            unit = self.add_soldier("barricade", camp, road=i*2+1, startswith="cs_")
            unit.health = unit.maxhealth = 220
            self.barricades.add(unit)
            self.soldiers[i*2].add(unit)
            unit.moveto("centerx", 1100 if camp == "l" else self.background_width-1100)

class b_classic(fallingSoldierBattle):
    DOC = (_("经典模式"), _("融合多种玩法的公平战斗模式"))
    def init(self):
        super().init()
        self.all_soldiers = ["soldier", "bow_infantry"]

    def getdelta(self):
        return 7000
    
    def update(self):
        if "golem" not in self.all_soldiers and self.period > 1:
            self.all_soldiers += ["cannon", "light_cavalry", "golem"]
            
        super().update()
        
    def add_soldier(self, name, camp, road, startswith="c_", money=0):
        sprite = super().add_soldier(name, camp, road, startswith, money)

        if self.period > 1 and "master" not in name:
            inf = float("inf")
            sprite.do_increase("speed", 0.5, inf)
            sprite.do_increase("attack_delta", -0.3, inf)
            sprite.do_increase("frame_delta", -0.3, inf)
            if name != "barricade":
                sprite.cover_color((255, 0, 255, 80), inf)

        return sprite
    
class b_double_energy(Battle):
    DOC = (_("双倍能量对战"), _("获得能量的速度翻倍"))
    def init(self):
        super().init()
        self.money_got[1] *= 2

class b_energy_party(fallingSoldierBattle):
    DOC = (_("能量狂欢"), _("获得能量的速度翻倍，每经过10秒双方各自派出一排能量精灵"))
    def init(self):
        super().init()
        self.difficulty += 0.001
        self.money_got[1] *= 2
        self.all_soldiers = ["energy_sprite"]

    def getdelta(self):
        return 10000
    
class b_falling_barbarian(fallingSoldierBattle):
    DOC = (_("蛮兵入侵"), _("每过一段时间，双方各自派出一排野蛮人士兵，蛮兵具有比普通士兵更强的战斗力"))
    def init(self):
        super().init()     
        self.period_events[2][1] = _("倒计时180秒  野蛮象兵加入战场")
        self.all_soldiers = ["cs_barbarian_soldier", "cs_barbarian_bow_infantry",
                             "cs_barbarian_light_dagger_infantry"]

    def update(self):
        if "elephant_rider" not in self.all_soldiers and self.period > 1:
            self.all_soldiers.append("elephant_rider")
            
        super().update()
            
class b_falling_bomb(fallingSpellBattle):
    DOC = (_("随机轰炸模式"), _("每过一段时间，战场上就会落下20颗霹雳弹"))
    def init(self):
        super().init()
        self.all_spells = ["bomb"]

    def getdelta(self):
        return 8000 - pg.math.clamp(self.period, 0, 3) * 1000
        
class b_falling_catapult(fallingSoldierBattle):
    DOC = (_("战斗机器世界"), _("每经过25秒，双方各自派出一排攻城弩、投石车、加农炮或黄金加农炮"))
    def init(self):
        super().init()
        self.all_soldiers = ["ballista", "catapult", "cannon", "gold_cannon"]

    def getdelta(self):
        return 25000

class b_falling_clone(fallingSpellBattle):
    DOC = (_("克隆战场"), _("每过一段时间，随机克隆20个区域"))
    def init(self):
        super().init()
        self.all_spells = ["clone"]
        
class b_falling_freeze_fire(fallingSpellBattle):
    DOC = (_("冰火二重天"), _("每过一段时间，随机冰冻或燃烧10个区域"))
    def init(self):
        super().init()

        self.all_spells = ["freeze", "fire"]
        self.count = 5
    
class b_falling_soldiers(fallingSoldierBattle):
    DOC = (_("战斗乐园"), _("每过一段时间，双方各自派出一排战兵、弓箭手、盾兵、矛兵或超级士兵"))
    def init(self):
        super().init()

        self.all_soldiers = ["soldier", "bow_infantry", "shielded_sword_infantry",
                             "elite_spear_infantry", "dragon_infantry"]

class b_falling_masters(fallingSoldierBattle):
    DOC = (_("法师派对"), _("每过一段时间，双方各自派出一排雷电法师、寒冰法师、飓风法师或五行战士"))
    def init(self):
        super().init()

        self.all_soldiers = ["lightning_master", "ice_master", "wind_master", "powerful_master"]

    def getdelta(self):
        return 14000 - pg.math.clamp(self.period, 0, 2) * 2000

class b_fog_battle(fallingSpellBattle):
    DOC = (_("迷雾之地"), _("远程攻击类兵种精准度变差，且会定时落下闪电"))
    def init(self):
        super().init()
        self.all_spells = ["thunder"]

        self.mm.stop()
        self.mm = MusicManager(music_formats=["_spooky"])
        pg.mixer.music.set_volume(0.6)

        self.battle_projectile_offset = "uniform(0.75, 1.01)"
        
        surf = pg.Surface((self.background_width, HEIGHT)).convert_alpha()
        surf.fill((128, 0, 128, 100))
        self.background.blit(surf, (0, 0))

        self.fog_image = load_image("bg_dec_fog.png").convert_alpha()
        
    def draw(self):
        super().draw()
        self.screen.blit(self.fog_image, self.pos(0, self.action_bar_height))
    
class b_rage_battle(Battle):
    DOC = (_("狂暴对战"), _("所有士兵（除法师）将持续处于狂暴状态"))
    def init(self):
        super().init()

        surf = pg.Surface((self.background_width, HEIGHT)).convert_alpha()
        surf.fill((255, 0, 255, 30))
        self.background.blit(surf, (0, 0))
        
    def add_soldier(self, name, camp, road, startswith="c_", money=0):
        sprite = super().add_soldier(name, camp, road, startswith, money)

        if "master" not in name:
            inf = float("inf")
            sprite.do_increase("speed", 0.5, inf)
            sprite.do_increase("attack_delta", -0.3, inf)
            sprite.do_increase("frame_delta", -0.3, inf)
            if name != "barricade":
                sprite.cover_color((255, 0, 255, 80), inf)

        return sprite
