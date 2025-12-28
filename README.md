Quick DQN snake trainer

Files added:
- `snake_env.py` — simple grid-based snake environment (no pygame)
- `dqn.py` — DQN agent, network, and replay buffer (PyTorch)
- `train.py` — training loop to run episodes
- `requirements.txt` — minimal Python deps

How to run (Windows PowerShell):

```powershell
python -m pip install -r requirements.txt
python train.py
```

Notes:
- Environment is simplified to a grid to make training easy.
- You can adapt `snake_env.py` to mirror your pygame logic and then use the same `dqn.py`/`train.py`.
