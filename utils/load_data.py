import os


def match_pathes(name_filter=None):
    paths = []
    path = r"..\\matches"
    for dir_name in os.listdir(path):
            league_path = os.path.join(path, dir_name)
            if os.path.isdir(league_path):
                for season in os.listdir(league_path):
                    season_path = os.path.join(league_path, season)
                    if os.path.isdir(season_path):
                        for date_name in os.listdir(season_path):
                            date_path = os.path.join(season_path, date_name)
                            if os.path.isdir(date_path):
                                for match_name in os.listdir(date_path):
                                    match_path = os.path.join(
                                        date_path, match_name)
                                    if os.path.isdir(match_path) and match_name not in [
                                        '.ipynb_checkpoints']:
                                        if name_filter is not None and any(i in match_path for i in name_filter):
                                        # and 'England-Premier-League' in match_path:
                                            paths.append(match_path)
                                        elif name_filter is None:
                                            paths.append(match_path)
    paths = sorted(paths)
    return paths


if __name__ == '__main__':
    match_pathes(['Liverpool','2020-2021'])
