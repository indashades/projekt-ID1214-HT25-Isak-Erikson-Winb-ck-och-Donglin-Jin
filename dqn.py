import random
from collections import deque
import pickle
import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim

class ReplayBuffer:
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        # ensure states are numeric arrays with consistent dtype and 3-channel shape
        def to_three(x):
            try:
                arr = np.array(x, dtype=np.float32)
            except Exception:
                arr = np.asarray(x)
            if isinstance(arr, np.ndarray):
                if arr.ndim == 2:
                    h, w = arr.shape
                    out = np.zeros((3, h, w), dtype=np.float32)
                    out[0] = (arr == 1).astype(np.float32)
                    out[1] = (arr == 2).astype(np.float32)
                    out[2] = (arr == 3).astype(np.float32)
                    return out
                if arr.ndim == 3 and arr.shape[0] == 1:
                    return np.repeat(arr, 3, axis=0).astype(np.float32)
                if arr.ndim == 3 and arr.shape[0] == 3:
                    return arr.astype(np.float32)
            # fallback: try to coerce to float32 array
            return np.array(arr, dtype=np.float32)

        s = to_three(state)
        ns = to_three(next_state)
        self.buffer.append((s, action, float(reward), ns, bool(done)))

    def sample(self, batch_size):
        # sample until we have batch_size compatible numeric states (same shape)
        if batch_size > len(self.buffer):
            raise ValueError('Not enough samples in buffer')
        selected = []
        attempts = 0
        base_shape = None
        while len(selected) < batch_size and attempts < batch_size * 10:
            s, a, r, ns, d = random.choice(self.buffer)
            try:
                s_arr = np.array(s, dtype=np.float32)
                ns_arr = np.array(ns, dtype=np.float32)
            except Exception:
                attempts += 1
                continue
            if s_arr.shape != ns_arr.shape:
                attempts += 1
                continue
            if base_shape is None:
                base_shape = s_arr.shape
            if s_arr.shape != base_shape:
                attempts += 1
                continue
            selected.append((s_arr, a, r, ns_arr, d))
            attempts += 1

        if len(selected) < batch_size:
            raise ValueError('Could not gather enough compatible samples')

        states, actions, rewards, next_states, dones = zip(*selected)
        states_arr = np.stack(states)
        next_states_arr = np.stack(next_states)
        return states_arr, np.array(actions, dtype=np.int64), np.array(rewards, dtype=np.float32), next_states_arr, np.array(dones, dtype=np.bool_)

    def __len__(self):
        return len(self.buffer)

class DQNNet(nn.Module):
    def __init__(self, input_shape, n_actions):
        super().__init__()
        c, h, w = input_shape
        # small ConvNet to capture spatial structure
        self.conv = nn.Sequential(
            nn.Conv2d(c, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
        )
        conv_out = 64 * h * w
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(conv_out, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, n_actions)
        )

    def forward(self, x):
        # expect x shape (batch, c, h, w)
        x = self.conv(x)
        return self.fc(x)

