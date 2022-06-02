# -*- coding: utf-8 -*-
import csv
import os
from time import sleep

import pygame
from sys import exit
from pygame.locals import *
import random

# 设置游戏屏幕大小
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
ALL_CARDS = {}


# 环境类
class EnvInt():
    # 初始化
    def __init__(self):
        self.process_data = True  # 数据处理标识位
        self.op_delay_kb = 20  # 键盘两次操作之间的间隔（防止一直按下去的连击）
        self.op_delay_mo = 10  # 鼠标两次操作之间的间隔（防止一直按下去的连击）
        self.turn = 0  # 当前回合数
        self.our_energy = 3  # 我方能量
        self.our_cards_num = 6  # 我方卡牌数量
        self.enm_energy = 3  # 敌方能量
        self.enm_cards_num = 6  # 敌方卡牌数量

    def end_turn(self):
        self.our_energy += 2
        if self.our_energy > 10:
            self.our_energy = 10
        self.our_cards_num = 3
        self.enm_energy += 2
        if self.enm_energy > 10:
            self.enm_energy = 10
        self.enm_cards_num = 3
        self.turn += 1


# 玩家怪物类
class Axie(pygame.sprite.Sprite):
    def __init__(self, axie_img, axie_rect, init_pos):
        pygame.sprite.Sprite.__init__(self)
        self.image = []  # 用来存储axie图片的列表
        for i in range(len(axie_rect)):
            self.image.append(axie_img.subsurface(axie_rect[i]).convert_alpha())
        self.rect = axie_rect[0]  # 初始化图片所在的矩形
        self.rect.topleft = init_pos  # 初始化矩形的左上角坐标
        self.skills = self.get_skills()  # 初始化axie的技能
        self.cards_num = 0  # 初始化axie拥有的卡牌数量
        self.cards = []  # 初始化axie拥有的卡牌
        self.cards_att = []  # 初始化要出的卡牌
        self.hp = random.randint(300, 500)  # 血量随机值
        self.defence = 0  # 防御
        self.speed = random.randint(1, 1000)  # 进攻速度随机值
        self.rank = -1  # 攻击顺序

    def get_skills(self):
        get_cards = {}
        card_num = [random.randint(0, 131) for _ in range(4)]
        for _num in card_num:
            get_cards[_num] = ALL_CARDS[_num]
        return get_cards


class AxieGameInt():
    # 初始化 pygame
    def __init__(self):
        pygame.init()

        # 设置游戏界面大小、背景图片及标题
        # 游戏界面像素大小
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

        # 游戏界面标题
        pygame.display.set_caption('AXIE山寨游戏')

        # 背景图
        self.background = pygame.image.load('resources/image/background1280x720.png').convert()

        # Game Over 的背景图
        self.game_over = pygame.image.load('resources/image/background1280x720.png')

        # 我方怪物图片
        our_axie_img = pygame.image.load('resources/image/our_axie_1.png')
        # pygame.image.load('resources/image/our_axie_2.png'),
        # pygame.image.load('resources/image/our_axie_3.png')]
        # 敌方怪物图片
        enm_axie_img = pygame.image.load('resources/image/enm_axie_1.png')

        # end_turn图片
        end_turn_img = pygame.image.load('resources/image/end_turn.png')

        # 初始化我方AXIE
        self.our_axie = []
        self.our_axie_rect = [[], [], []]
        for _i in range(3):
            our_axie_pos = [20 + _i * 200, 300]  # 初始位置
            self.our_axie_rect[_i].append(pygame.Rect(0, 0, 150, 100))  # 正常axie图片  left , top, width, height
            self.our_axie_rect[_i].append(pygame.Rect(160, 0, 70, 100))  # 死亡图片
            self.our_axie.append(Axie(our_axie_img, self.our_axie_rect[_i], our_axie_pos))

        # 初始化敌方AXIE
        self.enm_axie = []
        self.enm_axie_rect = [[], [], []]
        for _i in range(3):
            enm_axie_pos = [700 + _i * 200, 300]  # 初始位置
            self.enm_axie_rect[_i].append(pygame.Rect(0, 0, 150, 100))  # 正常axie图片  left , top, width, height
            self.enm_axie_rect[_i].append(pygame.Rect(160, 0, 70, 100))  # 死亡图片
            self.enm_axie.append(Axie(enm_axie_img, self.enm_axie_rect[_i], enm_axie_pos))

        # 设置end_turn图片
        self.end_turn_rect = pygame.Rect(0, 0, 155, 55)
        self.end_turn_img = end_turn_img.subsurface(self.end_turn_rect)

        # # 存储我方axie，管理多个对象
        # self.our_axie_group = pygame.sprite.Group()
        #
        # # 存储敌方axie，管理多个对象
        # self.enm_axie_group = pygame.sprite.Group()

        # 初始化环境信息（回合数、敌我能量）
        self.env = EnvInt()

        # 游戏循环帧率设置
        self.clock = pygame.time.Clock()

        # 判断游戏循环退出的参数
        self.running = True


