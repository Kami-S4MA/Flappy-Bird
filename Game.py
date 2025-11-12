# flappy_full.py
import pygame
import neat
import os
import random
import sys
import time

pygame.init()
pygame.font.init()

# ---------------- WINDOW & ASSETS ----------------
WIN_WIDTH = 500
WIN_HEIGHT = 800
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird - Player & AI Modes")

IMG_DIR = "imgs"  # images folder (must exist)

# load images
BIRD_IMGS = [
    pygame.transform.scale2x(pygame.image.load(os.path.join(IMG_DIR, "bird1.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join(IMG_DIR, "bird2.png"))),
    pygame.transform.scale2x(pygame.image.load(os.path.join(IMG_DIR, "bird3.png")))
]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join(IMG_DIR, "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join(IMG_DIR, "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join(IMG_DIR, "bg.png")))

# fonts and colors
TITLE_FONT = pygame.font.SysFont("comicsans", 64)
BIG_FONT = pygame.font.SysFont("comicsans", 44)
STAT_FONT = pygame.font.SysFont("comicsans", 28)
SMALL_FONT = pygame.font.SysFont("comicsans", 18)

WHITE = (255, 255, 255)
GREY = (200, 200, 200)
HIGHLIGHT = (30, 144, 255)
GOLD = (212, 175, 55)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)

FPS_MANUAL = 30
FPS_AI = 45

# highscores file
HIGHSCORE_FILE = "highscores.txt"
MAX_HIGHS = 10

# ---------------- GAME OBJECTS ----------------
class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
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
        d = self.vel * self.tick_count + 1.5 * (self.tick_count ** 2)
        if d >= 16:
            d = 16
        if d < 0:
            d -= 2
        self.y += d

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
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

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
        return t_point or b_point

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

# ---------------- HIGHSCORE HELPERS ----------------
def ensure_highscore_file():
    if not os.path.exists(HIGHSCORE_FILE):
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            pass

def load_highscores():
    ensure_highscore_file()
    highs = []
    with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # expect "name,score"
            parts = line.split(",", 1)
            if len(parts) != 2:
                continue
            name = parts[0].strip()
            try:
                score = int(parts[1].strip())
            except:
                continue
            highs.append((name, score))
    highs.sort(key=lambda x: x[1], reverse=True)
    return highs[:MAX_HIGHS]

def save_highscores_list(highs):
    # highs: list of (name,score) sorted desc
    with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
        for name, score in highs[:MAX_HIGHS]:
            f.write(f"{name},{score}\n")

def try_add_highscore(name, score):
    highs = load_highscores()
    highs.append((name, score))
    highs.sort(key=lambda x: x[1], reverse=True)
    highs = highs[:MAX_HIGHS]
    save_highscores_list(highs)
    return highs

# ---------------- DRAW UTILITIES ----------------
def draw_text_center(win, text, font, color, y):
    surf = font.render(text, True, color)
    win.blit(surf, (WIN_WIDTH//2 - surf.get_width()//2, y))

# ---------------- GAME DRAW ----------------
def draw_game_window(win, bird, pipes, base, score):
    win.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw(win)
    score_text = STAT_FONT.render(f"Score: {score}", True, WHITE)
    win.blit(score_text, (WIN_WIDTH - 10 - score_text.get_width(), 10))
    base.draw(win)
    bird.draw(win)
    pygame.display.update()

def draw_ai_window(win, birds, pipes, base, score, gen):
    win.blit(BG_IMG, (0, 0))
    for pipe in pipes:
        pipe.draw(win)
    score_text = STAT_FONT.render(f"Score: {score}", True, WHITE)
    gen_text = STAT_FONT.render(f"Gen: {gen}", True, WHITE)
    win.blit(score_text, (WIN_WIDTH - 10 - score_text.get_width(), 10))
    win.blit(gen_text, (10, 10))
    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()

# ---------------- GAMERTAG INPUT (IN-WINDOW) ----------------
def input_gamertag(win):
    gamertag = ""
    clock = pygame.time.Clock()
    prompt = "Enter gamertag (Enter to confirm, ESC to cancel)"
    blink = True
    blink_timer = 0

    while True:
        clock.tick(30)
        blink_timer = (blink_timer + 1) % 40
        blink = blink_timer < 20

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if gamertag.strip() == "":
                        continue
                    return gamertag.strip()[:16]
                elif event.key == pygame.K_BACKSPACE:
                    gamertag = gamertag[:-1]
                else:
                    if len(gamertag) < 16 and event.unicode.isprintable():
                        gamertag += event.unicode

        win.blit(BG_IMG, (0,0))
        draw_text_center(win, "Play Yourself", BIG_FONT, WHITE, 100)
        draw_text_center(win, prompt, STAT_FONT, GREY, 170)

        # input box
        box_w, box_h = 360, 50
        box_x = WIN_WIDTH//2 - box_w//2
        box_y = 240
        pygame.draw.rect(win, (0, 0, 0), (box_x, box_y, box_w, box_h))
        pygame.draw.rect(win, WHITE, (box_x, box_y, box_w, box_h), 2)
        name_surf = STAT_FONT.render(gamertag, True, WHITE)
        win.blit(name_surf, (box_x + 10, box_y + 10))
        if blink:
            cur_x = box_x + 10 + name_surf.get_width() + 2
            pygame.draw.rect(win, WHITE, (cur_x, box_y + 12, 2, box_h - 24))
        draw_text_center(win, "(max 16 characters)", SMALL_FONT, GREY, box_y + box_h + 12)
        draw_text_center(win, "ESC to cancel", SMALL_FONT, GREY, WIN_HEIGHT - 40)
        pygame.display.update()

# ---------------- MANUAL MODE ----------------
def manual_mode(win, gamertag):
    bird = Bird(230, 350)
    base = Base(730)
    pipes = [Pipe(600)]
    clock = pygame.time.Clock()
    score = 0
    run = True

    while run:
        clock.tick(FPS_MANUAL)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird.jump()
                elif event.key == pygame.K_ESCAPE:
                    return None

        bird.move()
        base.move()
        add_pipe = False
        rem = []

        for pipe in pipes:
            pipe.move()
            if pipe.collide(bird):
                run = False
            if not pipe.passed and pipe.x < bird.x:
                pipe.passed = True
                add_pipe = True
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

        if add_pipe:
            score += 1
            pipes.append(Pipe(WIN_WIDTH))
        for r in rem:
            if r in pipes:
                pipes.remove(r)

        if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
            run = False

        draw_game_window(win, bird, pipes, base, score)

    # end game: save highscore if qualifies (top 10)
    highs = load_highscores()
    is_high = False
    if len(highs) < MAX_HIGHS or score > highs[-1][1]:
        is_high = True
        highs = try_add_highscore(gamertag, score)
    # show simple game over screen then return to menu
    clock = pygame.time.Clock()
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE):
                return None

        win.blit(BG_IMG, (0,0))
        draw_text_center(win, "Game Over", TITLE_FONT, WHITE, 120)
        draw_text_center(win, f"{gamertag} scored: {score}", BIG_FONT, GREY, 220)
        if is_high:
            draw_text_center(win, "NEW TOP 10! Saved.", STAT_FONT, GOLD, 300)
        else:
            draw_text_center(win, "Press Enter or ESC to return to title", STAT_FONT, GREY, 300)

        # preview
        draw_text_center(win, "Top highs (preview):", STAT_FONT, WHITE, 360)
        y = 400
        preview = highs[:5]
        for idx, (n, s) in enumerate(preview, start=1):
            color = WHITE
            medal = ""
            if idx == 1:
                color = GOLD; medal = "🥇 "
            elif idx == 2:
                color = SILVER; medal = "🥈 "
            elif idx == 3:
                color = BRONZE; medal = "🥉 "
            surf = STAT_FONT.render(f"{idx}. {medal}{n} - {s}", True, color)
            win.blit(surf, (WIN_WIDTH//2 - surf.get_width()//2, y))
            y += 36

        pygame.display.update()

# ---------------- AI: per-generation runner ----------------
def ai_generation_runner(genomes, config, surface, generation_ref):
    """
    Run one generation of NEAT. This function handles per-frame events and drawing.
    generation_ref is a dict: {'gen':int, 'stop_all':bool, 'running':bool}
    If user presses ESC or closes window, set generation_ref['stop_all'] = True and return.
    """
    nets = []
    ge = []
    birds = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(600)]
    clock = pygame.time.Clock()
    score = 0
    generation_ref['running'] = True

    while True:
        clock.tick(FPS_AI)

        # events: allow ESC to stop whole AI run
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                generation_ref['stop_all'] = True
                generation_ref['running'] = False
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                generation_ref['stop_all'] = True
                generation_ref['running'] = False
                # show brief feedback
                surface.blit(BG_IMG, (0,0))
                msg_surf = STAT_FONT.render("Returning to menu...", True, WHITE)
                surface.blit(msg_surf, (WIN_WIDTH//2 - msg_surf.get_width()//2, WIN_HEIGHT//2 - msg_surf.get_height()//2))
                pygame.display.update()
                pygame.time.delay(500)
                return

        if len(birds) == 0:
            generation_ref['running'] = False
            return

        pipe_ind = 0
        if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
            pipe_ind = 1

        # birds update
        for x, bird in enumerate(list(birds)):
            bird.move()
            ge[x].fitness += 0.1
            if pipe_ind < len(pipes):
                inputs = (bird.y,
                          abs(bird.y - pipes[pipe_ind].height),
                          abs(bird.y - pipes[pipe_ind].bottom))
            else:
                inputs = (bird.y, 0.0, 0.0)
            output = nets[x].activate(inputs)
            if output[0] > 0.5:
                bird.jump()

        base.move()

        add_pipe = False
        rem = []
        for pipe in pipes:
            pipe.move()
            for x, bird in enumerate(list(birds)):
                if pipe.collide(bird):
                    try:
                        ge[x].fitness -= 1
                        birds.pop(x); nets.pop(x); ge.pop(x)
                    except Exception:
                        pass
                else:
                    if not pipe.passed and pipe.x < bird.x:
                        pipe.passed = True
                        add_pipe = True
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(WIN_WIDTH))

        for r in rem:
            if r in pipes:
                pipes.remove(r)

        for bird in list(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                try:
                    idx = birds.index(bird)
                    birds.pop(idx); nets.pop(idx); ge.pop(idx)
                except ValueError:
                    pass

        # draw
        draw_ai_window(surface, birds, pipes, base, score, generation_ref['gen'])

        if generation_ref.get('stop_all'):
            generation_ref['running'] = False
            return

# ---------------- run_ai: generation-by-generation ----------------
def run_ai(config_path, max_gens=50):
    """
    Run NEAT generation-by-generation, allowing ESC to stop cleanly.
    Uses external config file (config_path).
    """
    # load neat config and make population
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    surface = pygame.display.get_surface()
    generation_ref = {'gen': 0, 'stop_all': False, 'running': False}

    def main_wrapper(genomes, config_inner):
        # increment generation counter only when starting
        generation_ref['gen'] += 1
        # store current generation for drawing inside runner
        generation_ref_local = generation_ref
        ai_generation_runner(genomes, config_inner, surface, generation_ref_local)
        # after this returns, NEAT will continue or we will break
        return

    # run up to max_gens, one generation at a time
    for i in range(max_gens):
        if generation_ref['stop_all']:
            break
        p.run(main_wrapper, 1)
        if generation_ref['stop_all']:
            break

    # small pause when returning
    if generation_ref['stop_all']:
        surface.blit(BG_IMG, (0,0))
        msg_surf = STAT_FONT.render("Returned to menu", True, WHITE)
        surface.blit(msg_surf, (WIN_WIDTH//2 - msg_surf.get_width()//2, WIN_HEIGHT//2 - msg_surf.get_height()//2))
        pygame.display.update()
        pygame.time.delay(300)

# ---------------- HIGHSCORE SCREEN ----------------
def highscores_screen(win):
    ensure_highscore_file()
    clock = pygame.time.Clock()
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return

        win.blit(BG_IMG, (0,0))
        draw_text_center(win, "TOP 10 HIGHSCORES", TITLE_FONT, WHITE, 60)
        highs = load_highscores()
        y = 150
        for idx, (name, score) in enumerate(highs, start=1):
            color = WHITE
            medal = ""
            if idx == 1:
                color = GOLD; medal = "🥇 "
            elif idx == 2:
                color = SILVER; medal = "🥈 "
            elif idx == 3:
                color = BRONZE; medal = "🥉 "
            line = f"{idx}. {medal}{name} - {score}"
            surf = STAT_FONT.render(line, True, color)
            win.blit(surf, (WIN_WIDTH//2 - surf.get_width()//2, y))
            y += 40
        pygame.display.update()

# ---------------- TITLE MENU ----------------
def title_screen():
    clock = pygame.time.Clock()
    menu_items = ["Play Yourself", "AI Mode", "Top 10", "Quit"]
    selected = 0

    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(menu_items)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(menu_items)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    choice = menu_items[selected]
                    if choice == "Play Yourself":
                        name = input_gamertag(WIN)
                        if name:
                            manual_mode(WIN, name)
                    elif choice == "AI Mode":
                        local_dir = os.path.dirname(__file__)
                        config_path = os.path.join(local_dir, "config-feedforward.txt")
                        if not os.path.exists(config_path):
                            # show message then return to menu
                            WIN.blit(BG_IMG, (0,0))
                            msg = STAT_FONT.render("Missing config-feedforward.txt", True, WHITE)
                            WIN.blit(msg, (WIN_WIDTH//2 - msg.get_width()//2, WIN_HEIGHT//2))
                            pygame.display.update()
                            pygame.time.delay(1000)
                        else:
                            run_ai(config_path, max_gens=50)
                    elif choice == "Top 10":
                        highscores_screen(WIN)
                    elif choice == "Quit":
                        pygame.quit(); sys.exit()
                elif event.key == pygame.K_1:
                    name = input_gamertag(WIN)
                    if name:
                        manual_mode(WIN, name)
                elif event.key == pygame.K_2:
                    local_dir = os.path.dirname(__file__)
                    config_path = os.path.join(local_dir, "config-feedforward.txt")
                    if not os.path.exists(config_path):
                        WIN.blit(BG_IMG, (0,0))
                        msg = STAT_FONT.render("Missing config-feedforward.txt", True, WHITE)
                        WIN.blit(msg, (WIN_WIDTH//2 - msg.get_width()//2, WIN_HEIGHT//2))
                        pygame.display.update()
                        pygame.time.delay(1000)
                    else:
                        run_ai(config_path, max_gens=50)
                elif event.key == pygame.K_3:
                    highscores_screen(WIN)
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        # draw menu
        WIN.blit(BG_IMG, (0,0))
        draw_text_center(WIN, "Flappy Bird", TITLE_FONT, WHITE, 120)
        start_y = 260
        gap = 80
        for idx, item in enumerate(menu_items):
            if idx == selected:
                surf = BIG_FONT.render(f"> {item}", True, HIGHLIGHT)
            else:
                surf = BIG_FONT.render(item, True, WHITE)
            WIN.blit(surf, (WIN_WIDTH//2 - surf.get_width()//2, start_y + idx * gap))
        draw_text_center(WIN, "Use Up/Down or W/S, Enter to select. 1/2/3 quick keys also work.", SMALL_FONT, GREY, WIN_HEIGHT - 40)
        pygame.display.update()

# ------------------ MAIN ----------------
if __name__ == "__main__":
    ensure_highscore_file()
    title_screen()
