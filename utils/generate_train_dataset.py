import json
import os

from progressbar import ProgressBar

from utils.json_type import write_json, to_snake, load_json
from utils.load_data import match_pathes

event_mapping = load_json("../config/event_mapping.json")
all_types = set()
pass_types = {'keyPassThrowin', 'midThird', 'passInaccurate', 'pos', 'passCornerAccurate', 'passBack', 'passRight',
              'finalThird', 'passFreekickAccurate', 'passAccurate', 'keyPassCross', 'passThroughBallAccurate',
              'passLeft', 'passThroughBallInaccurate', 'assistThroughball', 'passForwardZoneAccurate',
              'bigChanceCreated', 'throwIn', 'defensiveThird', 'passLongBallAccurate', 'passRightFoot', 'assistOther',
              'passCornerInaccurate', 'passHead', 'assistCorner', 'passFreekickInaccurate', 'assistFreekick',
              'passCrossInaccurate', 'keyPassThroughball', 'passLeftFoot', 'successfulFinalThirdPasses', 'passKey',
              'passFreekick', 'passCrossAccurate', 'passLongBallInaccurate', 'keyPassFreekick', 'keyPassLong',
              'passCorner', 'keyPassShort', 'assistThrowin', 'shortPassAccurate', 'keyPassOther', 'keyPassCorner',
              'passForward', 'shortPassInaccurate', 'passChipped', 'assistCross', 'intentionalAssist',
              'passBackZoneInaccurate', 'assist', 'touches'}


def parse_shots_from_match(match_info):
    match_id = match_info['startDate'][:10] + "/" + match_info['home']['name'] + "-" + match_info['away']['name']
    player_ids = match_info['playerIdNameDictionary']

    shots = []
    for event in match_info['events']:
        if 9 in event['satisfiedEventsTypes']:
            minute = event['minute']

            player_id = str(event['playerId'])
            player_name = player_ids.get(player_id, '')
            x_coord = event['x']
            y_coord = event['y']

            goalMouthY = ''
            goalMouthZ = ''
            try:
                goalMouthY = event['goalMouthY']
                goalMouthZ = event['goalMouthZ']
            except:
                pass

            is_big_chance = 0
            is_from_corner = 0
            is_freekick = 0
            is_penalty = 0
            if 'qualifiers' in event:
                for q in event['qualifiers']:
                    if q['type']['displayName'] == 'BigChance':
                        is_big_chance = 1
                    if q['type']['displayName'] == 'FromCorner':
                        is_from_corner = 1
                    if q['type']['displayName'] == 'DirectFreekick':
                        is_freekick = 1
                    if q['type']['displayName'] == 'Penalty':
                        is_penalty = 1

            is_open_play = int(3 in event['satisfiedEventsTypes'])
            is_counter = int(4 in event['satisfiedEventsTypes'])
            is_set_piece = int(5 in event['satisfiedEventsTypes'])
            is_goal = int(('isGoal' in event) and (event['isGoal'] == True))
            is_shot_on_target = int(8 in event['satisfiedEventsTypes'])
            is_blocked = int(10 in event['satisfiedEventsTypes'])

            shot_type = 0
            if 11 in event['satisfiedEventsTypes']:
                shot_type = 1
            if 12 in event['satisfiedEventsTypes']:
                shot_type = 1
            if 13 in event['satisfiedEventsTypes']:
                shot_type = 2
            if 14 in event['satisfiedEventsTypes']:
                shot_type = 2

            shots.append(
                [match_id, event['teamId'], player_id, player_name, minute, x_coord, y_coord, goalMouthY, goalMouthZ,
                 shot_type, is_big_chance, is_from_corner, is_open_play, is_counter, is_set_piece, is_freekick,
                 is_penalty, is_shot_on_target, is_blocked, is_goal])

    return shots


def get_match_xa_pass(match_path, match_info=None):
    if match_path and not match_info:
        match_info = load_json(match_path)
    _passes = []
    for i, event in enumerate(match_info['events']):
        qualifiers = {qualifier['type']['displayName']:
                          {'id': qualifier['type']['value'], 'value': qualifier.get('value', 1)}
                      for qualifier in event['qualifiers']}
        detailed_types = {event_mapping[str(type_id)]: type_id
                          for type_id in event['satisfiedEventsTypes']}
        detailed_types_set = set(detailed_types)
        if event['type']['displayName'] == 'Pass':
            pass_item = {to_snake(key): event[key]
                         for key in ['x', 'y', 'endX', 'endY', 'teamId', 'playerId']}
            if 'Zone' not in qualifiers:
                print(qualifiers)
                continue
            pass_item.update({to_snake(key): qualifiers[key]['value']
                              for key in ['Angle', 'Length', 'Zone']})
            pass_item['is_success'] = 1 if event['outcomeType']['displayName'] == 'Successful' else 0
            all_types.union(detailed_types_set)
            for key, satisfied_types in {
                'is_freekick': {'passFreekick'},
                'is_assist': {'assist'}, 'is_big_chance': {'bigChanceCreated'},
                'is_final_third': {'finalThird'}, 'is_key_pass': {'passKey'},
                'is_to_final_third': {'successfulFinalThirdPasses'},
                'is_chip': {'passChipped'}, 'is_corner': {'passCorner'},
                'is_forward': {'passForward'}, 'is_cross': {'passCrossAccurate', 'passCrossInaccurate'},
                'is_head': {'passHead'}, 'is_long': {'passLongBallAccurate', 'passLongBallInaccurate'},
                'is_through': {'passThroughBallAccurate', 'passThroughBallInaccurate'},
                'is_short': {'shortPassAccurate', 'shortPassInaccurate'},
            }.items():
                pass_item[key] = 1 if satisfied_types & detailed_types_set else 0
            _passes.append(pass_item)
    return _passes


if __name__ == '__main__':
    progress = ProgressBar()
    passes = []
    for match_path in progress(match_pathes()):
        if '2019-2020' in match_path:
            data_path = os.path.join(match_path, 'match.json')
            passes += get_match_xa_pass(data_path)
    write_json('nn_xg/passes.json', passes)
    passes = get_match_xa_pass('matches/England-Premier-League/2019-2020/2020-07-26/Leicester-Man Utd/match.json')
    passes += get_match_xa_pass('matches/England-Premier-League/2019-2020/2020-07-26/Man City-Norwich/match.json')
    write_json('nn_xg/test_passes.json', passes)