def load_axie_skill():
    module_path = os.path.dirname(__file__) + '/resources/csv'
    csv_path = module_path + './cards.csv'
    axie_skill = {}
    # print(csv_path)  #去打印。
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            axie_skill[int(row[0])] = {
                'name': row[1],
                'energy': row[2],
                'class': row[3],
                'part': row[4],
                'att_type': row[5],
                'att': row[6],
                'def': row[7],
                'att_enable': row[8],
                'def_enable': row[9],
                'combo': row[10],
                'garbage': row[11],
                'description': row[12],
            }
    # print(axie_skill)
    return axie_skill


def get_att_seq(axie_int):
    att_seq = []
    for _i in range(3):  # 把所有存活怪物的速度加入对比队列
        if axie_int.our_axie[_i].hp > 0:
            att_seq.append(axie_int.our_axie[_i].speed)
        if axie_int.enm_axie[_i].hp > 0:
            att_seq.append(axie_int.enm_axie[_i].speed)
    att_seq.sort()  # 从大到小排序
    for _i in range(3):  # 获得排位即攻击顺序，死亡怪物计-1不参与排序
        if axie_int.our_axie[_i].hp > 0:
            axie_int.our_axie[_i].rank = att_seq.index(axie_int.our_axie[_i].speed)
        else:
            axie_int.our_axie[_i].rank = -1
        if axie_int.enm_axie[_i].hp > 0:
            axie_int.enm_axie[_i].rank = att_seq.index(axie_int.enm_axie[_i].speed)
        else:
            axie_int.enm_axie[_i].rank = -1


def get_random_cards(axie_int):
    """
    随机分配卡牌
    """
    our_axie_pos = [x for x in range(3) if axie_int.our_axie[x].hp > 0]
    enm_axie_pos = [x for x in range(3) if axie_int.enm_axie[x].hp > 0]
    for _i in range(axie_int.env.our_cards_num):
        random_pos = random.randint(0, len(our_axie_pos) - 1)
        axie_int.our_axie[our_axie_pos[random_pos]].cards_num = \
            len(axie_int.our_axie[our_axie_pos[random_pos]].cards) + 1
        axie_int.our_axie[our_axie_pos[random_pos]].cards = \
            axie_int.our_axie[our_axie_pos[random_pos]].cards + \
            random.sample(axie_int.our_axie[our_axie_pos[random_pos]].skills.keys(), 1)

        random_pos = random.randint(0, len(enm_axie_pos) - 1)
        axie_int.enm_axie[enm_axie_pos[random_pos]].cards_num = \
            len(axie_int.enm_axie[enm_axie_pos[random_pos]].cards) + 1
        axie_int.enm_axie[enm_axie_pos[random_pos]].cards = \
            axie_int.enm_axie[enm_axie_pos[random_pos]].cards + \
            random.sample(axie_int.enm_axie[enm_axie_pos[random_pos]].skills.keys(), 1)


