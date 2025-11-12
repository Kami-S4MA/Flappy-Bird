# flappy_ai.py
# NEAT runner that imports core game pieces from flappy_core.
# Exposes run_ai(config_path, surface, max_gens=50)

import neat
import os
import pygame
from flappy_core import Bird, Pipe, Base, draw_ai_window, WIN_WIDTH
import time

GEN = 0

def ai_generation_runner(genomes, config, surface, generation_ref):
    """
    Run one generation. generation_ref is a dict used to control generation/run
    keys: 'gen', 'stop_all', 'running'
    """
    global GEN
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
        clock.tick(45)

        # handle events (allow ESC to stop entire run)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                generation_ref['stop_all'] = True
                generation_ref['running'] = False
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                generation_ref['stop_all'] = True
                generation_ref['running'] = False
                # small feedback
                surface.blit(pygame.Surface((1,1)), (0,0))
                pygame.display.update()
                pygame.time.delay(200)
                return

        if len(birds) == 0:
            generation_ref['running'] = False
            return

        pipe_ind = 0
        if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
            pipe_ind = 1

        # update birds
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

        draw_ai_window(surface, birds, pipes, base, score, generation_ref['gen'])

        if generation_ref.get('stop_all'):
            generation_ref['running'] = False
            return

def run_ai(config_path, surface, max_gens=50):
    """
    Run NEAT generation-by-generation, allowing ESC to stop cleanly.
    surface: pygame surface to draw to (pygame.display.get_surface()).
    """
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    generation_ref = {'gen': 0, 'stop_all': False, 'running': False}

    def main_wrapper(genomes, config_inner):
        generation_ref['gen'] += 1
        ai_generation_runner(genomes, config_inner, surface, generation_ref)
        return

    # Run one generation at a time to allow early exit via ESC
    for i in range(max_gens):
        if generation_ref['stop_all']:
            break
        p.run(main_wrapper, 1)
        if generation_ref['stop_all']:
            break

    # small pause when returning
    if generation_ref['stop_all']:
        surface.blit(pygame.Surface((1,1)), (0,0))
        pygame.display.update()
        pygame.time.delay(200)
