# -*- coding: UTF-8 -*-
import json
import os

import joblib
import pandas as pd

from utils import individual_stats, team_stats, mapping_dic
from utils.json_type import load_json
from utils.generate_train_dataset import parse_shots_from_match, get_match_xa_pass

lr = joblib.load('../statistics/shots/LogisticRegression.pkl')

added_keys = {"recoveryX", "totalPass", "keyPass", "passDistance", "passLeadingKp", "involvingOpenChance",
              "forwardPassMeter", "forwardPassPercentage", "dispossessedInD3rd", "passToA3rd", "successfulPassToA3rd",
              "dribbleInMiddle", "goalAssistOwn", "successfulTotalPass", "successfulPassDistance",
              "successfulForwardPassMeter", "successfulForwardPassPercentage", "expectedGoal",
              "expectedGoalChain", "expectedGoalBuildUp", "teamExpectedGoal", "teamExpectedGoalConceded",
              "teamGoalConceded", "teamGoal", 'defensiveDuelSuccess', 'offensiveDuelSuccess',
              'expectedSuccessPass', 'expectedAssist',
              "winCount", "loseCount", "drawCount"}
with open('../config/event_types.json', encoding="utf-8") as json_data:
    d = json.load(json_data)
full_event_type = d
court_size = {"length": 105, "width": 68}


def parse_result(scores, team_keys):
    game_result = {}
    if scores[0] > scores[1]:
        game_result[team_keys[0]] = {'winCount': 1}
        game_result[team_keys[1]] = {'loseCount': 1}
    elif scores[0] < scores[1]:
        game_result[team_keys[1]] = {'winCount': 1}
        game_result[team_keys[0]] = {'loseCount': 1}
    else:
        game_result[team_keys[0]] = {'drawCount': 1}
        game_result[team_keys[1]] = {'drawCount': 1}
    return game_result