def game_display(axie_int):
    # 游戏主循环
    # 控制游戏最大帧率为 60
    axie_int.clock.tick(60)

    # 绘制背景
    axie_int.screen.fill(0)
    axie_int.screen.blit(axie_int.background, (0, 0))

    # 绘制end_turn
    axie_int.screen.blit(axie_int.end_turn_img, (550, 50))

    # 绘制回合
    round_font = pygame.font.Font(None, 48)
    turn_text = round_font.render('Round: ' + str(axie_int.env.turn), True, (128, 128, 128))
    text_rect = turn_text.get_rect()
    text_rect.topleft = [10, 10]
    axie_int.screen.blit(turn_text, text_rect)

    # 绘制能量
    energy_font = pygame.font.Font(None, 36)
    turn_text = energy_font.render('Energy: ' + str(axie_int.env.our_energy), True, (128, 128, 128))
    text_rect = turn_text.get_rect()
    text_rect.topleft = [10, 50]
    axie_int.screen.blit(turn_text, text_rect)

    turn_text = energy_font.render('Energy: ' + str(axie_int.env.enm_energy), True, (128, 128, 128))
    text_rect = turn_text.get_rect()
    text_rect.topleft = [1150, 50]
    axie_int.screen.blit(turn_text, text_rect)

    # 绘制我方axie图片
    for _i in range(3):
        if axie_int.our_axie[_i].hp > 0:
            axie_int.screen.blit(axie_int.our_axie[_i].image[0], axie_int.our_axie[_i].rect)  # 将正常axie画出来
        else:
            # axie死亡后图片
            axie_int.screen.blit(axie_int.our_axie[_i].image[1], axie_int.our_axie[_i].rect)  # 将死亡axie画出来

    # 绘制敌方axie图片
    for _i in range(3):
        if axie_int.enm_axie[_i].hp > 0:
            axie_int.screen.blit(axie_int.enm_axie[_i].image[0], axie_int.enm_axie[_i].rect)  # 将正常axie画出来
        else:
            # axie死亡后图片
            axie_int.screen.blit(axie_int.enm_axie[_i].image[1], axie_int.enm_axie[_i].rect)  # 将死亡axie画出来

    # 绘制血量
    hp_font = pygame.font.Font(None, 24)
    for _i in range(3):  # 我方血量
        if axie_int.our_axie[_i].hp > 0:
            hp_text = hp_font.render('SPEED: ' +
                                     str(axie_int.our_axie[_i].rank + 1) + '  HP: ' + str(axie_int.our_axie[_i].hp),
                                     True, (0, 128, 0))
            text_rect = hp_text.get_rect()
            text_rect.topleft = [50 + _i * 200, 250]
            axie_int.screen.blit(hp_text, text_rect)

    for _i in range(3):  # 敌方血量
        if axie_int.enm_axie[_i].hp > 0:
            hp_text = hp_font.render('SPEED: ' +
                                     str(axie_int.enm_axie[_i].rank + 1) + '  HP: ' + str(axie_int.enm_axie[_i].hp),
                                     True, (0, 128, 0))
            text_rect = hp_text.get_rect()
            text_rect.topleft = [710 + _i * 200, 250]
            axie_int.screen.blit(hp_text, text_rect)

    # 绘制防御
    def_font = pygame.font.Font(None, 24)
    for _i in range(3):  # 我方防御
        if axie_int.our_axie[_i].hp > 0:
            def_text = def_font.render('DEF: ' + str(axie_int.our_axie[_i].defence), True, (0, 0, 250))
            text_rect = def_text.get_rect()
            text_rect.topleft = [50 + _i * 200, 280]
            axie_int.screen.blit(def_text, text_rect)

    for _i in range(3):  # 敌方防御
        if axie_int.enm_axie[_i].hp > 0:
            def_text = def_font.render('DEF: ' + str(axie_int.enm_axie[_i].defence), True, (0, 0, 250))
            text_rect = def_text.get_rect()
            text_rect.topleft = [710 + _i * 200, 280]
            axie_int.screen.blit(def_text, text_rect)

    # 绘制手牌
    cards_font = pygame.font.Font(None, 20)
    for _i in range(3):  # 我方卡牌
        if axie_int.our_axie[_i].hp > 0:
            for key, _cards in enumerate(axie_int.our_axie[_i].cards):
                if _cards in axie_int.our_axie[_i].skills.keys():
                    cards_text = cards_font.render(str(_cards) + '  ' +
                                                   str(axie_int.our_axie[_i].skills[_cards]['name']) + '  ' +
                                                   str(axie_int.our_axie[_i].skills[_cards]['energy']) + '  ' +
                                                   str(axie_int.our_axie[_i].skills[_cards]['att']) + '  ' +
                                                   str(axie_int.our_axie[_i].skills[_cards]['def'])
                                                   , True, (128, 128, 128))
                else:
                    cards_text = cards_font.render('  ', True, (128, 128, 128))
                text_rect = cards_text.get_rect()
                text_rect.topleft = [50 + _i * 200, 450 + key * 30]
                axie_int.screen.blit(cards_text, text_rect)

    for _i in range(3):  # 敌方卡牌
        if axie_int.enm_axie[_i].hp > 0:
            for key, _cards in enumerate(axie_int.enm_axie[_i].cards):
                if _cards in axie_int.enm_axie[_i].skills.keys():
                    cards_text = cards_font.render(str(_cards) + '  ' +
                                                   str(axie_int.enm_axie[_i].skills[_cards]['name']) + '  ' +
                                                   str(axie_int.enm_axie[_i].skills[_cards]['energy']) + '  ' +
                                                   str(axie_int.enm_axie[_i].skills[_cards]['att']) + '  ' +
                                                   str(axie_int.enm_axie[_i].skills[_cards]['def'])
                                                   , True, (128, 128, 128))
                else:
                    cards_text = cards_font.render('  ', True, (128, 128, 128))
                text_rect = cards_text.get_rect()
                text_rect.topleft = [700 + _i * 200, 450 + key * 30]
                axie_int.screen.blit(cards_text, text_rect)

    # 绘制出卡卡牌
    cards_font = pygame.font.Font(None, 20)
    for _i in range(3):  # 我方卡牌
        for key, _cards in enumerate(axie_int.our_axie[_i].cards_att):
            cards_text = cards_font.render(str(_cards) + '  ' +
                                           str(axie_int.our_axie[_i].skills[_cards]['name']) + '  ' +
                                           str(axie_int.our_axie[_i].skills[_cards]['energy']) + '  ' +
                                           str(axie_int.our_axie[_i].skills[_cards]['att']) + '  ' +
                                           str(axie_int.our_axie[_i].skills[_cards]['def'])
                                           , True, (128, 128, 128))
            text_rect = cards_text.get_rect()
            text_rect.topleft = [50 + _i * 200, 220 - key * 30]
            axie_int.screen.blit(cards_text, text_rect)

    for _i in range(3):  # 敌方卡牌
        for key, _cards in enumerate(axie_int.enm_axie[_i].cards_att):
            cards_text = cards_font.render(str(_cards) + '  ' +
                                           str(axie_int.enm_axie[_i].skills[_cards]['name']) + '  ' +
                                           str(axie_int.enm_axie[_i].skills[_cards]['energy']) + '  ' +
                                           str(axie_int.enm_axie[_i].skills[_cards]['att']) + '  ' +
                                           str(axie_int.enm_axie[_i].skills[_cards]['def'])
                                           , True, (128, 128, 128))
            text_rect = cards_text.get_rect()
            text_rect.topleft = [700 + _i * 200, 220 - key * 30]
            axie_int.screen.blit(cards_text, text_rect)

    # 更新屏幕
    pygame.display.update()


