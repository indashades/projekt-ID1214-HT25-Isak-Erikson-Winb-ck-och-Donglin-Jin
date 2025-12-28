import pygame
import random
import os
import numpy as np
import torch
from dqn import DQNAgent

pygame.init()
screenWidth = 800
screenHight = 800
#wasd: we just have the ai change these to true for movement

#under här är variabler att reseta när spelet är över{
a=0
w=0
s=0
d=0
last_dir = None

screen = pygame.display.set_mode((screenWidth,screenHight))
solidSnake = pygame.Rect((10,10,10,10))
mat1=random.randint(20,790)
mat2=random.randint(20,790)
snakeLength=0
prevX = []
prevY = []
wallX =[]
wallY = []
time=120
reward=0

mat=False
#}
clock=pygame.time.Clock()

# Agent integration settings
USE_AGENT = True
AGENT_GRID = 12
AGENT_CHANNELS = 3
AGENT_TRAIN = True
TRAIN_WARMUP = 500
TRAIN_UPDATES_PER_STEP = 1
TRAIN_SYNC_STEPS = 500
TRAIN_EPS_START = 1.0
TRAIN_EPS_FINAL = 0.02
TRAIN_EPS_DECAY = 5000.0
TOTAL_TRAIN_STEPS = 0
CKPT_PATH = os.path.join('checkpoints', 'dqn.pth')
agent = None
if USE_AGENT and os.path.exists(CKPT_PATH):
    try:
        agent = DQNAgent((AGENT_CHANNELS, AGENT_GRID, AGENT_GRID), 4)
        agent.load(CKPT_PATH, load_buffer=False)
        print('Loaded agent from', CKPT_PATH)
    except Exception as e:
        print('Failed loading agent:', e)

def build_agent_obs(grid_size=AGENT_GRID):
    # build a downsampled multi-channel observation from the pygame screen
    # channels: 0=snake, 1=food, 2=wall
    ch = AGENT_CHANNELS
    obs = np.zeros((ch, grid_size, grid_size), dtype=np.float32)
    cell_w = screenWidth // grid_size
    cell_h = screenHight // grid_size
    for gy in range(grid_size):
        for gx in range(grid_size):
            cx = gx * cell_w + cell_w // 2
            cy = gy * cell_h + cell_h // 2
            col = check_location(cx, cy)
            if col is None:
                continue
            r, g, b, a = col
            # detect food (green)
            if g > 200 and r < 100:
                obs[1, gy, gx] = 1.0
            # detect wall (red)
            elif r > 200 and g < 100:
                obs[2, gy, gx] = 1.0
            # detect snake (white-ish)
            elif r > 200 and g > 200 and b > 200:
                obs[0, gy, gx] = 1.0
    return obs

def check_location(x, y):
    if 0 <= x < screenWidth and 0 <= y < screenHight:
        return screen.get_at((x, y))
    return None

