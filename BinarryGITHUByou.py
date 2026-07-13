import pyxel
import random
import math

# --- 定数設定 ---
GAMEPAD_DPAD_UP = pyxel.GAMEPAD1_BUTTON_DPAD_UP
GAMEPAD_DPAD_DOWN = pyxel.GAMEPAD1_BUTTON_DPAD_DOWN
GAMEPAD_DPAD_LEFT = pyxel.GAMEPAD1_BUTTON_DPAD_LEFT
GAMEPAD_DPAD_RIGHT = pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT
GAMEPAD_A_ID = pyxel.GAMEPAD1_BUTTON_A
GAMEPAD_START_ID = pyxel.GAMEPAD1_BUTTON_START
GAMEPAD_Y_ID = pyxel.GAMEPAD1_BUTTON_Y

TILE = 8
OY = 16

STAGES = [
    ["1111111111111111","1000000110000001","1011100220011101","1010301111030101","1030000000000301","1011110110111101","1000000000000001","1011011111101101","1000004004000001","1011110110111101","1000000000000001","1111111111111111"],
    ["1111111111111111","1030000110000301","1111100220011111","1000001111000001","1011111001111101","1004000000004001","1011111001111101","1000000000000001","1111101111011111","1000000330000001","1011101111011101","1111111111111111"],
    ["1111111111111111","1030301111030301","1111100220011111","1000001111000001","1010111001110101","1004000000004001","1010111001110101","1000001111000001","1011111111111101","1000000330000001","1011101111011101","1111111111111111"],
    ["1111111111111111","1000000000000001","1031110000111301","1000001111000001","1011110000111101","1040000220000401","1011110000111101","1000001111000001","1031110000111301","1000000000000001","1000000000000001","1111111111111111"],
    ["1111111111111111","1030000000000301","1011110111011101","1000000000000001","1010111001110101","1040000220000401","1010111001110101","1000000000000001","1010111111110101","1030000000000301","1011111111111101","1111111111111111"],
    ["1111111111111111","1030000000000301","1000000000000001","1000111111110001","1000100000001001","1000100000001001","1000100000001001","1000111111110001","1000000000000001","1030000000000301","1000000000000001","1111111111111111"]
]