def keyboard_monitor(_axie_int):
    # 检测键盘
    op_key = False
    op_key_value = ''
    if _axie_int.env.op_delay_kb > 0:
        _axie_int.env.op_delay_kb -= 1
    else:
        key_pressed = pygame.key.get_pressed()
        if key_pressed[K_RETURN]:
            op_key = True
            op_key_value = 'enter'
        if op_key:
            _axie_int.env.op_delay_kb = 20
    return op_key, op_key_value


def get_mouse():
    axie_num = -1
    card_num = -1
    pressed_array = pygame.mouse.get_pressed()
    for index in range(len(pressed_array)):
        if pressed_array[index]:
            if index == 0:
                pos = pygame.mouse.get_pos()
                # print('Pressed LEFT Button!', pos)
                break
        else:
            return axie_num, card_num
    x = pos[0]
    y = pos[1]

    return x, y


def mouse_monitor(_axie_int):
    # 检测鼠标
    op_val = [-1, -1]
    op_name = -1
    op_mo = False
    if _axie_int.env.op_delay_mo > 0:
        _axie_int.env.op_delay_mo -= 1
    else:
        x, y = get_mouse()
        if y > 440:
            if 50 < x < 600:  # 选择我方卡牌
                op_name = 'card'
                for _i in range(3):  # 判断是那只怪的卡
                    if 50 + _i * 180 < x <= 50 + (_i + 1) * 180:
                        op_val[0] = _i
                for _i in range(9):  # 判断是哪行卡
                    if 440 + 30 * _i < y <= 440 + (_i + 1) * 30:
                        op_val[1] = _i

            elif 700 < x < 1250:  # 敌方卡牌
                op_name = 'card'
                for _i in range(3):  # 判断是那只怪的卡
                    if 700 + _i * 180 < x <= 700 + (_i + 1) * 180:
                        op_val[0] = _i + 3
                for _i in range(9):  # 判断是哪行卡
                    if 440 + 30 * _i < y <= 440 + (_i + 1) * 30:
                        op_val[1] = _i

        if 548 < x < 707 and 51 < y < 105:
            op_name = 'end_turn'

        if op_name != -1:
            op_mo = True
            _axie_int.env.op_delay_kb = 20
    return op_mo, op_name, op_val