i = True
while i:
    clock.tick(time) #how fast things move, probably removed or changed for ai training
    if solidSnake.x<=mat1 and solidSnake.x>=mat1-10 and solidSnake.y<=mat2 and solidSnake.y>=mat2-10 or solidSnake.x>=mat1 and solidSnake.x<=mat1+10 and solidSnake.y>=mat2 and solidSnake.y<=mat2+10:
        mat=True
    if mat: #kollar om maten är uppäten
        reward=10
        z=True
        while z:
            mat1=random.randint(20,790)
            mat2=random.randint(20,790)
            if not (mat1>solidSnake.x-10 and mat1<solidSnake.x+20 and mat2>solidSnake.y-10 and mat2<solidSnake.y+20 or check_location(mat1,mat2)==(255,0,0,255) or check_location(mat1+10,mat2)==(255,0,0,255) or check_location(mat1,mat2+10)==(255,0,0,255) or check_location(mat1+10,mat2+10)==(255,0,0,255)):
                z=False
        snakeLength=snakeLength+1
        z=True
        while z:
            x1=random.randint(20,790)
            y1=random.randint(20,790)
            if not (x1>mat1-10 and x1<mat1+20 and y1>mat2-10 and y1<mat2+20 or x1>solidSnake.x-10 and x1<solidSnake.x+20 and y1>solidSnake.y-10 and y1<solidSnake.y+20):
                if random.randint(0,100)>75 and snakeLength>3:
                    f=random.randint(0,snakeLength-2)
                    wallX[f]=x1
                    wallY[f]=y1
                else:
                    z=False
        
        wallX.insert(0, x1)
        wallY.insert(0, y1)
        mat=False
    screen.fill((0,0,0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            i=False
    #back in loop, why doesnt python use parenteses :(
    pygame.draw.rect(screen,(0,255,0),pygame.Rect((mat1,mat2,10,10)))
    pygame.draw.rect(screen,(255,255,255),solidSnake)
    #here we loop the snake tail
    vilken=-1
    wall=-1
    for u in range(0,snakeLength,0+1):
        vilken=vilken+11
        if u==0:
            pygame.draw.rect(screen,(255,255,255),pygame.Rect((prevX[vilken],prevY[vilken],10,10)))
        else:
            pygame.draw.rect(screen,(255,245,255),pygame.Rect((prevX[vilken],prevY[vilken],10,10)))
        wall=wall+1
        pygame.draw.rect(screen,(255,0,0),pygame.Rect((wallX[wall],wallY[wall],10,10)))
    #collision
    if solidSnake.x < 0 or solidSnake.x + solidSnake.width > screenWidth or solidSnake.y < 0 or solidSnake.y + solidSnake.height > screenHight:
        #ran out of bounds
        reward=-8
        #under här är variable        the game still crashedr att reseta när spelet är över{
        a=0
        w=0
        s=0
        d=0
        solidSnake = pygame.Rect((10,10,10,10))
        mat1=random.randint(20,790)
        mat2=random.randint(20,790)
        snakeLength=0
        prevX = []
        prevY = []
        wallX =[]
        wallY = []
        reward=0
        mat=False
        #}
    elif check_location(solidSnake.x,solidSnake.y)==(255,245,255,255) or check_location(solidSnake.x+10,solidSnake.y)==(255,245,255,255) or check_location(solidSnake.x,solidSnake.y+10)==(255,245,255,255) or check_location(solidSnake.x+10,solidSnake.y+10)==(255,245,255,255):
        #ran into self
        reward=-10
        #under här är variabler att reseta när spelet är över{
        a=0
        w=0
        s=0
        d=0
        solidSnake = pygame.Rect((10,10,10,10))
        mat1=random.randint(20,790)
        mat2=random.randint(20,790)
        snakeLength=0
        prevX = []
        prevY = []
        wallX =[]
        wallY = []
        reward=0
        mat=False
        #}
    elif check_location(solidSnake.x,solidSnake.y)==(255,0,0,255) or check_location(solidSnake.x+10,solidSnake.y)==(255,0,0,255) or check_location(solidSnake.x,solidSnake.y+10)==(255,0,0,255) or check_location(solidSnake.x+10,solidSnake.y+10)==(255,0,0,255):
        #ran into wall
        reward=-5
        #under här är variabler att reseta när spelet är över{
        a=0
        w=0
        s=0
        d=0
        solidSnake = pygame.Rect((10,10,10,10))
        mat1=random.randint(20,790)
        mat2=random.randint(20,790)
        snakeLength=0
        prevX = []
        prevY = []
        wallX =[]
        wallY = []
        reward=0
        mat=False
        #}
    
    # movement with direction locking: prevent immediate reverse
    key = pygame.key.get_pressed()
    desired = None
    # record distance before movement for proximity reward
    try:
        head_before_x = solidSnake.x
        head_before_y = solidSnake.y
        dist_before = abs(head_before_x - mat1) + abs(head_before_y - mat2)
    except Exception:
        dist_before = None
    # if agent active, query it for the action and set desired accordingly
    if agent is not None:
        obs = build_agent_obs(AGENT_GRID)
        # agent expects shape (C,H,W)
        state = obs.astype(np.float32)
        try:
            if AGENT_TRAIN:
                # exploration schedule
                eps = TRAIN_EPS_FINAL + (TRAIN_EPS_START - TRAIN_EPS_FINAL) * np.exp(-1.0 * TOTAL_TRAIN_STEPS / TRAIN_EPS_DECAY)
            else:
                eps = 0.0
            action = agent.select_action(state, eps=eps)
            if action == 0:
                desired = 'L'
            elif action == 1:
                desired = 'R'
            elif action == 2:
                desired = 'U'
            elif action == 3:
                desired = 'D'
            prev_agent_state = state
            prev_agent_action = action
        except Exception as e:
            # on any agent error, disable agent for safety
            print('Agent inference error:', e)
            agent = None
    if key[pygame.K_a]:
        desired = 'L'
    elif key[pygame.K_d]:
        desired = 'R'
    elif key[pygame.K_w]:
        desired = 'U'
    elif key[pygame.K_s]:
        desired = 'D'
    elif key[pygame.K_q]:
        time=120
    elif key[pygame.K_e]:
        time=1000000

    # if desired direction is not the opposite of last_dir, accept it
    if desired:
        if not ((last_dir == 'L' and desired == 'R') or (last_dir == 'R' and desired == 'L') or (last_dir == 'U' and desired == 'D') or (last_dir == 'D' and desired == 'U')):
            if desired == 'L':
                a = 1
            elif desired == 'R':
                d = 1
            elif desired == 'U':
                w = 1
            elif desired == 'D':
                s = 1

    if w or a or s or d:
        prevX.insert(0, solidSnake.x)
        prevY.insert(0, solidSnake.y)
        solidSnake.move_ip(d-a, s-w)
        # update last_dir based on movement vector
        dx = d - a
        dy = s - w
        if dx < 0:
            last_dir = 'L'
        elif dx > 0:
            last_dir = 'R'
        elif dy < 0:
            last_dir = 'U'
        elif dy > 0:
            last_dir = 'D'

        # agent training: collect transition and train online
        if agent is not None and AGENT_TRAIN:
            TOTAL_TRAIN_STEPS += 1
            # build next state
            next_state = build_agent_obs(AGENT_GRID)
            # reward variable is set during collision/food checks above
            # done flag: True if collision or out-of-bounds — detect via mat/reset logic or screen checks
            done_flag = False
            # we consider death when reward is negative and game was reset — approximate
            if reward < 0:
                done_flag = True
            # push transition
            try:
                agent.buffer.push(prev_agent_state, prev_agent_action, float(reward), next_state, done_flag)
            except Exception:
                pass
            # updates
            if len(agent.buffer) >= TRAIN_WARMUP:
                for _ in range(TRAIN_UPDATES_PER_STEP):
                    agent.update()
            if TOTAL_TRAIN_STEPS % TRAIN_SYNC_STEPS == 0:
                agent.sync_target()

        # proximity reward: small positive reward if moved closer to food
        try:
            head_after_x = solidSnake.x
            head_after_y = solidSnake.y
            if dist_before is not None:
                dist_after = abs(head_after_x - mat1) + abs(head_after_y - mat2)
                if dist_after < dist_before:
                    reward = reward + 0.02
        except Exception:
            pass

        a = 0
        w = 0
        s = 0
        d = 0
        
    pygame.display.update()

    # draw agent status
    if agent is not None:
        try:
            font = pygame.font.SysFont(None, 24)
            status = 'TRAIN' if AGENT_TRAIN else 'AUTO'
            text = font.render(f'Agent: {status} steps={TOTAL_TRAIN_STEPS}', True, (255,255,0))
            screen.blit(text, (10, 10))
            pygame.display.update()
        except Exception:
            pass

pygame.quit()




##########################################################################
#################################-readme-#################################
# the w, a, s and d variables are used for movement.
# the prevX and prevY lists are where the snake has moved before.
# the mat1 and mat2 are where the food is.
# obstructions as mentioned in the project proposal are located at 
# wallX and wallY.
# reward is the variable for the reward, it should be tweaked probably
# that should be all the ai needs to be aware of.
#
# i probably also add so that the ai can know what it did wrong when 
# it fails.