class DQNAgent:
    def __init__(self, input_shape, n_actions, lr=1e-3, gamma=0.99, device=None):
        self.device = device or (torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu'))
        self.net = DQNNet(input_shape, n_actions).to(self.device)
        self.target = DQNNet(input_shape, n_actions).to(self.device)
        self.target.load_state_dict(self.net.state_dict())
        self.optimizer = optim.Adam(self.net.parameters(), lr=lr)
        self.gamma = gamma
        self.buffer = ReplayBuffer()
        self.n_actions = n_actions

    def save(self, path, save_buffer=False, buffer_path=None):
        data = {
            'model': self.net.state_dict(),
            'target': self.target.state_dict(),
            'optimizer': self.optimizer.state_dict()
        }
        torch.save(data, path)
        if save_buffer and buffer_path is not None:
            with open(buffer_path, 'wb') as f:
                pickle.dump(self.buffer.buffer, f)

    def load(self, path, load_buffer=False, buffer_path=None, map_location=None):
        map_location = map_location or self.device
        ckpt = torch.load(path, map_location=map_location)
        model_state = ckpt.get('model', {})
        cur_state = self.net.state_dict()

        # adapt conv input channel mismatch by repeating weights if necessary
        for k, v in list(model_state.items()):
            if k in cur_state and v.shape != cur_state[k].shape:
                # handle first conv weight (conv.0.weight)
                if k.endswith('conv.0.weight') or k == 'conv.0.weight':
                    try:
                        old = v
                        new_shape = cur_state[k].shape
                        if old.ndim == 4 and len(new_shape) == 4:
                            out_ch, in_ch_old, kh, kw = old.shape
                            out_ch2, in_ch_new, kh2, kw2 = new_shape
                            if out_ch == out_ch2 and kh == kh2 and kw == kw2 and in_ch_new > in_ch_old:
                                reps = int(np.ceil(in_ch_new / in_ch_old))
                                expanded = np.tile(old, (1, reps, 1, 1))[:, :in_ch_new, :, :]
                                model_state[k] = torch.tensor(expanded, dtype=v.dtype)
                                continue
                    except Exception:
                        pass
                # cannot adapt this key, remove it so load won't fail
                print(f"Skipping incompatible weight '{k}' (saved {v.shape}, expected {cur_state[k].shape})")
                del model_state[k]

        # load adapted model state
        try:
            self.net.load_state_dict(model_state, strict=False)
        except Exception as e:
            print('Warning: partial model load failed:', e)
            self.net.load_state_dict({k: v for k, v in model_state.items() if k in cur_state}, strict=False)

        if 'target' in ckpt:
            try:
                self.target.load_state_dict(ckpt['target'])
            except Exception:
                self.target.load_state_dict(self.net.state_dict())
        else:
            self.target.load_state_dict(self.net.state_dict())
        # Do not load optimizer state to avoid shape mismatches when adapting model.
        if load_buffer and buffer_path is not None and os.path.exists(buffer_path):
            with open(buffer_path, 'rb') as f:
                items = pickle.load(f)
            # ensure states in buffer have consistent numeric shapes; convert single-channel grids to 3-channel one-hot
            fixed = []
            for s, a, r, ns, d in items:
                try:
                    s_arr = np.array(s, dtype=np.float32)
                except Exception:
                    s_arr = np.asarray(s)
                try:
                    ns_arr = np.array(ns, dtype=np.float32)
                except Exception:
                    ns_arr = np.asarray(ns)
                def to_three(x):
                    if isinstance(x, np.ndarray) and x.ndim == 2:
                        h, w = x.shape
                        out = np.zeros((3, h, w), dtype=np.float32)
                        out[0] = (x == 1).astype(np.float32)
                        out[1] = (x == 2).astype(np.float32)
                        out[2] = (x == 3).astype(np.float32)
                        return out
                    return x.astype(np.float32) if isinstance(x, np.ndarray) else np.array(x, dtype=np.float32)
                s_fixed = to_three(s_arr)
                ns_fixed = to_three(ns_arr)
                fixed.append((s_fixed, a, float(r), ns_fixed, bool(d)))
            self.buffer.buffer = deque(fixed, maxlen=self.buffer.buffer.maxlen)

    def select_action(self, state, eps=0.1):
        if random.random() < eps:
            return random.randrange(self.n_actions)
        state_t = torch.tensor(state, dtype=torch.float32, device=self.device).unsqueeze(0)
        with torch.no_grad():
            q = self.net(state_t)
        return int(q.argmax().item())

    def update(self, batch_size=64):
        if len(self.buffer) < batch_size:
            return 0.0
        try:
            states, actions, rewards, next_states, dones = self.buffer.sample(batch_size)
        except Exception:
            return 0.0
        # ensure sampled batches have shape (B, C, H, W) with C==3
        # handle (B, H, W)
        if isinstance(states, np.ndarray) and states.ndim == 3:
            b, h, w = states.shape
            new = np.zeros((b, 3, h, w), dtype=np.float32)
            for i in range(b):
                s = states[i]
                new[i, 0] = (s == 1).astype(np.float32)
                new[i, 1] = (s == 2).astype(np.float32)
                new[i, 2] = (s == 3).astype(np.float32)
            states = new
        # handle (B, 1, H, W) by repeating channel
        if isinstance(states, np.ndarray) and states.ndim == 4 and states.shape[1] == 1:
            states = np.repeat(states, 3, axis=1)

        if isinstance(next_states, np.ndarray) and next_states.ndim == 3:
            b, h, w = next_states.shape
            newn = np.zeros((b, 3, h, w), dtype=np.float32)
            for i in range(b):
                s = next_states[i]
                newn[i, 0] = (s == 1).astype(np.float32)
                newn[i, 1] = (s == 2).astype(np.float32)
                newn[i, 2] = (s == 3).astype(np.float32)
            next_states = newn
        if isinstance(next_states, np.ndarray) and next_states.ndim == 4 and next_states.shape[1] == 1:
            next_states = np.repeat(next_states, 3, axis=1)

        states_t = torch.tensor(states, dtype=torch.float32, device=self.device)
        next_t = torch.tensor(next_states, dtype=torch.float32, device=self.device)
        actions_t = torch.tensor(actions, dtype=torch.int64, device=self.device).unsqueeze(1)
        rewards_t = torch.tensor(rewards, dtype=torch.float32, device=self.device).unsqueeze(1)
        dones_t = torch.tensor(dones, dtype=torch.float32, device=self.device).unsqueeze(1)

        q_values = self.net(states_t).gather(1, actions_t)
        with torch.no_grad():
            q_next = self.target(next_t).max(1)[0].unsqueeze(1)
            q_target = rewards_t + (1 - dones_t) * self.gamma * q_next

        loss = nn.functional.mse_loss(q_values, q_target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        return loss.item()

    def sync_target(self):
        self.target.load_state_dict(self.net.state_dict())
