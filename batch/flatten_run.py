import os

from analysis.corner import get_two_team_paths
from utils.event_flatten import single_match_flatten
from utils.json_type import load_json
from utils.load_data import match_pathes

if __name__ == '__main__':
    # ts1, ts2 = get_two_team_paths('Liverpool', 'Leeds')
    # for index,row in ts1.iterrows():
    #     match_path = row['path']
    #     data = load_json(match_path)
    #     df = single_match_flatten(data)
    #     df.to_csv(match_path.replace('match.json', 'event.csv'))
    # for index,row in ts2.iterrows():
    #     match_path = row['path']
    #     data = load_json(match_path)
    #     df = single_match_flatten(data)
    #     df.to_csv(match_path.replace('match.json', 'event.csv'))
    # Event data
    match_path = match_pathes(name_filter=['England-Premier-League', 'Europa-League'])
    for each_match_path in match_path:
        json_path = os.path.join(each_match_path, 'match.json')
        csv_path = json_path.replace('match.json', 'event.csv')
        if os.path.exists(json_path) and not os.path.exists(csv_path):
            data = load_json(json_path)
            df = single_match_flatten(data)
            df.to_csv(json_path.replace('match.json', 'event.csv'))
            print(csv_path + ' Done!')