def parse_player_event_data(file_name):
    _,__, league, season, date, match, _ = file_name.split('/')
    match_info = load_json(file_name)
    event_type_mapping = {}
    for key in full_event_type:
        event_type_mapping[full_event_type[key]] = key
    minutes = match_info['expandedMaxMinute']
    match_id = match_info['startDate'][:10] + "/" + match_info['home']['name'] + "-" + match_info['away']['name']
    player_stats = {}
    team_keys = ['home', 'away']
    opponent_team_mapping = {}
    game_result = parse_result(match_info['score'].split(' : '), team_keys)
    formation_positions = load_json('../statistics/formation_positions.json')
    on_court_players = {}
    for i, key in enumerate(team_keys):
        game_result[match_info[key]['teamId']] = game_result[key]
        for player in match_info[key]['players']:
            opponent = team_keys[1 - i]
            opponent_team_mapping[match_info[key]['teamId']] = match_info[opponent]['teamId']
            on_court = player.get('isFirstEleven', False)
            if on_court:
                on_court_players[match_info[key]['teamId']] = on_court_players.get(match_info[key]['teamId'], []) + [
                    str(player['playerId'])]

            player_stats[str(player['playerId'])] = {'name': player['name'], 'age': player['age'],
                                                     'height': player['height'], 'weight': player['weight'],
                                                     'id': str(player['playerId']),
                                                     'date': date, 'field': key, 'match_id': match_id,
                                                     'stadium': match_info.get('venueName', ''),
                                                     'minutes': minutes if on_court else 0,
                                                     'team_id': match_info[key]['teamId'],
                                                     'opponent_team_id': match_info[opponent]['teamId'],
                                                     'team_name': match_info[key]['name'],
                                                     'opponent_team_name': match_info[opponent]['name']}
            for event in full_event_type:
                player_stats[str(player['playerId'])][event] = 0
            for item in added_keys:
                player_stats[str(player['playerId'])][item] = 0
        for formation in match_info[key]['formations']:
            formation_position = formation_positions[str(formation['formationId'])]
            formation_minutes = formation['endMinuteExpanded'] - formation['startMinuteExpanded']
            for i, player_id in enumerate(formation['playerIds'][:11]):
                if str(player_id) not in player_stats:
                    continue
                position_key = formation_position['positions'][i]['position'] + "_minutes"
                player_stats[str(player_id)][position_key] = player_stats[str(player_id)] \
                                                                 .get(position_key, 0) + formation_minutes
    involve_attack = []
    continued_team_events = []
    last_team_id = ""
    xg_data = get_match_xG(file_name)
    _, xpass_data = get_match_xA_xsp(file_name)
    xg_mapping = {}
    for item in xpass_data.T.to_dict().values():
        if str(item['player_id']) in player_stats:
            player_stats[str(item['player_id'])]['expectedAssist'] += item['xA']
            player_stats[str(item['player_id'])]['expectedSuccessPass'] += item['xsp']
    for item in xg_data.T.to_dict().values():
        if str(item['player_id']) in player_stats:
            player_stats[str(item['player_id'])]['expectedGoal'] += item['xG']
        xg_mapping["{0}_{1}_{2}_{3}_{4}_{5}".format(item['player_id'], item['minute'],
                                                    item['x'], item['y'], item['goalMouthY'], item['goalMouthZ'])] \
            = item
    for i, event in enumerate(match_info['events']):
        # Attacking involvements records here: starts with ball recovery
        # Can chase back one attack via temp variable involve_attack
        if "playerId" in event:
            player_id = str(event["playerId"])
            current_team_id = event["teamId"]
            for _key, _value in game_result[current_team_id].items():
                player_stats[player_id][_key] = _value
            if player_id not in player_stats:
                continue
            if event['type']['displayName'] == 'SubstitutionOff':
                player_stats[player_id]['minutes'] = event['expandedMinute']
                if player_id in on_court_players[current_team_id]:
                    on_court_players[current_team_id].remove(player_id)
            if event['type']['displayName'] == 'SubstitutionOn':
                player_stats[player_id]['minutes'] = minutes - event['expandedMinute']
                on_court_players[current_team_id].append(player_id)

            # shotTotal
            if 9 in event["satisfiedEventsTypes"]:
                key = "{0}_{1}_{2}_{3}_{4}_{5}".format(event['playerId'], event['minute'],
                                                       event.get('x', ''), event.get('y', ''),
                                                       event.get('goalMouthY', ''),
                                                       event.get('goalMouthZ', ''), )
                if event.get('isGoal', False):
                    for _player_id in on_court_players[current_team_id]:
                        player_stats[_player_id]['teamGoal'] += 1
                    for _player_id in on_court_players[opponent_team_mapping[current_team_id]]:
                        player_stats[_player_id]['teamGoalConceded'] += 1
                if key in xg_mapping:
                    xg_item = xg_mapping[key]
                    for _player_id in on_court_players[current_team_id]:
                        player_stats[_player_id]['teamExpectedGoal'] += xg_item['xG']
                    for _player_id in on_court_players[opponent_team_mapping[current_team_id]]:
                        player_stats[_player_id]['teamExpectedGoalConceded'] += xg_item['xG']
            if event['outcomeType']['value'] == 1 and current_team_id != last_team_id:
                # print(involve_attack, event['minute'], event['id'])
                prev_events = []
                for prev_event in continued_team_events:
                    key = "{0}_{1}_{2}_{3}_{4}_{5}".format(prev_event['playerId'], prev_event['minute'],
                                                           prev_event.get('x', ''), prev_event.get('y', ''),
                                                           prev_event.get('goalMouthY', ''),
                                                           prev_event.get('goalMouthZ', ''), )
                    prev_events.append(prev_event)
                    if key in xg_mapping:
                        xgItem = xg_mapping[key]
                        for _event in prev_events:
                            _player_id = str(_event['playerId'])
                            if "playerId" in _event and _player_id in player_stats:
                                player_stats[_player_id]['expectedGoalChain'] += xgItem['xG']
                                if not _event.get('isGoal', False) and 91 not in _event['satisfiedEventsTypes'] \
                                        and _event['id'] != prev_event['id']:
                                    player_stats[_player_id]['expectedGoalBuildUp'] += xgItem['xG']
                involve_attack.clear()
                continued_team_events.clear()
                last_team_id = event["teamId"]
            if current_team_id == last_team_id and \
                    "displayName" in event["type"] and "playerId" in event \
                    and 'Substitution' not in event['type']['displayName']:
                continued_team_events.append(event)
                involve_attack.append([player_id, event["type"]["displayName"]])
            for sat_event in event["satisfiedEventsTypes"]:
                event_name = event_type_mapping[sat_event]
                player_stats[player_id][event_name] += 1
            # recoveryX:
            if 92 in event["satisfiedEventsTypes"]:
                recovery_num = player_stats[player_id]["ballRecovery"]
                player_stats[player_id]["recoveryX"] = ((recovery_num - 1) * player_stats[player_id]["recoveryX"] +
                                                        event["x"]) / recovery_num
            # totalPass && passDistance && KeyPass&&forwardPassMeter && forwardPassPercentage
            isKeyPass = False
            xChangeOnPass = 0
            yChangeOnPass = 0
            is_successful = False
            isPassToFinalThird = False
            if event['type']['displayName'] == 'Pass' \
                    and 'x' in event and 'y' in event \
                    and 'endX' in event and 'endY' in event:
                distance = 0
                for item in event['qualifiers']:
                    if item['type']['displayName'] == 'KeyPass':
                        isKeyPass = True
                        player_stats[player_id]["keyPass"] += 1
                    if item['type']['displayName'] == 'Length':
                        distance = float(item['value'])
                    if item['type']['displayName'] == 'PassEndX':
                        xChangeOnPass = float(item.get('value', 0)) - event['x']
                        if event['endX'] > 66.7 > event['x']:
                            isPassToFinalThird = True
                            player_stats[player_id]["passToA3rd"] += 1
                    if item['type']['displayName'] == 'PassEndY':
                        yChangeOnPass = float(item.get('value', 0)) - event['y']
                if event['outcomeType']['displayName'] == 'Successful':
                    is_successful = True
                if isPassToFinalThird and is_successful:
                    player_stats[player_id]["successfulPassToA3rd"] += 1
                if is_successful:
                    total_pass = player_stats[player_id]['successfulTotalPass']
                    player_stats[player_id]["successfulForwardPassMeter"] = (player_stats[player_id][
                                                                                 "successfulForwardPassMeter"] * total_pass + xChangeOnPass) / (
                                                                                    total_pass + 1) * court_size[
                                                                                "length"] / 100
                    player_stats[player_id]["successfulForwardPassPercentage"] += xChangeOnPass / (
                            abs(xChangeOnPass) + abs(yChangeOnPass)) if abs(xChangeOnPass) + abs(
                        yChangeOnPass) > 0 else 0
                    player_stats[player_id]["successfulPassDistance"] = (total_pass * player_stats[player_id][
                        "successfulPassDistance"] + distance) / (total_pass + 1)
                    player_stats[player_id]['successfulTotalPass'] = total_pass + 1
                total_pass = player_stats[player_id]['totalPass']
                player_stats[player_id]["forwardPassMeter"] = (player_stats[player_id][
                                                                   "forwardPassMeter"] * total_pass + xChangeOnPass) / (
                                                                      total_pass + 1) * court_size["length"] / 100
                player_stats[player_id]["forwardPassPercentage"] += xChangeOnPass / (
                        abs(xChangeOnPass) + abs(yChangeOnPass)) if abs(xChangeOnPass) + abs(yChangeOnPass) > 0 else 0
                player_stats[player_id]["passDistance"] = (total_pass * player_stats[player_id][
                    "passDistance"] + distance) / (total_pass + 1)
                player_stats[player_id]['totalPass'] = total_pass + 1
            if isKeyPass and len(involve_attack) >= 2:
                j = len(involve_attack) - 1
                if involve_attack[j][1] == 'Pass':
                    player_stats[involve_attack[j][0]]['passLeadingKp'] += 1
            # dispossessedInD3rd
            if event['type']['displayName'] == 'Dispossessed':
                if event['x'] < 33.3:
                    player_stats[player_id]['dispossessedInD3rd'] += 1
            # dribbleInMiddle:
            if 53 in event["satisfiedEventsTypes"] and 33.3 < event['y'] < 66.7:
                player_stats[player_id]["dribbleInMiddle"] += 1
            # duel
            if 198 in event["satisfiedEventsTypes"]:
                player_stats[player_id]["offensiveDuelSuccess"] += 1 if 196 in event["satisfiedEventsTypes"] else 0
            if 199 in event["satisfiedEventsTypes"]:
                player_stats[player_id]["defensiveDuelSuccess"] += 1 if 196 in event["satisfiedEventsTypes"] else 0
            # goalOwn
            if 22 in event["satisfiedEventsTypes"]:
                delta = 1
                prev_event = match_info['events'][i - delta]
                while prev_event['teamId'] == event['teamId'] \
                        or 'playerId' not in prev_event:
                    delta += 1
                    prev_event = match_info['events'][i - delta]
                prev_player_id = str(prev_event['playerId'])
                player_stats[prev_player_id]['goalAssistOwn'] += 1
            # involvingOpenChance
            if 3 in event["satisfiedEventsTypes"]:
                length = len(involve_attack)
                for i in range(1, length):
                    player_stats[involve_attack[length - i][0]]['involvingOpenChance'] += 1
    df = pd.DataFrame(list(player_stats.values())).fillna(0)
    df.to_csv(file_name.replace('match.json', 'event_count.csv'), index=None)
    return player_stats


