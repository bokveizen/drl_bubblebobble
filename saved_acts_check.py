from pathlib import Path
import pickle

saved_path = Path('saved_acts_one_level_only')
for i in range(1, 100):
    if not (saved_path / 'lvl{}_acts.pickle'.format(i)).exists():
        print('lvl', i, 'does not exists.')
    # else:
    #     with open('saved_acts_one_level_only/lvl{}_acts.pickle'.format(i), 'rb') as handle:
    #         action_array = pickle.load(handle)
    #     print('lvl', i, 'has a {}-step solution'.format(len(action_array)))
