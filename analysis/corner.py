from copy import deepcopy
from datetime import date

from utils.fixtures_flatten import fixture_flatten
import pandas as pd
import lightgbm as lgb

sets = ['total_corner', 'home_corner_ma', 'home_tt_coner_ma', 'away_corner_ma',
        'away_total_corner_ma', 'home_wide_pass', 'home_cross',
        'away_wide_pass', 'away_cross']


def get_two_team_paths(team_a, team_b):
    return fixture_flatten(team_a), fixture_flatten(team_b)


def get_match_data(match_date, home_name, away_name,fixtures=None,filter_=None,n=5):
    rel_fixture_rows = fixtures
    if fixtures is None:
        rel_fixture_rows = pd.read_csv('../statistics/fixture_table.csv')
    if filter_ is not None:
        rel_fixture_rows = rel_fixture_rows[rel_fixture_rows.apply(lambda x: filter_ in x['path'], axis=1)]
    df = pd.DataFrame(columns=sets.remove('total_corner'))
    last_n_home_corner = get_last_n_game_corner(home_name, match_date, n=n, fixtures=rel_fixture_rows,
                                                filter_=home_name)
    last_n_away_corner = get_last_n_game_corner(away_name, match_date, n=n, fixtures=rel_fixture_rows,
                                                filter_=away_name)
    if last_n_home_corner.shape[0] < n or last_n_away_corner.shape[0] < n:
        raise ValueError('No data!')
    home_ma = last_n_home_corner['teamCorner'].mean()
    home_tt_ma = last_n_home_corner['sum_corner'].mean()
    away_ma = last_n_away_corner['teamCorner'].mean()
    away_tt_ma = last_n_away_corner['sum_corner'].mean()
    home_wide_pass, home_cross = get_last_n_game_pass(home_name, match_date, n=n, fixtures=rel_fixture_rows,
                                                      filter_=home_name)
    away_wide_pass, away_cross = get_last_n_game_pass(away_name, match_date, n=n, fixtures=rel_fixture_rows,
                                                      filter_=away_name)
    data = {'home_corner_ma': home_ma, 'home_tt_coner_ma': home_tt_ma,
            'away_corner_ma': away_ma,
            'away_total_corner_ma': away_tt_ma, 'home_wide_pass': home_wide_pass, 'home_cross': home_cross,
            'away_wide_pass': away_wide_pass, 'away_cross': away_cross}
    df = df.append(data, ignore_index=True)
    return df

def get_corner_inputs(team_name=None, fixtures=None, filter_=None, n=5):
    rel_fixture_rows = fixtures
    if fixtures is None:
        rel_fixture_rows = pd.read_csv('../statistics/fixture_table.csv')
    if filter_ is not None:
        rel_fixture_rows = rel_fixture_rows[rel_fixture_rows.apply(lambda x: filter_ in x['path'], axis=1)]
    if team_name is not None:
        team_fixture_rows = rel_fixture_rows[
            (rel_fixture_rows['home'].isin(team_name)) | (rel_fixture_rows['away'].isin(team_name))]
    else:
        team_fixture_rows = rel_fixture_rows
    df = pd.DataFrame(columns=sets)
    for index, row in team_fixture_rows.iterrows():
        match_date = date.fromisoformat(row['date'])
        home_name = row['home']
        away_name = row['away']
        match_path = row['path']
        event_flatten_result = pd.read_csv(match_path.replace('match.json', 'event.csv'))
        pass_res = event_flatten_result[event_flatten_result['type'] == 'Pass']['satisfiedEventsTypes']
        team_corner_count = pass_res[pass_res.apply(lambda x: '30' in x)].count()
        last_n_home_corner = get_last_n_game_corner(home_name, match_date, n=n, fixtures=team_fixture_rows,
                                                    filter_=home_name)
        last_n_away_corner = get_last_n_game_corner(away_name, match_date, n=n, fixtures=rel_fixture_rows,
                                                    filter_=away_name)
        if last_n_home_corner.shape[0] < n or last_n_away_corner.shape[0] < n:
            continue
        home_ma = last_n_home_corner['teamCorner'].mean()
        home_tt_ma = last_n_home_corner['sum_corner'].mean()
        away_ma = last_n_away_corner['teamCorner'].mean()
        away_tt_ma = last_n_away_corner['sum_corner'].mean()
        home_wide_pass, home_cross = get_last_n_game_pass(home_name, match_date, n=n, fixtures=team_fixture_rows,
                                                          filter_=home_name)
        away_wide_pass, away_cross = get_last_n_game_pass(away_name, match_date, n=n, fixtures=rel_fixture_rows,
                                                          filter_=away_name)
        data = {'total_corner': team_corner_count, 'home_corner_ma': home_ma, 'home_tt_coner_ma': home_tt_ma,
                'away_corner_ma': away_ma,
                'away_total_corner_ma': away_tt_ma, 'home_wide_pass': home_wide_pass, 'home_cross': home_cross,
                'away_wide_pass': away_wide_pass, 'away_cross': away_cross}
        df = df.append(data, ignore_index=True)
        print('Input Done!' + row['path'])
    df.to_csv('corner_input.csv')