def parse_accumulated_passes(match_info):
    home_id = match_info['home']['teamId']
    away_id = match_info['away']['teamId']
    home_name = match_info['home']['name']
    away_name = match_info['away']['name']
    accumulated_forward_pass = []
    home_passes = {}
    away_passes = {}
    attacking_third_passes = {'home': 0.0, 'away': 0.0}
    successful_athird_passes = {'home': 0.0, 'away': 0.0}
    total_passes = {'home': sum(match_info['home']['stats']['passesTotal'].values()),
                    'away': sum(match_info['away']['stats']['passesTotal'].values())}
    for event in match_info['events']:
        if event['type']['displayName'] == 'Pass' and event['teamId'] == home_id:
            if not home_passes.__contains__(event['minute']):
                home_passes[event['minute']] = event['endX'] - event['x']
            else:
                home_passes[event['minute']] += event['endX'] - event['x']
        elif event['type']['displayName'] == 'Pass' and event['teamId'] == away_id:
            if not away_passes.__contains__(event['minute']):
                away_passes[event['minute']] = event['endX'] - event['x']
            else:
                away_passes[event['minute']] += event['endX'] - event['x']
        if event['type']['displayName'] == 'Pass' and event['endX'] > 67 and event['teamId'] == home_id:
            attacking_third_passes['home'] += 1
            if event['outcomeType']['displayName'] == "Successful":
                successful_athird_passes['home'] += 1
        elif event['type']['displayName'] == 'Pass' and event['endX'] > 67 and event['teamId'] == away_id:
            attacking_third_passes['away'] += 1
            if event['outcomeType']['displayName'] == "Successful":
                successful_athird_passes['away'] += 1
    sorted_keys = sorted(home_passes.keys())
    i = 0
    accumulated_home_passes_dic = {}
    for i in range(len(sorted_keys)):
        if i == 0:
            accumulated_home_passes_dic[sorted_keys[i]] = home_passes[sorted_keys[i]]
        else:
            accumulated_home_passes_dic[sorted_keys[i]] = home_passes[sorted_keys[i]] + accumulated_home_passes_dic[
                sorted_keys[i - 1]]
    sorted_keys_away = sorted(away_passes.keys())
    accumulated_away_passes_dic = {}
    for i in range(len(sorted_keys_away)):
        if i == 0:
            accumulated_away_passes_dic[sorted_keys_away[i]] = away_passes[sorted_keys_away[i]]
        else:
            accumulated_away_passes_dic[sorted_keys_away[i]] = away_passes[sorted_keys_away[i]] + \
                                                               accumulated_away_passes_dic[sorted_keys_away[i - 1]]
    accumulated_forward_pass.append({
        home_id: {
            'home_name': home_name,
            'accumulatedPasses_series': accumulated_home_passes_dic,
            'final_forwardPass': accumulated_home_passes_dic[sorted_keys[-1]],
            'successful_finalThirdPass': successful_athird_passes['home'],
            'final_third_pass': attacking_third_passes['home'],
            'total_pass': total_passes['home']},
        away_id: {
            'away_name': away_name,
            'accumulatedPasses_series': accumulated_away_passes_dic,
            'final_forwardPass': accumulated_away_passes_dic[sorted_keys_away[-1]],
            'successful_finalThirdPass': successful_athird_passes['away'],
            'final_third_pass': attacking_third_passes['away'],
            'total_pass': total_passes['away']}
    })
    return accumulated_forward_pass