def game_operate(_axie_int, key_value, mo_name, mo_value):
    # end turn执行动作
    if key_value == 'enter' or mo_name == 'end_turn':
        # 执行攻击操作
        for _rank in range(6):
            for _i in range(3):
                if _axie_int.our_axie[_i].rank == _rank and _axie_int.our_axie[_i].hp > 0:  # 我方
                    if _axie_int.our_axie[_i].cards_att:
                        att_pos_list = [x for x in range(3) if _axie_int.enm_axie[x].hp > 0]
                        att_pos = att_pos_list[0]
                        _axie_int.our_axie[_i].rect.topleft = (550 + 200 * att_pos, 300)
                        game_display(_axie_int)

                        for _card in _axie_int.our_axie[_i].cards_att:
                            att_value = int(ALL_CARDS[_card]['att'])  # 卡牌攻击力
                            if _axie_int.enm_axie[att_pos].defence < att_value:
                                _axie_int.enm_axie[att_pos].hp -= att_value - _axie_int.enm_axie[att_pos].defence
                                _axie_int.enm_axie[att_pos].defence = 0
                                if _axie_int.enm_axie[att_pos].hp < 0:
                                    break
                            else:
                                _axie_int.enm_axie[att_pos].defence -= att_value
                            # 更新界面
                            _axie_int.our_axie[_i].rect.topleft = (550 + 200 * att_pos, 280)
                            game_display(_axie_int)
                            sleep(0.2)
                            _axie_int.our_axie[_i].rect.topleft = (550 + 200 * att_pos, 300)
                            game_display(_axie_int)
                            sleep(0.2)
                        _axie_int.our_axie[_i].rect.topleft = (20 + 200 * _i, 300)
                        game_display(_axie_int)

                if _axie_int.enm_axie[_i].rank == _rank and _axie_int.enm_axie[_i].hp > 0:  # 敌方
                    if _axie_int.enm_axie[_i].cards_att:
                        att_pos_list = [x for x in range(3) if _axie_int.our_axie[x].hp > 0]
                        att_pos = att_pos_list[len(att_pos_list) - 1]
                        _axie_int.enm_axie[_i].rect.topleft = (160 + 200 * att_pos, 300)
                        game_display(_axie_int)

                        for _card in _axie_int.enm_axie[_i].cards_att:
                            att_value = int(ALL_CARDS[_card]['att'])  # 卡牌攻击力
                            if _axie_int.our_axie[att_pos].defence < att_value:
                                _axie_int.our_axie[att_pos].hp -= att_value - _axie_int.our_axie[att_pos].defence
                                _axie_int.our_axie[att_pos].defence = 0
                                if _axie_int.our_axie[att_pos].hp < 0:
                                    break
                            else:
                                _axie_int.our_axie[att_pos].defence -= att_value
                            # 更新界面
                            _axie_int.enm_axie[_i].rect.topleft = (160 + 200 * att_pos, 280)
                            game_display(_axie_int)
                            sleep(0.2)
                            _axie_int.enm_axie[_i].rect.topleft = (160 + 200 * att_pos, 300)
                            game_display(_axie_int)
                            sleep(0.2)
                        _axie_int.enm_axie[_i].rect.topleft = (700 + 200 * _i, 300)
                        game_display(_axie_int)
        _axie_int.env.process_data = True

    # 选择卡牌执行动作
    if mo_name == 'card':
        axie_num = mo_value[0]
        card_num = mo_value[1]
        if 0 <= axie_num < 3:
            if card_num <= len(_axie_int.our_axie[axie_num].cards) - 1 and len(
                    _axie_int.our_axie[axie_num].cards_att) < 4:  # 选中的地方有卡牌 并且 出卡总数小于4
                if _axie_int.our_axie[axie_num].cards[card_num] > 0:  # 判断是否为未选过卡牌
                    sel_card_energy = int(ALL_CARDS[_axie_int.our_axie[axie_num].cards[card_num]]['energy'])
                    if _axie_int.env.our_energy >= sel_card_energy:  # 能量足够
                        _axie_int.env.our_energy -= sel_card_energy
                        _axie_int.our_axie[axie_num].defence += int(
                            ALL_CARDS[_axie_int.our_axie[axie_num].cards[card_num]]['def'])  # 加上防御
                        _axie_int.our_axie[axie_num].cards_att.append(_axie_int.our_axie[axie_num].cards[card_num])
                        _axie_int.our_axie[axie_num].cards[card_num] = -1  # 这张卡牌清掉

        elif 3 <= axie_num < 6:
            axie_num -= 3
            if card_num <= len(_axie_int.enm_axie[axie_num].cards) - 1 and len(
                    _axie_int.enm_axie[axie_num].cards_att) < 4:  # 选中的地方有卡牌 并且 出卡总数小于4
                if _axie_int.enm_axie[axie_num].cards[card_num] > 0:  # 判断是否为未选过卡牌
                    sel_card_energy = int(ALL_CARDS[_axie_int.enm_axie[axie_num].cards[card_num]]['energy'])
                    if _axie_int.env.enm_energy >= sel_card_energy:
                        _axie_int.env.enm_energy -= sel_card_energy
                        _axie_int.enm_axie[axie_num].defence += int(
                            ALL_CARDS[_axie_int.enm_axie[axie_num].cards[card_num]]['def'])  # 加上防御
                        _axie_int.enm_axie[axie_num].cards_att.append(_axie_int.enm_axie[axie_num].cards[card_num])
                        _axie_int.enm_axie[axie_num].cards[card_num] = -1  # 这张卡牌清掉


