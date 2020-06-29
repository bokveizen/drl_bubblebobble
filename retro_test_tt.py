import retro
import numpy as np
import pickle
import time
import argparse


def action_one_step(n):
    # 0: B(Fire), 1: Left, 2: Right, 3: A(Jump), 4: Left Jump, 5: Right Jump
    if n == 0:
        return np.int8([1, 0, 0, 0, 0, 0, 0, 0, 0])
    if n == 1:
        return np.int8([1, 0, 0, 0, 0, 0, 1, 0, 0])
    if n == 2:
        return np.int8([1, 0, 0, 0, 0, 0, 0, 1, 0])
    if n == 3:
        return np.int8([1, 0, 0, 0, 0, 0, 0, 0, 1])
    if n == 4:
        return np.int8([1, 0, 0, 0, 0, 0, 1, 0, 1])
    if n == 5:
        return np.int8([1, 0, 0, 0, 0, 0, 0, 1, 1])
    return np.int8([0, 0, 0, 0, 0, 0, 0, 0, 0])


def action(n):
    # 0: B(Fire), 1: Left, 2: Right, 3: A(Jump), 4: Left Jump, 5: Right Jump
    # if n == 0:
    #     return [action_one_step(0)] * 5 + [action_one_step(-1)] * 5
    # if n == 1:
    #     return [action_one_step(1)] * 5 + [action_one_step(-1)] * 5
    # if n == 2:
    #     return [action_one_step(2)] * 5 + [action_one_step(-1)] * 5
    # if n == 3:
    #     return [action_one_step(3)] * 5 + [action_one_step(-1)] * 5
    # if n == 4:
    #     return [action_one_step(4)] * 5 + [action_one_step(-1)] * 5
    # if n == 5:
    #     return [action_one_step(5)] * 5 + [action_one_step(-1)] * 5
    return ([action_one_step(-1)] + [action_one_step(n)]) * 5


def test(level=1, display=400):
    env = retro.make(game='BubbleBobble-Nes', state='Level{:02d}'.format(level))
    obs = env.reset()
    env.render()
    action_buffer = []
    filename = 'saved_acts_MCTS_max/lvl1to2_score866_acts.pickle'
    with open(filename, 'rb') as handle:
        action_array = pickle.load(handle)
    display = display
    info = None
    while action_array:
        if not action_buffer:
            action_buffer += action(action_array.pop(0))
        obs, rew, done, info = env.step(action_buffer.pop())
        if display > 0:
            time.sleep(1 / display)
            env.render()
    print(info)
    input()
    time.sleep(1)
    env.close()


if __name__ == "__main__":
    test()