def parse_pass_from_match(match_info):
    output = []
    for event in match_info['events']:
        if event['type']['displayName'] == 'Pass':
            output.append(event)
    return output


def parse_events(file_name):
    data = load_json(file_name)
    result = {}
    for key in ['home', 'away']:
        for player in data[key]['players']:
            result[str(player['playerId'])] = {'name': player['name'], 'id': str(player['playerId']),
                                               'team_id': data[key]['teamId']}
    events = load_json("../config/event_mapping.json")
    for event in data['events']:
        for id in event['satisfiedEventsTypes']:
            if 'playerId' in event:
                key = events[str(id)] + "Count"
                player_key = str(event['playerId'])
                if player_key in result:
                    result[player_key][key] = result[player_key].get(key, 0) + 1
    df = pd.DataFrame(list(result.values())).fillna(0)
    df.to_csv(file_name.replace('match.json', 'event_count.csv'), index=None)
    return df


def represent(shots_list):
    return pd.DataFrame(shots_list, columns=['match_id', 'team_id', 'player_id', 'player_name', 'minute', 'x', 'y',
                                             'goalMouthY', 'goalMouthZ', 'shot_type', 'is_big_chance', 'is_from_corner',
                                             'is_open_play', 'is_counter',
                                             'is_set_piece', 'is_freekick', 'is_penalty', 'is_on_target', 'is_blocked',
                                             'is_goal'])