def data_process(_axie_int):
    # 环境信息更新
    if _axie_int.env.turn == 0:
        _axie_int.env.turn += 1
    else:
        _axie_int.env.end_turn()

    # 根据速度计算攻击顺序
    get_att_seq(_axie_int)

    # 手牌信息更新
    for _i in range(3):
        _axie_int.our_axie[_i].cards = [x for x in _axie_int.our_axie[_i].cards if x > 0]
        _axie_int.our_axie[_i].cards_att = []
        _axie_int.enm_axie[_i].cards = [x for x in _axie_int.enm_axie[_i].cards if x > 0]
        _axie_int.enm_axie[_i].cards_att = []

    # 随机生成卡牌
    get_random_cards(_axie_int)

    # 护盾清零
    for _i in range(3):
        _axie_int.our_axie[_i].defence = 0
        _axie_int.enm_axie[_i].defence = 0


def axie_game_run(axie_int, action):
    # 处理游戏结束
    our_axie_num = [x for x in range(3) if axie_int.our_axie[x].hp > 0]
    enm_axie_num = [x for x in range(3) if axie_int.enm_axie[x].hp > 0]
    if not our_axie_num or not enm_axie_num:
        print('游戏结束')
        return False

    # 数据处理
    if axie_int.env.process_data:
        axie_int.env.process_data = False
        data_process(axie_int)

    # 显示界面
    game_display(axie_int)


    # 处理游戏退出
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    # 监测键盘
    op_key, op_key_value = keyboard_monitor(axie_int)

    # 监测鼠标
    op_mo, op_mo_name, op_mo_value = mouse_monitor(axie_int)

    # 执行相应动作
    if op_key or op_mo:
        game_operate(axie_int, op_key_value, op_mo_name, op_mo_value)

    return True


if __name__ == "__main__":
    ALL_CARDS = load_axie_skill()  # 加载卡牌

    _axie_int = AxieGameInt()  # 游戏初始化

    action = {}
    while axie_game_run(_axie_int, action):  # 进行游戏:
        pass

