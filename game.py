# game.py
# Main menu, manual mode, highscores and optional MySQL saving.

import os
import sys
import pygame
import neat
import time
from datetime import datetime

# --- NEW: load .env automatically ---
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
except Exception as e:
    print("Warning: dotenv not loaded:", e)

import mysql.connector
from flappy_core import (
    WIN_WIDTH, WIN_HEIGHT, BG_IMG, STAT_FONT,
    Bird, Pipe, Base, draw_game_window, draw_ai_window
)
from flappy_ai import run_ai
import errno

print(os.getenv("DB_PASSWORD")
)

pygame.init()
pygame.font.init()

# Window setup
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Flappy Bird - Player & AI Modes")

# fonts and colors for menu
TITLE_FONT = pygame.font.SysFont("comicsans", 64)
BIG_FONT = pygame.font.SysFont("comicsans", 44)
SMALL_FONT = pygame.font.SysFont("comicsans", 18)

WHITE = (255, 255, 255)
GREY = (180, 180, 180)
HIGHLIGHT = (30, 144, 255)
GOLD = (212, 175, 55)

# highscores file
HIGHSCORE_FILE = "highscores.txt"
MAX_HIGHS = 10

# DB env-configurable
DB_NAME = os.getenv("DB_NAME", "flappybird-ai")
DB_HOST = os.getenv("DB_HOST", None)
DB_USER = os.getenv("DB_USER", None)
DB_PASSWORD = os.getenv("DB_PASSWORD", None)

def ensure_highscore_file():
    if not os.path.exists(HIGHSCORE_FILE):
        open(HIGHSCORE_FILE, "w", encoding="utf-8").close()

def load_highscores():
    ensure_highscore_file()
    highs = []
    with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
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
    with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
        for name, score in highs[:MAX_HIGHS]:
            f.write(f"{name},{score}\n")

def try_add_highscore(name, score):
    highs = load_highscores()
    # if same name exists, update if higher
    updated = False
    for i, (n, s) in enumerate(highs):
        if n == name:
            if score > s:
                highs[i] = (name, score)
            updated = True
            break
    if not updated:
        highs.append((name, score))
    highs.sort(key=lambda x: x[1], reverse=True)
    highs = highs[:MAX_HIGHS]
    save_highscores_list(highs)
    return highs

# --- MySQL helpers ---
def connect_db():
    """
    Connect using environment variables DB_HOST, DB_USER, DB_PASSWORD, DB_NAME.
    If DB_HOST or DB_USER not provided, return None.
    """
    if not DB_HOST or not DB_USER:
        print("DB connection info not provided; skipping DB save.")
        return None
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD or "",
            database=DB_NAME
        )
        return conn
    except mysql.connector.Error as e:
        print("Could not connect to DB:", e)
        return None

def ensure_results_table():
    conn = connect_db()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(64),
            score INT,
            date_played DATETIME
        )
        """)
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print("Error ensuring results table:", e)
        return False

def save_result_to_db(name, score):
    conn = connect_db()
    if conn is None:
        return False
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO results (name, score, date_played) VALUES (%s, %s, %s)",
                    (name, score, datetime.now()))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print("Failed to save result to DB:", e)
        return False

# --- Input gamertag inside window ---
def draw_text_center(win, text, font, color, y):
    surf = font.render(text, True, color)
    win.blit(surf, (WIN_WIDTH//2 - surf.get_width()//2, y))

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
        draw_text_center(win, prompt, SMALL_FONT, GREY, 170)

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

# --- Manual mode ---
def manual_mode(win, gamertag):
    bird = Bird(230, 350)
    base = Base(730)
    pipes = [Pipe(600)]
    clock = pygame.time.Clock()
    score = 0
    run = True

    while run:
        clock.tick(30)
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

    # Game over: save highs locally and attempt DB save
    highs = load_highscores()
    is_high = False
    if len(highs) < MAX_HIGHS or score > highs[-1][1]:
        is_high = True
        highs = try_add_highscore(gamertag, score)

    # attempt DB save (non-fatal)
    saved_db = save_result_to_db(gamertag, score)

    # Show game over screen
    clock = pygame.time.Clock()
    while True:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE):
                return None

        win.blit(BG_IMG, (0,0))
        draw_text_center(win, "Game Over", TITLE_FONT, WHITE, 100)
        draw_text_center(win, f"{gamertag} scored: {score}", BIG_FONT, GREY, 200)
        if is_high:
            draw_text_center(win, "NEW TOP 10! Saved locally.", SMALL_FONT, GOLD, 280)
        else:
            draw_text_center(win, "Press Enter or ESC to return to title", SMALL_FONT, GREY, 280)

        draw_text_center(win, f"DB saved: {'Yes' if saved_db else 'No'}", SMALL_FONT, GREY, 320)

        # preview top 5
        draw_text_center(win, "Top highs (preview):", SMALL_FONT, WHITE, 360)
        y = 400
        preview = highs[:5]
        for idx, (n, s) in enumerate(preview, start=1):
            medal = ""
            if idx == 1:
                medal = "🥇 "
            elif idx == 2:
                medal = "🥈 "
            elif idx == 3:
                medal = "🥉 "
            surf = STAT_FONT.render(f"{idx}. {medal}{n} - {s}", True, WHITE)
            win.blit(surf, (WIN_WIDTH//2 - surf.get_width()//2, y))
            y += 36

        pygame.display.update()

# --- Highscores screen ---
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
                medal = "🥇 "
            elif idx == 2:
                medal = "🥈 "
            elif idx == 3:
                medal = "🥉 "
            line = f"{idx}. {medal}{name} - {score}"
            surf = STAT_FONT.render(line, True, color)
            win.blit(surf, (WIN_WIDTH//2 - surf.get_width()//2, y))
            y += 40
        pygame.display.update()

# --- Title/menu ---
def title_screen():
    ensure_highscore_file()
    ensure_results_table()  # try to create table (if DB configured)
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
                            WIN.blit(BG_IMG, (0,0))
                            msg = STAT_FONT.render("Missing config-feedforward.txt", True, WHITE)
                            WIN.blit(msg, (WIN_WIDTH//2 - msg.get_width()//2, WIN_HEIGHT//2))
                            pygame.display.update()
                            pygame.time.delay(1000)
                        else:
                            # run NEAT; this function will handle ESC to return cleanly
                            surface = pygame.display.get_surface()
                            run_ai(config_path, surface, max_gens=50)
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
                        surface = pygame.display.get_surface()
                        run_ai(config_path, surface, max_gens=50)
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
            prefix = "> " if idx == selected else "  "
            color = HIGHLIGHT if idx == selected else WHITE
            surf = BIG_FONT.render(f"{prefix}{item}", True, color)
            WIN.blit(surf, (WIN_WIDTH//2 - surf.get_width()//2, start_y + idx * gap))
        draw_text_center(WIN, "Use Up/Down or W/S, Enter to select. 1/2/3 quick keys supported.", SMALL_FONT, GREY, WIN_HEIGHT - 40)
        pygame.display.update()

if __name__ == "__main__":
    title_screen()
