import os
import time
import pygame
import numpy as np
from snake_env import SnakeEnv
from dqn import DQNAgent

CKPT_DIR = 'checkpoints'
CKPT_MODEL = os.path.join(CKPT_DIR, 'dqn.pth')

def preprocess(obs):
    arr = np.array(obs, dtype=np.float32)
    if arr.ndim == 2:
        return arr[np.newaxis, ...]
    return arr

def play(size=12, fps=6):
    env = SnakeEnv(size=size)
    obs_shape = (1, env.size, env.size)
    agent = DQNAgent(obs_shape, env.action_space)

    if os.path.exists(CKPT_MODEL):
        try:
            agent.load(CKPT_MODEL)
            print('Loaded agent checkpoint.')
        except Exception as e:
            print('Failed to load checkpoint:', e)

    pygame.init()
    cell = 30
    screen = pygame.display.set_mode((env.size*cell, env.size*cell))
    clock = pygame.time.Clock()

    COLORS = {
        0: (0, 0, 0),       # empty
        1: (255, 255, 255), # snake
        2: (0, 255, 0),     # food
    }

    running = True
    while running:
        obs = env.reset()
        done = False
        while not done and running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

            state = preprocess(obs)
            action = agent.select_action(state, eps=0.0)
            obs, reward, done, info = env.step(action)

            # draw
            for y in range(env.size):
                for x in range(env.size):
                    v = int(obs[y, x])
                    color = COLORS.get(v, (128, 0, 0))
                    rect = pygame.Rect(x*cell, y*cell, cell, cell)
                    pygame.draw.rect(screen, color, rect)
            pygame.display.flip()
            clock.tick(fps)

        # brief pause between episodes
        time.sleep(0.5)

    pygame.quit()

if __name__ == '__main__':
    play(size=12, fps=6)
