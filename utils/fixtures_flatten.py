import os
from datetime import date

import pandas as pd


def fixture_flatten(team_name=None, drop_fixture=None):
    df = pd.DataFrame(columns=['season', 'date', 'home', 'away', 'path'])
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
                                    if (team_name is not None and team_name in match_path) or team_name is None:
                                        tmp = {'season': season, 'date': date.fromisoformat(date_name),
                                               'home': match_name.split('-')[0], 'away': match_name.split('-')[1],
                                               'path': os.path.join(match_path, 'match.json')}
                                        df = df.append(tmp, ignore_index=True)
                                    # and 'England-Premier-League' in match_path:
    df = df.sort_values(by="date", ascending=True)
    if drop_fixture is not None:
        df.to_csv(drop_fixture)
    return df


if __name__ == '__main__':
    fixture_result = fixture_flatten('Liverpool')
    print(fixture_result)