def get_shot_xG(shot):
    return lr.predict_proba(shot.reshape(1, -1))[:, 1][0]


def get_list_xG(shots):
    xG_list = []
    for shot in shots:
        xG_list.append(get_shot_xG(shot))
    return xG_list


def get_match_xA_xsp(match_path):
    from nn_xg import predict_assists, predict_success_passes
    passes = get_match_xa_pass(match_path)
    return predict_assists(passes), predict_success_passes(passes)


def get_match_xG(match_path):
    match_info = load_json(match_path)
    df = represent(parse_shots_from_match(match_info))
    from nn_xg import predict_shots
    df = predict_shots(df.T.to_dict())
    return df
    # LR 预测
    # score = match_info['score']
    # home_team_id = match_info['home']['teamId']
    # away_team_id = match_info['away']['teamId']
    # home_team_name = match_info['home']['name']
    # away_team_name = match_info['away']['name']
    # shot_data = df[['team_id', 'x', 'y', 'shot_type', 'is_big_chance', 'is_from_corner', 'is_open_play', 'is_counter',
    #                 'is_set_piece', 'is_freekick']].copy()
    # shot_data['distance'] = np.sqrt((100 - shot_data['x']) ** 2 + ((100 - shot_data['y']) / 100 * 63) ** 2)
    # shot_data['y'] = abs(shot_data['y'] - 50)
    # print(shot_data.T.to_dict())
    # shot_data = pd.get_dummies(data=shot_data, columns=['shot_type'])
    # if 'shot_type_2' not in shot_data.columns:
    #     shot_data['shot_type_2'] = 0
    # shot_data = shot_data.drop('team_id', axis=1).values
    # df['xG'] = get_list_xG(shot_data)

    # home_pens = df[(df['is_penalty'] == 1) & (df['team_id'] == home_team_id)]['is_penalty'].sum()
    # away_pens = df[(df['is_penalty'] == 1) & (df['team_id'] == away_team_id)]['is_penalty'].sum()
    # df_no_pen = df[df['is_penalty'] == 0]
    # home_xG = df_no_pen[df_no_pen['team_id'] == home_team_id]['xG'].sum()
    # away_xG = df_no_pen[df_no_pen['team_id'] == away_team_id]['xG'].sum()
    # xG_score = '(%0.2f ' % (home_xG)
    # if home_pens != 0:
    #     xG_score += '(+%d pen) ' % (home_pens)
    # xG_score += ': %0.2f' % (away_xG)
    # if away_pens != 0:
    #     xG_score += ' (+%d pen)' % (away_pens)
    # xG_score += ')'
    #
    # shots_info = df_no_pen[['x', 'y', 'is_goal', 'xG', 'team_id']]
    # shots_info['home_team'] = (shots_info['team_id'] == home_team_id).astype(int)
    # return df