class Game:
    def __init__(self):
        pyxel.init(128, 128, title="Binary HUMAN DX")
        pyxel.load("my_resourcekakou.pyxres")
        pyxel.images[1].load(0, 0, "image_LOGO02.png")
        
        pyxel.sounds[0].set("c3e3g3c4e3c3g3e3f3a3c4f4a3f3c4a3", "p", "4", "n", 15)
        pyxel.sounds[1].set("a1", "n", "2", "n", 10)
        pyxel.sounds[2].set("e2g2", "s", "4", "n", 15)
        pyxel.sounds[3].set("c1", "n", "5", "n", 5)
        pyxel.sounds[4].set("c2e2g2c3", "s", "6", "n", 20)
        self.debug_mode = False
        pyxel.play(0, 0, loop=True)
        self.reset_game()
        pyxel.run(self.update, self.draw)

    def reset_game(self):
        self.state = "TITLE"
        self.score = 0
        self.lives = 3
        self.stage = 0
        self.loop = 1
        self.ending_timer = 0
        self.start_delay = 30
        self.input_sequence = []
        self.invincible_timer = 0
        self.invincible_item = None
        self.load_stage()

    def load_stage(self):
        self.map = [[c for c in r] for r in STAGES[self.stage % len(STAGES)]]
        self.items = [[x, y] for y, r in enumerate(self.map) for x, c in enumerate(r) if c == '3']
        potential_enemies = [[x, y] for y, r in enumerate(self.map) for x, c in enumerate(r) if c == '4']
        self.enemies = []
        for e in potential_enemies:
            if self.loop < 2:
                if (abs(e[0]-1) + abs(e[1]-10) > 2) and (abs(e[0]-14) + abs(e[1]-10) > 2):
                    self.enemies.append(e)
            else:
                self.enemies.append(e)
        self.door_open = False
        self.p1, self.p2 = [1, 10], [14, 10]
        if self.stage == 5:
            self.boss = [7, 5]
            self.boss_hp = 3 + self.loop
        else:
            self.boss = None

        self.bonus_item = None
        self.bonus_added = False
        self.invincible_timer = 0
        self.invincible_item = None
        self.spiders = []
        self.freeze_timer = 0

    def is_action_btn(self):
        return pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(GAMEPAD_A_ID)

    def demo_ai(self):
        if pyxel.frame_count % 15 != 0: return 0, 0
        target = None
        if self.items: target = self.items[0]
        elif self.door_open:
            for y, r in enumerate(self.map):
                for x, c in enumerate(r):
                    if c == '2': target = [x, y]; break
                if target: break
        if not target: return random.choice([-1, 0, 1]), random.choice([-1, 0, 1])
        dx = 1 if self.p1[0] < target[0] else (-1 if self.p1[0] > target[0] else 0)
        dy = 1 if self.p1[1] < target[1] else (-1 if self.p1[1] > target[1] else 0)
        if dx != 0 and self.map[self.p1[1]][self.p1[0] + dx] == '1': dx = 0
        if dy != 0 and self.map[self.p1[1] + dy][self.p1[0]] == '1': dy = 0
        return dx, dy

    def update(self):
        match self.state:
            case "TITLE":
                adx, ady = self.demo_ai()
                self.move_players(adx, ady)
                self.update_enemies()
                if pyxel.btnp(pyxel.KEY_UP) or pyxel.btnp(GAMEPAD_DPAD_UP): self.input_sequence.append("U")
                elif pyxel.btnp(pyxel.KEY_DOWN) or pyxel.btnp(GAMEPAD_DPAD_DOWN): self.input_sequence.append("D")
                if len(self.input_sequence) > 4: self.input_sequence.pop(0)
                if self.input_sequence == ["U", "U", "D", "D"]:
                    self.debug_mode = not self.debug_mode
                    self.input_sequence = []
                if pyxel.btnp(GAMEPAD_START_ID) or self.is_action_btn():
                    self.reset_game()
                    self.state = "OPENING"
            case "OPENING":
                if self.is_action_btn(): 
                    self.state = "GAME"
                    self.start_delay = 30
            case "GAME":
                if self.start_delay > 0: self.start_delay -= 1
                elif self.stage == 5: self.state = "BOSS"
                else: self.move_players(); self.update_enemies()
            case "BOSS":
                 if self.start_delay > 0:
                    self.start_delay -= 1
                 else:
                    self.move_players()
                
                    if pyxel.frame_count % 30 == 0:
                        self.target = self.p1 if random.random() < 0.5 else self.p2

                    target = getattr(self, "target", self.p1)

                    # ボス移動速度
                    boss_move_interval = max(8, 20 - (self.loop - 1) * 2)

                    if pyxel.frame_count % boss_move_interval == 0:

                        if self.boss[0] < target[0]:
                            self.boss[0] += 1
                        elif self.boss[0] > target[0]:
                            self.boss[0] -= 1

                        if self.boss[1] < target[1]:
                            self.boss[1] += 1
                        elif self.boss[1] > target[1]:
                            self.boss[1] -= 1
                    
                    if random.random() < min(0.02 * self.loop, 0.25):
                        dx = random.choice([-1, 0, 1])
                        dy = random.choice([-1, 0, 1])
                        if dx != 0 or dy != 0:
                            self.spiders.append([self.boss[0], self.boss[1], dx, dy])
                    if self.items:
                        for it in self.items[:]:
                            if it == self.p1 or it == self.p2: 
                                self.items.remove(it); pyxel.play(2, 2)
                    else: self.state = "ENDING"; self.ending_timer = 0
                    if not self.debug_mode and self.invincible_timer <= 0 and (self.boss == self.p1 or self.boss == self.p2): 
                        self.lives -= 1
                        if self.lives <= 0: self.state = "GAMEOVER"
                        else: self.load_stage(); self.start_delay = 30
            case "ENDING":
                self.ending_timer += 1
                if self.ending_timer > 800 and self.is_action_btn():
                    self.loop += 1
                    self.stage = 0
                    self.load_stage()
                    self.state = "GAME"
            case "GAMEOVER":
                if self.is_action_btn():
                    self.reset_game()

    def move_players(self, auto_dx=None, auto_dy=None):
        if self.invincible_timer > 0: self.invincible_timer -= 1
        prob = max(0.0005, 0.002 - (self.loop - 1) * 0.0003)
        if self.stage < 5 and self.state != "BOSS" and self.invincible_item is None and random.random() < prob:
            rx, ry = random.randint(1, 14), random.randint(1, 10)
            if self.map[ry][rx] == '0': self.invincible_item = [rx, ry]
        is_frozen = self.freeze_timer > 0
        if is_frozen: self.freeze_timer -= 1
        dx = dy = 0
        if not is_frozen:
            if auto_dx is not None and auto_dy is not None: dx, dy = auto_dx, auto_dy
            else:
                if pyxel.btnp(pyxel.KEY_LEFT, 10, 5) or pyxel.btnp(GAMEPAD_DPAD_LEFT, 10, 5): dx, dy = -1, 0
                elif pyxel.btnp(pyxel.KEY_RIGHT, 10, 5) or pyxel.btnp(GAMEPAD_DPAD_RIGHT, 10, 5): dx, dy = 1, 0
                elif pyxel.btnp(pyxel.KEY_UP, 10, 5) or pyxel.btnp(GAMEPAD_DPAD_UP, 10, 5): dx, dy = 0, -1
                elif pyxel.btnp(pyxel.KEY_DOWN, 10, 5) or pyxel.btnp(GAMEPAD_DPAD_DOWN, 10, 5): dx, dy = 0, 1
        if dx != 0 or dy != 0:
            for p, d in [(self.p1, dx), (self.p2, -dx)]:
                nx, ny = p[0] + d, p[1] + dy
                if self.map[ny][nx] != '1':
                    if self.map[ny][nx] == '2' and not self.door_open: continue
                    p[0], p[1] = nx, ny
            if self.state != "TITLE": pyxel.play(1, 1)
        if self.stage < 5:
            for it in self.items[:]:
                if it == self.p1 or it == self.p2: 
                    self.items.remove(it); self.score += 500
                    if self.state != "TITLE": pyxel.play(2, 2)
            if not self.items:
                if self.stage in [3, 4] and not self.bonus_added: self.bonus_item = [7, 4]; self.bonus_added = True
                self.door_open = True
            if self.bonus_item and (self.bonus_item == self.p1 or self.bonus_item == self.p2):
                self.lives += 1; self.bonus_item = None; pyxel.play(2, 2)
            if self.invincible_item and (self.invincible_item == self.p1 or self.invincible_item == self.p2):
                self.invincible_timer = 300; self.invincible_item = None; pyxel.play(2, 2)
            if self.door_open and self.map[self.p1[1]][self.p1[0]] == '2' and self.map[self.p2[1]][self.p2[0]] == '2':
                if self.state != "TITLE": pyxel.play(3, 4)
                self.stage += 1; self.load_stage(); self.start_delay = 30

    def update_enemies(self):
        speed = max(3, 30 - (self.stage * 4) - (self.loop - 1) * 2)
        if pyxel.frame_count % speed == 0:
            for e in self.enemies:
                nx, ny = e[0] + random.choice([-1, 0, 1]), e[1] + random.choice([-1, 0, 1])
                if 0 <= nx < 16 and 0 <= ny < 12 and self.map[ny][nx] != '1' and self.map[ny][nx] != '4': e[0], e[1] = nx, ny
                if random.random() < 0.1:
                    self.spiders.append([e[0], e[1], random.choice([-1, 0, 1]), random.choice([-1, 0, 1])])
        if pyxel.frame_count % max(3, speed // 2) == 0:
            for s in self.spiders[:]:
                s[0] += s[2]; s[1] += s[3]
                if s[0] < 0 or s[0] >= 16 or s[1] < 0 or s[1] >= 12 or self.map[s[1]][s[0]] == '1': self.spiders.remove(s)
                elif (s[:2] == self.p1 or s[:2] == self.p2) and not self.debug_mode and self.invincible_timer <= 0:
                    if self.state != "TITLE": self.spiders.remove(s); self.freeze_timer = 300; pyxel.play(3, 3)
        for e in self.enemies:
            if (e == self.p1 or e == self.p2) and not self.debug_mode and self.invincible_timer <= 0:
                if self.state == "TITLE": continue
                damage = 1
                if self.loop >= 5: damage = 2
                self.lives -= damage
                if self.lives <= 0: self.lives = 0; self.state = "GAMEOVER"
                else: self.load_stage(); self.start_delay = 30

    def draw_game_elements(self):
        for y, r in enumerate(self.map):
            for x, c in enumerate(r):
                if c == '1': pyxel.blt(x*TILE, OY+y*TILE, 0, 16, 0, 8, 8)
                if c == '4': pyxel.blt(x*TILE, OY+y*TILE, 0, 48, 0, 8, 8)
                if c == '2': pyxel.blt(x*TILE, OY+y*TILE, 0, 24, 0, 8, 8)
        for i in self.items: pyxel.blt(i[0]*TILE, OY+i[1]*TILE, 0, 32, 0, 8, 8, 0)
        if self.bonus_item and (pyxel.frame_count % 30 < 15):
            pyxel.blt(self.bonus_item[0]*TILE, OY+self.bonus_item[1]*TILE, 0, 56, 0, 8, 8, 0); pyxel.rectb(self.bonus_item[0]*TILE, OY+self.bonus_item[1]*TILE, 8, 8, 10)
        for e in self.enemies: pyxel.blt(e[0]*TILE, OY+e[1]*TILE, 0, 40, 0, 8, 8, 0)
        for s in self.spiders: pyxel.blt(s[0]*TILE, OY+s[1]*TILE, 0, 48, 0, 8, 8, 0)
        if self.boss:
            s = abs(math.sin(pyxel.frame_count * 0.2)) * 16 + 8
            pyxel.circ(self.boss[0]*TILE + 4, OY+self.boss[1]*TILE + 4, s, 8); pyxel.circb(self.boss[0]*TILE + 4, OY+self.boss[1]*TILE + 4, s + 2, 9); pyxel.blt(self.boss[0]*TILE, OY+self.boss[1]*TILE, 0, 40, 0, 8, 8, 0)
        if self.invincible_item is not None: pyxel.blt(self.invincible_item[0]*TILE, OY+self.invincible_item[1]*TILE, 0, 64, 0, 8, 8, 0)
        if self.invincible_timer <= 0 or pyxel.frame_count % 4 < 2:
            pyxel.blt(self.p1[0]*TILE, OY+self.p1[1]*TILE, 0, 0, 0, 8, 8, 0); pyxel.blt(self.p2[0]*TILE, OY+self.p2[1]*TILE, 0, 8, 0, 8, 8, 0)
    
    def draw(self):
        pyxel.cls(0)
        match self.state:
            case "TITLE":
                self.draw_game_elements()
                pyxel.blt(15, 30, 1, 0, 0, 100, 33)
                pyxel.rect(20, 95, 88, 25, 0); pyxel.rectb(20, 95, 88, 25, 7)
                pyxel.text(25, 100, "MOVE: ARROW KEYS", 9); pyxel.text(25, 110, "GET ITEMS & DOOR", 9); pyxel.text(25, 55, "(C)MIRAI WORK/M.T 2026", 6)
                if pyxel.frame_count % 40 < 20: pyxel.text(18, 80, "PUSH START/SPACE BUTTON!", 7)
                if self.debug_mode: pyxel.text(5, 5, "DEBUG MODE", 8)
            case "OPENING":
                pyxel.text(45, 35, "STORY START", 7); pyxel.blt(30 + (pyxel.frame_count % 60), 60, 0, 0, 0, 8, 8); pyxel.blt(90 - (pyxel.frame_count % 60), 60, 0, 8, 0, 8, 8)
                pyxel.text(25, 80, "PRESS SPACE/A BUTTON!", pyxel.frame_count % 16)
            case "GAME" | "BOSS":
                self.draw_game_elements()
                pyxel.text(3, 5, f"SCORE:{self.score} LOOP:{self.loop} STG:{self.stage+1} LIFE:{self.lives}", 11)
                if self.invincible_timer > 0: pyxel.text(90, 13, f"INV:{self.invincible_timer // 30}", 10)
                if self.debug_mode: pyxel.text(5, 13, "DEBUG MODE", 8)
                if self.start_delay > 0: pyxel.text(42, 60, "PLAY START!", (pyxel.frame_count // 4) % 15 + 1)
            case "ENDING":
                t = self.ending_timer
                if t < 150: s = abs(math.sin(t * 0.2)) * 40 + 10; pyxel.circ(64, 64, s, (t // 5) % 16); pyxel.circb(64, 64, s + 5, 8); pyxel.blt(60, 60, 0, 40, 0, 8, 8, 0)
                elif t < 200: pyxel.circ(64, 64, (t - 150) * 2, 10); pyxel.circ(64, 64, (t - 150) * 1.5, 9); pyxel.circ(64, 64, (t - 150) * 1, 7)
                if t > 180:
                    for i in range(40):
                        x = (i * 37) % 128
                        speed = 1 + (i % 3)
                        y = (i * 53 + (t - 180) * speed) % 128
                        pyxel.pset(x, y, 7 if speed == 3 else (6 if speed == 2 else 5))
                    earth_y = 100 + (t - 180) * 0.2; pyxel.circ(64, earth_y, 40, 1); pyxel.circ(50, earth_y - 10, 10, 3); pyxel.circ(70, earth_y + 10, 15, 3)
                    pod_y = 64 - (t - 180) * 0.3; pyxel.blt(56, pod_y, 0, 0, 0, 8, 8, 0); pyxel.blt(64, pod_y, 0, 8, 0, 8, 8, 0)
                if t > 250:
                    credits = ["BINARY HUMAN DX", "PRODUCER: M.T", "TEAM T.D", "(C)MIRAI WORK/M.T 2026", "THANK YOU FOR PLAYING!"]
                    for i, text in enumerate(credits):
                        y = 128 - ((t - 250) * 0.5) + (i * 15)
                        if -10 < y < 130: pyxel.text(64 - len(text)*2, y, text, 11)
                pyxel.text(10, 120, "PRESS SPACE/A TO CONTINUE" if t > 800 else "", 7)
            case "GAMEOVER":
                self.draw_game_elements()
                pyxel.text(5, 5, f"SCORE:{self.score} STG:{self.stage+1} LIFE:{self.lives}", 8)
                pyxel.text(45, 60, "GAME OVER", 8)
                pyxel.text(23, 80, "PUSH SPACE/A TO RESTART", (pyxel.frame_count % 15) + 1)

Game()
