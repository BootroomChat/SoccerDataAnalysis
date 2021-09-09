import json
import pandas as pd


def single_match_flatten(match_info):
    """
    match json flatten
    :param match_info: json
    :return: dataframe
    """
    flatten_column = ['id', 'eventId', 'minute', 'second', 'teamName', 'playerName', 'x', 'y', 'type', 'outcomeType',
                      'qualifiers',
                      'satisfiedEventsTypes', 'isTouch', 'endX', 'endY']
    match_df = pd.DataFrame(columns=flatten_column)
    team_name_dic = {match_info['home']['teamId']: match_info['home']['name'],
                     match_info['away']['teamId']: match_info['away']['name']}
    player_name_dic = match_info['playerIdNameDictionary']
    for event in match_info['events']:
        tmp = \
            {
                'id': event['id'],
                'eventId': event['eventId'],
                'minute': event['minute'],
                'second': event.get('second', 0),
                'teamName': team_name_dic[event['teamId']],
                'playerName': player_name_dic.get(event.get('playerId', 'NA'), None),
                'type': event['type']['displayName'],
                'outcomeType': event['outcomeType']['displayName'],
                'qualifiers': {x['type']['displayName']: x['type']['value'] for x in event['qualifiers']},
                'satisfiedEventsTypes': event['satisfiedEventsTypes'],
                'x': event['x'],
                'y': event['y'],
                'isTouch': event['isTouch'],
                'endX': event.get('endX', None),
                'endY': event.get('endY', None),
            }
        match_df = match_df.append(tmp, ignore_index=True)
    return match_df


if __name__ == '__main__':
    file = '..\\\\matches\\England-FA-Cup\\2019-2020\\2020-01-05\\Liverpool-Everton\\match.json'
    with open(file, encoding="utf-8") as json_data:
        d = json.load(json_data)
        df = single_match_flatten(d)
        df.to_csv(file.replace('match.json', 'event.csv'))
