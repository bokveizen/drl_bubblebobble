import argparse

import retro
import numpy as np
import time
import random
import pickle
import os
from multiprocessing import Pool, cpu_count

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--level', type=int, default=1, help="the starting level")
parser.add_argument('-r', '--random_run_times', type=int, default=1, help="rollout running times")
parser.add_argument('-s', '--single_state_run_times', type=int, default=20, help="expansion times in each tree level")
args = parser.parse_args()

max_enemies = [-1, 3, 4, 4, 6, 4, 4, 4, 4, 7, 7, 7, 6, 7, 7, 7, 7, 7, 6, 7, 5, 7, 4, 5, 7, 6, 7, 7, 7, 6, 7, 7, 7, 6,
               7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 6, 7, 7, 7, 6, 7, 6, 7, 7, 7, 7, 7, 6, 5, 7, 7, 4, 6, 7, 4, 6, 7, 7, 5,
               7, 7, 5, 7, 7, 7, 4, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 4, 7, 7, 7, 4, 6, 7, 7, 7, 7, 5, 6, 7, 7, 7]
action_space_size = 6
random_run_times = args.random_run_times
exploration_const = 0.  # np.sqrt(0.5)
loop_times_per_state = args.single_state_run_times
level_up_infos = []


class State:
    def __init__(self, game_name='BubbleBobble-Nes', start_lvl=1, env=None, acts=None, root=None, parent=None):
        # root node init.
        if acts is None:
            acts = []
        if root is None:
            root = self
        if env is None:
            env = retro.make(game=game_name, state='Level{:02d}'.format(start_lvl))
            env.reset()
        # game info.
        self.game_name = env.gamename
        self.start_lvl = start_lvl
        self.root = root
        self.acts = acts
        self.env_state = env.em.get_state()
        self.enemies, self.level, self.lives, self.score = env.data.lookup_all().values()
        env.close()
        # state eval.
        self.terminal = 0
        self.value = 0.
        if self.acts:
            self.terminal_cal()
            self.value_cal()
        # if self.terminal == 2:
        #     print('Level up from level {}.'.format(self.start_lvl))
        #     print('acts:', acts)
        # tree info.
        self.parent = parent
        self.children = [None] * action_space_size
        self.visit_times = 0
        self.mean_score = 0
        self.max_score = 0
        # print(self)

    def terminal_cal(self):  # 0:Non-terminal, 1:lives down, 2:level up
        if self.lives < self.root.lives:
            self.terminal = 1
        elif self.level > self.root.level:
            self.terminal = 2
        else:
            self.terminal = 0

    def value_cal(self):
        if self.terminal == 1:
            self.value = -1.
        elif self.terminal == 2:
            self.value = 1.
        else:
            self.value = 1. - (self.enemies / max_enemies[self.level]) ** 2

    def selection_p(self):
        if self.terminal:
            return 0.
        return self.max_score + exploration_const * np.sqrt(np.log(self.parent.visit_times) / self.visit_times)
        # return self.mean_score + exploration_const * np.sqrt(np.log(self.parent.visit_times) / self.visit_times)

    def full_children(self):
        return all(self.children)

    def best_children(self):
        best_children_index = np.argmax([c.selection_p() for c in self.children])
        return self.children[best_children_index]

    def selection(self):
        cur = self
        while cur:
            if cur.full_children():
                p_list = [c.selection_p() for c in cur.children]
                cur = cur.children[uneven_random(p_list)]
            else:
                return cur.next()  # expansion, simulation, and back-propagation

    def next(self):  # expansion in standard MCTS
        choice_array = [i for i in range(action_space_size) if not self.children[i]]
        action_index = random.choice(choice_array)
        action_buffer = action(action_index)
        env = retro.make(game=self.game_name)
        env.reset()
        env.em.set_state(self.env_state)
        while action_buffer:
            obs, rew, done, info = env.step(action_buffer.pop())
        next_state = State(self.game_name, self.start_lvl, env, self.acts + [action_index], self.root, self)
        next_state.random_run()
        self.children[action_index] = next_state
        return next_state

    def random_run(self):  # simulation & back-propagation in standard MCTS
        env = retro.make(game=self.game_name)
        env.reset()
        res_list = []
        for i in range(random_run_times):
            action_done = []
            action_buffer = []
            action_index = None
            env.reset()
            env.em.set_state(self.env_state)  # start from the current state
            terminal = False
            while not terminal:
                if not action_buffer:
                    if action_index is None:  # first step
                        action_index = random.randint(0, 5)
                        action_buffer += action(action_index)
                    else:
                        action_done.append(action_index)
                        new_enemies, new_level, new_lives, new_score = env.data.lookup_all().values()
                        if new_level > self.root.level or new_lives < self.root.lives:  # level up or lives down, terminal

                            if new_level > self.level:  # record level-up infos
                                terminal_info = (self.acts + action_done, new_enemies, new_level, new_lives, new_score)
                                # print(terminal_info)
                                level_up_infos.append(terminal_info)
                            else:  # failed scores are half-weighted
                                terminal_info = (
                                    self.acts + action_done, new_enemies, new_level, new_lives, new_score // 2
                                )
                            res_list.append(terminal_info)
                            terminal = True
                        action_index = random.randint(0, 5)
                        action_buffer += action(action_index)
                obs, rew, done, info = env.step(action_buffer.pop())
        env.close()
        # back-propagation
        cur = self
        terminal_score_mean = sum(info[-1] for info in res_list) / random_run_times
        terminal_score_max = max(info[-1] for info in res_list)
        while cur:
            cur.visit_times, cur.mean_score = cur.visit_times + 1, (
                    cur.visit_times * cur.mean_score + terminal_score_mean) / (cur.visit_times + 1)
            cur.max_score = max(cur.max_score, terminal_score_max)
            cur = cur.parent

    def __eq__(self, other):
        return self.start_lvl == other.start_lvl and self.acts == other.acts

    def __hash__(self):
        return hash(str(self.start_lvl) + str(self.acts))

    def __repr__(self):
        return 'Env starting from level {}, using {} steps, current state: enemies={}, level={}, lives={}, score={}, ' \
               'parent id={}' \
            .format(self.start_lvl, len(self.acts), self.enemies, self.level, self.lives, self.score, hash(self.parent))


