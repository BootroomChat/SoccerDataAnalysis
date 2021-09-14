from datetime import date

from utils.fixtures_flatten import fixture_flatten
import pandas as pd


def get_two_team_paths(team_a, team_b):
    return fixture_flatten(team_a), fixture_flatten(team_b)


def get_last_n_game_corner(team_name, this_date, n=5, fixtures=None, filter_=None):
    n = int(n)
    if fixtures is None:
        fixtures = pd.read_csv('../statistics/fixture_table.csv')
    team_rel_rows = fixtures[(fixtures['home'] == team_name) | (fixtures['away'] == team_name)]
    team_rel_rows = team_rel_rows[team_rel_rows.apply(lambda x: filter_ in x['path'], axis=1)]
    teme_last_rows = team_rel_rows[team_rel_rows['date'] <= this_date.isoformat()].sort_values(by='date',
                                                                                               ascending=False).head(n)
    df = corner_analysis(team_name, teme_last_rows)
    return df


def corner_analysis(team_name, fixtures):
    df = pd.DataFrame(columns=['date', 'teamName', 'oppositeName', 'teamCorner', 'oppositeCorner'])
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
    df_ma = df.set_index('date').rolling(5).mean()
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

    fixture_date = date(2021, 9, 10)
    team = 'West Ham'
    result=get_last_n_game_corner(team, fixture_date,filter_='Premier')
    result.to_csv(team + '.csv')