def is_wide_pass(is_home, is_first_half, x, y, end_x, end_y):
    if (not is_home and is_first_half) or (is_home and not is_first_half):
        if end_x > 66.6 and (end_y < 33.3 or end_y > 66.6):
            if not (x > 66.6 and (y < 33.3 or y > 66.6)):
                return True
            else:
                return False
        else:
            return False
    else:
        if end_x < 33.3 and (end_y < 33.3 or end_y > 66.6):
            if not (end_x < 33.3 and (end_y < 33.3 or end_y > 66.6)):
                return True
            else:
                return False
        else:
            return False


def get_last_n_game_pass(team_name, this_date, n=5, fixtures=None, filter_=None):
    n = int(n)
    if fixtures is None:
        fixtures = pd.read_csv('../statistics/fixture_table.csv')
    else:
        fixtures = deepcopy(fixtures)
    team_rel_rows = fixtures[(fixtures['home'] == team_name) | (fixtures['away'] == team_name)]
    team_rel_rows = team_rel_rows[team_rel_rows.apply(lambda x: filter_ in x['path'], axis=1)]
    teme_last_rows = team_rel_rows[team_rel_rows['date'] < this_date.isoformat()].sort_values(by='date',
                                                                                              ascending=False).head(n)
    passes, crosses = 0.0, 0.0
    for index, row in teme_last_rows.iterrows():
        match_path = row['path']
        event_flatten_result = pd.read_csv(match_path.replace('match.json', 'event.csv'))
        team_pass_event = event_flatten_result[(event_flatten_result['teamName'] == team_name) & (
            event_flatten_result['satisfiedEventsTypes'].map(lambda x: '116' in x))]
        cross_pass_event = event_flatten_result[(event_flatten_result['teamName'] == team_name) & (
            event_flatten_result['satisfiedEventsTypes'].map(lambda x: '124' in x or '125' in x))]
        is_home = True if row['home'] == team_name else False
        count_wide_pass = 0
        for pass_index, pass_row in team_pass_event.iterrows():
            is_first_half = True if pass_row['minute'] <= 45 else False
            try:
                if_wide_pass = is_wide_pass(is_home, is_first_half, pass_row['x'], pass_row['y'], pass_row['endX'],
                                            pass_row['endY'])
            except:
                if_wide_pass = False
            count_wide_pass = count_wide_pass + 1 if if_wide_pass else count_wide_pass
        passes += count_wide_pass
        crosses += cross_pass_event.shape[0]

    return passes / n, crosses / n


def get_last_n_game_corner(team_name, this_date, n=5, fixtures=None, filter_=None):
    n = int(n)
    if fixtures is None:
        fixtures = pd.read_csv('../statistics/fixture_table.csv')
    else:
        fixtures = deepcopy(fixtures)
    team_rel_rows = fixtures[(fixtures['home'] == team_name) | (fixtures['away'] == team_name)]
    team_rel_rows = team_rel_rows[team_rel_rows.apply(lambda x: filter_ in x['path'], axis=1)]
    teme_last_rows = team_rel_rows[team_rel_rows['date'] < this_date.isoformat()].sort_values(by='date',
                                                                                              ascending=False).head(n)
    df = corner_analysis(team_name, teme_last_rows)
    return df


def corner_analysis(team_name, fixtures, n=5):
    df = pd.DataFrame(
        columns=['date', 'teamName', 'oppositeName', 'teamCorner', 'oppositeCorner'])
    for index, row in fixtures.iterrows():
        match_path = row['path']
        event_flatten_result = pd.read_csv(match_path.replace('match.json', 'event.csv'))
        team_event = event_flatten_result[event_flatten_result['teamName'] == team_name]['satisfiedEventsTypes']
        team_corner_count = team_event[team_event.apply(lambda x: '30' in x)].count()
        opposite_event = event_flatten_result[event_flatten_result['teamName'] != team_name]['satisfiedEventsTypes']
        opposite_corner_count = opposite_event[opposite_event.apply(lambda x: '30' in x)].count()
        df = df.append({'date': row['date'], 'teamName': team_name,
                        'oppositeName': row['home'] if team_name == row['away'] else row['away'],
                        'teamCorner': team_corner_count, 'oppositeCorner': opposite_corner_count}, ignore_index=True)
    df_ma = df.set_index('date').rolling(n).mean()
    result = pd.merge(df, df_ma, left_on=['date'], right_index=True)
    result['sum_corner'] = result['teamCorner_x'] + result['oppositeCorner_x']
    result['ma_sum_corner'] = result['teamCorner_y'] + result['oppositeCorner_y']
    result = result.rename(
        columns={'teamCorner_x': 'teamCorner', 'oppositeCorner_x': 'oppositeCorner', 'teamCorner_y': 'teamCorner_ma',
                 'oppositeCorner_y': 'oppositeCorner_ma'})
    return result


if __name__ == '__main__':
    # team1, team2 = 'Liverpool', 'Leeds'
    # ts1, ts2 = get_two_team_paths(team1, team2)
    # result_ts1 = corner_analysis(team1, ts1)
    # result_ts2 = corner_analysis(team2, ts2)
    # result_ts1.to_csv(team1 + '.csv')
    # result_ts2.to_csv(team2 + '.csv')

    # fixture_date = date(2021, 9, 10)
    # team = 'West Ham'
    # result = get_last_n_game_pass(team, fixture_date, filter_='Premier')
    # result.to_csv(team + '.csv')

    get_corner_inputs(filter_='Premier')
