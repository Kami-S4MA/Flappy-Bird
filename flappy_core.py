# flappy_core.py
# Core game objects and drawing helpers used by both manual and AI modes.

import pygame
import os
import random
pygame.font.init()

# Window dimensions (used by draw helpers)
WIN_WIDTH = 500
WIN_HEIGHT = 800

# Locate images relative to this file
BASE_DIR = os.path.dirname(__file__)
IMG_DIR = os.path.join(BASE_DIR, "imgs")

def load_image(name):
    path = os.path.join(IMG_DIR, name)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required image not found: {path}")
    return pygame.transform.scale2x(pygame.image.load(path))

# Load assets (raise a clear error if missing)
BIRD_IMGS = [
    load_image("bird1.png"),
    load_image("bird2.png"),
    load_image("bird3.png"),
]
PIPE_IMG = load_image("pipe.png")
BASE_IMG = load_image("base.png")
BG_IMG = load_image("bg.png")

# Fonts
STAT_FONT = pygame.font.SysFont("comicsans", 28)

# Game classes
class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0  # degrees to tilt
        self.tick_count = 0
        self.vel = 0
        self.height = y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        # kinematic equation for displacement
        d = self.vel * self.tick_count + 1.5 * (self.tick_count ** 2)
        # terminal velocity
        if d >= 16:
            d = 16
        if d < 0:
            d -= 2
        self.y += d

        # tilt logic
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(40, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)
        return bool(t_point or b_point)

class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))

# Drawing helpers for manual and AI modes
def draw_game_window(win, bird, pipes, base, score):
    win.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw(win)
    score_text = STAT_FONT.render(f"Score: {score}", True, (255, 255, 255))
    win.blit(score_text, (WIN_WIDTH - 10 - score_text.get_width(), 10))
    base.draw(win)
    bird.draw(win)
    pygame.display.update()

def draw_ai_window(win, birds, pipes, base, score, gen):
    win.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw(win)
    score_text = STAT_FONT.render(f"Score: {score}", True, (255, 255, 255))
    gen_text = STAT_FONT.render(f"Gen: {gen}", True, (255, 255, 255))
    win.blit(score_text, (WIN_WIDTH - 10 - score_text.get_width(), 10))
    win.blit(gen_text, (10, 10))
    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()