def uneven_random(p_list):
    range_list = [0]
    for p in p_list:
        range_list.append(range_list[-1] + p)
    rand_num = random.uniform(0, range_list[-1])
    for i in range(len(p_list)):
        if range_list[i] <= rand_num < range_list[i + 1]:
            return i
    return len(p_list) - 1


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


def retro_search(process_id, game_name='BubbleBobble-Nes', level=1):
    print(process_id, 'started.')
    root_state = State(game_name=game_name, start_lvl=level)
    cur_state = root_state
    best_score = 0
    while not cur_state.terminal:
        print('cur_state', cur_state)
        for _ in range(loop_times_per_state):
            cur_state.selection()
        cur_state = cur_state.best_children()
        if level_up_infos:
            best_index = int(np.argmax([info[-1] for info in level_up_infos]))
            cur_best_score = level_up_infos[best_index][-1]
            print(process_id, level_up_infos[best_index][1:])
            # print(level_up_infos[best_index][0])
            if cur_best_score > best_score:
                best_score = cur_best_score
                cur_acts = level_up_infos[best_index][0]
                cur_level = level_up_infos[best_index][2]
                file_name = 'saved_acts_MCTS_max/lvl{}to{}_score{}_acts.pickle'.format(level, cur_level, best_score)
                with open(file_name, 'wb') as handle:
                    pickle.dump(cur_acts, handle)
    print(process_id, 'exited.')


if __name__ == '__main__':
    os.makedirs('saved_acts_MCTS_max', exist_ok=True)
    retro_search(0, level=args.level)
    # cpu_num = cpu_count()
    # pool_size = cpu_num // 2
    # search_level_list = range(args.level, 100)
    # search_level_num = len(search_level_list)
    # p = Pool(pool_size)
    # os.makedirs('saved_acts_MCTS', exist_ok=True)
    # for i in range(search_level_num):
    #     p.apply_async(retro_search, (i + 1, 'BubbleBobble-Nes', i + 1))
    # p.close()
    # p.join()
