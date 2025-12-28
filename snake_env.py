import random
import numpy as np

class SnakeEnv:
    """Simple grid-based Snake environment (Gym-like).

    Observation: (H, W) int grid where 0=empty, 1=snake, 2=food, 3=wall
    Action space: 0=left,1=right,2=up,3=down
    """
    def __init__(self, size=20, init_length=3):
        self.size = size
        self.init_length = init_length
        self.reset()

        # proximity reward weight (positive when getting closer to food)
        self.proximity_reward = 0.02

    def reset(self):
        self.grid = np.zeros((self.size, self.size), dtype=np.int8)
        mid = self.size // 2
        self.snake = [(mid + i, mid) for i in range(self.init_length)][::-1]
        for x, y in self.snake:
            self.grid[y, x] = 1
        self.direction = (-1, 0)  # left
        self._place_food()
        self.done = False
        self.score = 0
        # track previous distance to food for proximity reward
        if self.food is not None:
            hx, hy = self.snake[0]
            fx, fy = self.food
            self.prev_dist = abs(hx - fx) + abs(hy - fy)
        else:
            self.prev_dist = None
        return self._get_obs()

    def _place_food(self):
        empties = list(zip(*np.where(self.grid == 0)))
        if not empties:
            self.food = None
            return
        y, x = random.choice(empties)
        self.grid[y, x] = 2
        self.food = (x, y)

    def step(self, action):
        if self.done:
            return self._get_obs(), 0, True, {}

        if action == 0:
            desired = (-1, 0)
        elif action == 1:
            desired = (1, 0)
        elif action == 2:
            desired = (0, -1)
        elif action == 3:
            desired = (0, 1)
        else:
            desired = self.direction

        # prevent immediate reverse
        if (desired[0] == -self.direction[0] and desired[1] == -self.direction[1]):
            desired = self.direction
        self.direction = desired

        head_x, head_y = self.snake[0]
        nx = head_x + self.direction[0]
        ny = head_y + self.direction[1]

        # check collisions
        if nx < 0 or ny < 0 or nx >= self.size or ny >= self.size:
            self.done = True
            return self._get_obs(), -1.0, True, {}

        cell = self.grid[ny, nx]
        if cell == 1:
            self.done = True
            return self._get_obs(), -1.0, True, {}

        # small step penalty to encourage finding food faster
        reward = -0.01
        ate = False
        if cell == 2:
            reward = reward + 1.0
            ate = True
            self.score += 1

        # move head
        self.snake.insert(0, (nx, ny))
        self.grid[ny, nx] = 1
        # proximity reward: positive if moved closer to food
        if self.food is not None and self.prev_dist is not None:
            fx, fy = self.food
            new_dist = abs(nx - fx) + abs(ny - fy)
            if new_dist < self.prev_dist:
                reward += self.proximity_reward
            self.prev_dist = new_dist

        if not ate:
            tx, ty = self.snake.pop()
            self.grid[ty, tx] = 0
        else:
            self._place_food()
            # update prev_dist after eating (new food placed)
            if self.food is not None:
                fx, fy = self.food
                hx, hy = self.snake[0]
                self.prev_dist = abs(hx - fx) + abs(hy - fy)

        return self._get_obs(), reward, self.done, {"score": self.score}

    def _get_obs(self):
        return np.copy(self.grid)

    def render(self):
        for y in range(self.size):
            print(''.join(['.#O*'[self.grid[y, x]] for x in range(self.size)]))
        print(f"score={self.score}\n")

    @property
    def action_space(self):
        return 4

    @property
    def observation_shape(self):
        return (self.size, self.size)
