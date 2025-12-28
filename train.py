import os
import numpy as np
import torch
from snake_env import SnakeEnv
from dqn import DQNAgent

# checkpoint settings
CKPT_DIR = 'checkpoints'
CKPT_MODEL = os.path.join(CKPT_DIR, 'dqn.pth')
CKPT_BUFFER = os.path.join(CKPT_DIR, 'replay.pkl')

os.makedirs(CKPT_DIR, exist_ok=True)

def preprocess(obs):
    # obs may be multi-channel or single-channel grid; normalize to float channels
    arr = np.array(obs, dtype=np.float32)
    if arr.ndim == 2:
        # convert single-channel grid values into 3 one-hot channels
        h, w = arr.shape
        out = np.zeros((3, h, w), dtype=np.float32)
        out[0] = (arr == 1).astype(np.float32)  # snake
        out[1] = (arr == 2).astype(np.float32)  # food
        out[2] = (arr == 3).astype(np.float32)  # wall (if any)
        return out
    return arr  # assume already (C,H,W)

def train(episodes=500, steps_per_ep=10000):
    env = SnakeEnv(size=12)
    # train with 3-channel observations (snake/food/wall)
    obs_shape = (3, env.size, env.size)
    agent = DQNAgent(obs_shape, env.action_space)

    # try to load existing checkpoint
    if os.path.exists(CKPT_MODEL):
        try:
            agent.load(CKPT_MODEL, load_buffer=True, buffer_path=CKPT_BUFFER)
            print(f"Loaded checkpoint from {CKPT_MODEL}")
        except Exception as e:
            print(f"Failed loading checkpoint: {e}")

    # hyperparams
    eps_start = 1.0
    eps_final = 0.05
    eps_decay = 5000.0  # slower, per-step decay
    warmup_steps = 200  # smaller warmup for quicker retrain
    updates_per_step = 1
    sync_target_steps = 500

    total_steps = 0

    for ep in range(episodes):
        obs = env.reset()
        obs_proc = preprocess(obs)
        total_reward = 0.0
        for t in range(steps_per_ep):
            total_steps += 1
            # per-step epsilon decay
            eps = eps_final + (eps_start - eps_final) * np.exp(-1.0 * total_steps / eps_decay)
            action = agent.select_action(obs_proc, eps=eps)
            next_obs, reward, done, info = env.step(action)
            next_proc = preprocess(next_obs)
            agent.buffer.push(obs_proc, action, float(reward), next_proc, done)

            # only update after warmup
            if len(agent.buffer) >= warmup_steps:
                for _ in range(updates_per_step):
                    loss = agent.update()

            obs_proc = next_proc
            total_reward += reward
            if total_steps % sync_target_steps == 0:
                agent.sync_target()
            if done:
                break

        # periodic checkpointing and logging
        if ep % 10 == 0:
            try:
                agent.save(CKPT_MODEL, save_buffer=True, buffer_path=CKPT_BUFFER)
            except Exception as e:
                print(f"Failed saving checkpoint: {e}")
        print(f"ep={ep} reward={total_reward:.2f} steps={t+1} score={info.get('score',0)} eps={eps:.3f}")

    # final save at end of training
    try:
        agent.save(CKPT_MODEL, save_buffer=True, buffer_path=CKPT_BUFFER)
        print(f"Saved final checkpoint to {CKPT_MODEL}")
    except Exception as e:
        print(f"Failed saving final checkpoint: {e}")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--episodes', type=int, default=200)
    p.add_argument('--steps', type=int, default=200)
    args = p.parse_args()
    print(f"Starting training: episodes={args.episodes} steps_per_ep={args.steps}")
    train(episodes=args.episodes, steps_per_ep=args.steps)