def parse_individual_stats(match_path):
    _,__,league, season, date, match = match_path.split('/')
    match_info = load_json(os.path.join(match_path, 'match.json'))
    # General Info
    match_id = match_info['startDate'][:10] + "/" + match_info['home']['name'] + "-" + match_info['away']['name']
    player_stats = {}
    minutes = match_info['expandedMaxMinute']
    both_team_stats = {}
    team_keys = ['home', 'away']
    homeId = match_info['home']['teamId']
    awayId = match_info['away']['teamId']
    for i, key in enumerate(team_keys):
        for player in match_info[key]['players']:
            opponent = team_keys[1 - i]
            player_stats[player['playerId']] = {'name': player['name'], 'id': str(player['playerId']),
                                                'position': player['position'],
                                                'match_id': match_id,
                                                'team_id': match_info[key]['teamId'],
                                                'team_name': match_info[key]['name'],
                                                'minutes': minutes if int(player['playerId']) in
                                                                      match_info[key]['formations'][0][
                                                                          'playerIds'][:11] else 0,
                                                'opponent_team_id': match_info[opponent]['teamId'],
                                                'opponent_team_name': match_info[opponent]['name'],
                                                'season': season, 'date': date, 'age': player['age'],
                                                'height': player['height'], 'weight': player['weight'],
                                                'league': league}
            for item in individual_stats:
                player_stats[player['playerId']][item] = 0
        both_team_stats[match_info[key]['teamId']] = {}
        for item in team_stats:
            both_team_stats[match_info[key]['teamId']][item] = 0
        for stats in mapping_dic:
            both_team_stats[match_info[key]['teamId']][stats] = 0
        both_team_stats[match_info[key]['teamId']]["Name"] = match_info[key]['name']

    players_on_the_pitch = {}
    home_attack = False
    last_touch_Id = awayId
    transition_time = 0
    # Initialize
    if match_info['events'][0]['teamId'] == homeId:
        home_attack = True
        last_touch_Id = homeId
        for item in match_info['home']['players']:
            if 'isFirstEleven' in item and item['isFirstEleven'] == True:
                players_on_the_pitch[item['playerId']] = 'Attack'
        for item in match_info['away']['players']:
            if 'isFirstEleven' in item and item['isFirstEleven'] == True:
                players_on_the_pitch[item['playerId']] = 'Defense'
    else:
        for item in match_info['home']['players']:
            if 'isFirstEleven' in item and item['isFirstEleven'] == True:
                players_on_the_pitch[item['playerId']] = 'Defense'
        for item in match_info['away']['players']:
            if 'isFirstEleven' in item and item['isFirstEleven'] == True:
                players_on_the_pitch[item['playerId']] = 'Attack'
    for event in match_info['events']:
        if event['isTouch']:
            current_touch_id = event["teamId"]
            if event['type']['displayName'] in ('TakeOn', 'Tackle', 'Clearance', 'Save', 'BlockedPass'):
                continue
            else:
                if current_touch_id != last_touch_Id:
                    home_attack = not home_attack
                    last_touch_Id = current_touch_id
                    both_team_stats[awayId]["Rounds"] += 1
                    both_team_stats[homeId]["Rounds"] += 1
                    if home_attack:
                        current_time = event['minute'] + event['second'] / 60.0
                        both_team_stats[homeId]["DefendTimes"] += current_time - transition_time
                        both_team_stats[awayId]["AttackTimes"] += current_time - transition_time
                        for keys in players_on_the_pitch:
                            if not keys in player_stats:
                                continue
                            player_stats[keys]["Rounds"] += 1
                            if player_stats[keys]['team_id'] == homeId:
                                player_stats[keys]["DefendTimes"] += current_time - transition_time
                            else:
                                player_stats[keys]["AttackTimes"] += current_time - transition_time
                        transition_time = current_time
                    else:
                        current_time = event['minute'] + event['second'] / 60.0
                        both_team_stats[awayId]["DefendTimes"] += current_time - transition_time
                        both_team_stats[homeId]["AttackTimes"] += current_time - transition_time
                        for keys in players_on_the_pitch:
                            if not keys in player_stats:
                                continue
                            player_stats[keys]["Rounds"] += 1
                            if player_stats[keys]['team_id'] == awayId:
                                player_stats[keys]["DefendTimes"] += current_time - transition_time
                            else:
                                player_stats[keys]["AttackTimes"] += current_time - transition_time
                        transition_time = current_time
        if 'playerId' in event and event['playerId'] in player_stats:
            if event['type']['displayName'] == 'SubstitutionOff':
                player_stats[event['playerId']]['minutes'] = event['expandedMinute']
            if event['type']['displayName'] == 'SubstitutionOn':
                player_stats[event['playerId']]['minutes'] = minutes - event['expandedMinute']
        if event['type']['displayName'] == 'SubstitutionOn' and 'relatedPlayerId' in event:
            if event['relatedPlayerId'] in players_on_the_pitch:
                players_on_the_pitch[event['playerId']] = players_on_the_pitch[event['relatedPlayerId']]
                players_on_the_pitch.__delitem__(event['relatedPlayerId'])
            else:
                players_on_the_pitch[event['playerId']] = "SubOn"
        if event['type']['displayName'] == 'SubstitutionOn' and 'relatedPlayerId' not in event:
            players_on_the_pitch[event['playerId']] = "SubOn"
    if os.path.exists(os.path.join(match_path, 'event_count.csv')):
        df = pd.read_csv(os.path.join(match_path, 'event_count.csv'), header=0, sep=',')
        df = pd.DataFrame(df)
        df['goalNormal'] = df['goalNormal'] + df['penaltyScored'] + df['goalAssistOwn']
        df.set_index(["id"], inplace=True)
        for key in player_stats:
            rounds = player_stats[key]['Rounds']
            attack_time = player_stats[key]["AttackTimes"]
            defend_time = player_stats[key]["DefendTimes"]
            teamId = player_stats[key]['team_id']
            if rounds == 0 or attack_time == 0 or defend_time == 0:
                continue
            dic = {}
            for stats in mapping_dic:
                if "PerDefense" in stats or "PerAttack" in stats:
                    dic[stats] = round(df.at[key, mapping_dic[stats]] / rounds * 100, 4)
                elif "PerD90m" in stats:
                    dic[stats] = round(df.at[key, mapping_dic[stats]] / defend_time * 90, 4)
                elif "PerA90m" in stats:
                    dic[stats] = round(df.at[key, mapping_dic[stats]] / attack_time * 90, 4)
                elif "Total" in stats:
                    dic[stats] = df.at[key, mapping_dic[stats]]
            for stats in dic:
                if "Total" in stats:
                    both_team_stats[teamId][stats] = both_team_stats[teamId][stats] + dic[stats]
            for stats in dic:
                if "PerDefense" in stats:
                    event = stats.replace("PerDefense", "")
                    both_team_stats[teamId][stats] = both_team_stats[teamId][event + "Total"] / both_team_stats[teamId][
                        "Rounds"] * 100
                if "PerAttack" in stats:
                    event = stats.replace("PerAttack", "")
                    both_team_stats[teamId][stats] = both_team_stats[teamId][event + "Total"] / both_team_stats[teamId][
                        "Rounds"] * 100
                elif "PerD90m" in stats:
                    event = stats.replace("PerD90m", "")
                    both_team_stats[teamId][stats] = both_team_stats[teamId][event + "Total"] / both_team_stats[teamId][
                        "DefendTimes"] * 90
                elif "PerA90m" in stats:
                    event = stats.replace("PerA90m", "")
                    both_team_stats[teamId][stats] = both_team_stats[teamId][event + "Total"] / both_team_stats[teamId][
                        "AttackTimes"] * 90
            player_stats[key].update(dic)
    player_stats_csv = []
    match_stats_csv = []
    for playerId in player_stats:
        player_stats_csv.append(player_stats[playerId])
    for teamId in both_team_stats:
        dic_tmp = both_team_stats[teamId].copy()
        dic_tmp["teamId"] = teamId
        match_stats_csv.append(dic_tmp)
    df1 = pd.DataFrame(player_stats_csv)
    df2 = pd.DataFrame(match_stats_csv)
    df1.to_csv(os.path.join(match_path, 'player_stats_per.csv'), mode='w', index=False)
    df2.to_csv(os.path.join(match_path, 'match_stats_per.csv'), mode='w', index=False)
    return both_team_stats


if __name__ == '__main__':
    # get_match_xG("matches/England-Premier-League/2018-2019/2018-08-20/Crystal Palace-Liverpool/match.json")
    # get_match_xG("matches/England-Premier-League/2018-2019/2018-09-15/Watford-Man Utd/match.json")
    # parse_events("matches/England-Premier-League/2018-2019/2018-09-15/Watford-Man Utd/match.json")
    # parse_events("match.json")
    # data = pd.read_csv('statistics/shots/shots.csv')
    # data = represent(parse_shots_from_match(load_json("matches/England-Premier-League/2019-2020/2020-07-26/Leicester-Man Utd/match.json")))
    # data.dropna()
    # data = data.T#.drop(['match_id', 'team_id', 'player_id', 'player_name', 'minute', 'goalMouthY', 'goalMouthZ'])
    # print(data.to_json('nn_xg/test_shots.json'))
    parse_player_event_data('../matches/England-Premier-League/2019-2020/2020-07-15/Arsenal-Liverpool/match.json')
    # parse_individual_stats('matches/England-Premier-League/2018-2019/2018-08-10/Man Utd-Leicester')
    pass
