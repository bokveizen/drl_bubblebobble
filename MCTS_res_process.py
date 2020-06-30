import os


def find_best_acts(path, level, aux):
    if level == 99:
        level_acts_files = [f for f in os.listdir(path) if 'lvl99' in f]
    else:
        level_acts_files = [f for f in os.listdir(path) if 'lvl{}to{}_'.format(level, level + 1) in f]
    if level_acts_files:
        return os.path.join(path, max(level_acts_files, key=lambda f: int(f[f.find('score') + 5:f.find('acts') - 1])))
    return '{}/lvl{}_acts.pickle'.format(aux, level)


auxiliary_dir = 'saved_acts_one_level_only'
acts_dir = 'saved_acts_MCTS'
for lvl in range(1, 100):
    f = find_best_acts(acts_dir, lvl, auxiliary_dir)
    f = f[15:]
    print(lvl, int(f[f.find('score') + 5:f.find('acts') - 1]))
