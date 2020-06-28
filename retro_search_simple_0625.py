import retro
import numpy as np
import time
import random
import pickle
import os
from multiprocessing import Pool, cpu_count
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


def action(n, repeat=5):
    # 0: B(Fire), 1: Left, 2: Right, 3: A(Jump), 4: Left Jump, 5: Right Jump
    return ([action_one_step(-1)] + [action_one_step(n)]) * repeat


def search(index, level):
    env = retro.make(game='BubbleBobble-Nes', state='Level{:02d}'.format(level))
    obs = env.reset()
    max_enemies_list = [0, 3, 4, 4, 6, 4, 4, 4, 4, 7, 7, 7, 6, 7, 7, 7, 7, 7, 6, 7, 5, 7, 4, 5, 7, 6, 7, 7, 7, 6, 7, 7,
                        7, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 6, 7, 7, 7, 6, 7, 6, 7, 7, 7, 7, 7, 6, 5, 7, 7, 4, 6, 7, 4,
                        6, 7, 7, 5, 7, 7, 5, 7, 7, 7, 4, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 4, 7, 7, 7, 4, 6, 7, 7, 7, 7, 5,
                        6, 7, 7, 7]
    min_enemies_achieved = max_enemies_list[level]
    remember_state = None
    remember_acts = []
    rem_enemies, rem_level, rem_lives, rem_score = env.data.lookup_all().values()
    display = 0
    action_index_lists_saved = []
    action_index_list = []
    if action_index_lists_saved:
        action_index_list = action_index_lists_saved[-1][:]
    if not action_index_list:
        action_index = None
        action_buffer = []
    else:
        action_index = action_index_list.pop(0)
        action_buffer = []
        action_buffer += action(action_index)
    action_done = []
    zero_enemy_count = 0
    while not os.path.exists('saved_acts_one_level_only/lvl{}_acts.pickle'.format(level)):
        if not action_buffer:
            if action_index is None:  # first step
                action_index = random.randint(0, 5)
                action_buffer += action(action_index)
            else:
                action_done.append(action_index)
                new_enemies, new_level, new_lives, new_score = env.data.lookup_all().values()
                if new_enemies == 0:
                    zero_enemy_count += 1
                if new_lives < rem_lives:  # lives down, reset
                    print(index, 'info', env.data.lookup_all())
                    # if action_index_lists_saved:
                    #     print('action_index_lists_saved', len(action_index_lists_saved), action_index_lists_saved)
                    # print('action_done', len(action_done), action_done)
                    # print('remember_acts', len(remember_acts), remember_acts)
                    obs = env.reset()
                    if remember_state is not None:
                        env.em.set_state(remember_state)
                    if action_index_lists_saved:
                        action_index_list = action_index_lists_saved[-1][:]
                    if not action_index_list:
                        action_index = None
                        action_buffer = []
                    else:
                        action_index = action_index_list.pop(0)
                        action_buffer = []
                        action_buffer += action(action_index)
                    action_done = []
                    zero_enemy_count = 0
                    continue
                elif new_level > rem_level or (rem_level == 99 and zero_enemy_count >= 1000):  # level up, save
                    remember_acts += action_done
                    with open('saved_acts_one_level_only/lvl{}_acts.pickle'.format(level), 'wb') as handle:
                        pickle.dump(remember_acts, handle)
                    break
                elif new_enemies < min_enemies_achieved:
                    min_enemies_achieved = new_enemies
                    action_index_lists_saved.append(action_done[:])
                if not action_index_list:
                    action_index = random.randint(0, 5)
                else:
                    action_index = action_index_list.pop(0)
                action_buffer += action(action_index)
        obs, rew, done, info = env.step(action_buffer.pop())
        if display > 0:
            env.render()
            time.sleep(1 / display)
    env.close()
    print(index, 'Exited.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--level', type=int, default=1, help="the starting level")
    args = parser.parse_args()

    cpu_num = cpu_count()
    pool_size = cpu_num // 2
    test_level_list = range(args.level, 100)
    test_level_num = len(test_level_list)
    p = Pool(pool_size)
    os.makedirs('saved_acts_one_level_only', exist_ok=True)
    for i in range(pool_size * test_level_num):
        p.apply_async(search, (i, test_level_list[i // pool_size]))
    p.close()
    p.join()
