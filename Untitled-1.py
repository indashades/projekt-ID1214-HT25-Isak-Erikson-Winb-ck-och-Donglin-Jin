import pygame
import random

pygame.init()
screenWidth = 800
screenHight = 800
#wasd: we just have the ai change these to true for movement

#under här är variabler att reseta när spelet är över{
a=0
w=0
s=0
d=0

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
            if not (mat1>solidSnake.x-10 and mat1<solidSnake.x+20 and mat2>solidSnake.y-10 and mat2<solidSnake.y+20 or screen.get_at((mat1,mat2))==(255,0,0,255) or screen.get_at((mat1+10,mat2))==(255,0,0,255) or screen.get_at((mat1,mat2+10))==(255,0,0,255) or screen.get_at((mat1+10,mat2+10))==(255,0,0,255)):
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
    if solidSnake.x<0 or solidSnake.x>800 or solidSnake.y<0 or solidSnake.y>800:
        #ran out of bounds
        reward=-8
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
    elif screen.get_at((solidSnake.x,solidSnake.y))==(255,245,255,255) or screen.get_at((solidSnake.x+10,solidSnake.y))==(255,245,255,255) or screen.get_at((solidSnake.x,solidSnake.y+10))==(255,245,255,255) or screen.get_at((solidSnake.x+10,solidSnake.y+10))==(255,245,255,255):
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
    elif screen.get_at((solidSnake.x,solidSnake.y))==(255,0,0,255) or screen.get_at((solidSnake.x+10,solidSnake.y))==(255,0,0,255) or screen.get_at((solidSnake.x,solidSnake.y+10))==(255,0,0,255) or screen.get_at((solidSnake.x+10,solidSnake.y+10))==(255,0,0,255):
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
    
    #movement, i will give this to both ai and observers of the ai for now
    key = pygame.key.get_pressed()
    if key[pygame.K_a] == True:
        a=1
    elif key[pygame.K_s] == True:
        s=1
    elif key[pygame.K_d] == True:
        d=1
    elif key[pygame.K_w] == True:
        w=1
    elif key[pygame.K_q] == True:
        time=120
    elif key[pygame.K_e] == True:
        time=1000000
    if w or a or s or d:
        prevX.insert(0, solidSnake.x)
        prevY.insert(0, solidSnake.y)
        solidSnake.move_ip(d-a,s-w)
        a=0
        w=0
        s=0
        d=0
        
    pygame.display.update()

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