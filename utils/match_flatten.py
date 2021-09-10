import csv
import json

STATS_KEYS = [u'id', u'team', u'name', u'position', u'playMins', u'result', u'goals', u'assists', u'goalsConceded',
              u'penaltyConceded',
              u'cornersTotal', u'aerialsWon', u'dribblesLost', u'shotsTotal', u'passesAccurate', u'tackleUnsuccesful',
              u'defensiveAerials', u'aerialsTotal', u'offensiveAerials', u'passesTotal', u'throwInsTotal',
              u'offsidesCaught', u'interceptions', u'ratings', u'touches', u'dispossessed', u'parriedSafe',
              u'claimsHigh',
              u'clearances', u'throwInAccuracy', u'collected', u'parriedDanger', u'possession', u'shotsOffTarget',
              u'dribblesAttempted',
              u'shotsOnPost', u'dribblesWon', u'cornersAccurate', u'tackleSuccess', u'throwInsAccurate',
              u'dribbleSuccess', u'errorsCount',
              u'aerialSuccess', u'shotsBlocked', u'tacklesTotal', u'tackleSuccessful', u'shotsOnTarget',
              u'dribbledPast',
              u'passesKey', u'foulsCommited', u'totalSaves', u'passSuccess', u'claimsTotal', u'claimsGround']


def parse_stats(data):
    # keys:
    # [u'startDate', u'periodCode', u'home', u'attendance', u'expandedMinutes',
    # u'away', u'timeStamp', u'score', u'etScore', u'commonEvents', u'events', u'referee',
    # u'maxMinute', u'elapsed', u'pkScore', u'startTime', u'weatherCode',
    # u'expandedMaxMinute', u'periodMinuteLimits', u'timeoutInSeconds', u'periodEndMinutes',
    # u'htScore', u'playerIdNameDictionary', u'maxPeriod', u'minuteExpanded', u'venueName',
    # u'statusCode', u'ftScore']
    stats = []
    penaltyConceded = {}
    assists = {}
    team_fields = ['home', 'away']
    goals = {}
    goals_mins = {'home': [], 'away': []}

    for event in data['events']:
        # penaltyConceded: 133
        if 133 in event.get(u'satisfiedEventsTypes', []):
            penaltyConceded[event[u'playerId']] = penaltyConceded.get(
                event['playerId'], 0) + 1
        # assist: 91
        if 91 in event.get(u'satisfiedEventsTypes', []):
            assists[event[u'playerId']] = assists.get(event['playerId'], 0) + 1
    for team in team_fields:
        # keys:
        # [u'averageAge', u'stats', u'name', u'incidentEvents', u'players', u'formations',
        # u'countryName', u'field', u'teamId', u'scores', u'shotZones', u'managerName']
        for event in data[team].get('incidentEvents', []):
            if 'isGoal' in event:
                goals[event[u'playerId']] = goals.get(event['playerId'], 0) + 1
                goals_mins[team].append(int(event['expandedMinute']))
    for team in team_fields:
        other_team = team_fields[1 - team_fields.index(team)]
        for player in data[team]['players']:
            # keys:
            # [u'shirtNo', u'stats', u'name', u'weight', u'playerId', u'age',
            # u'height', u'isManOfTheMatch', u'field', u'isFirstEleven', u'position']
            # stats keys:
            # [u'cornersTotal', u'aerialsWon', u'dribblesLost', u'shotsTotal', u'passesAccurate',
            # u'tackleUnsuccesful', u'defensiveAerials', u'aerialsTotal', u'offensiveAerials',
            # u'passesTotal', u'throwInsTotal', u'dispossessed', u'interceptions', u'ratings',
            # u'touches', u'offsidesCaught', u'parriedSafe', u'clearances', u'throwInAccuracy',
            # u'collected', u'parriedDanger', u'possession', u'shotsOffTarget', u'dribblesAttempted',
            # u'dribblesWon', u'cornersAccurate', u'tackleSuccess', u'throwInsAccurate', u'dribbleSuccess',
            # u'errors', u'aerialSuccess', u'tacklesTotal', u'tackleSuccessful', u'shotsOnTarget',
            # u'passesKey', u'dribbledPast', u'foulsCommited', u'shotsBlocked', u'totalSaves', u'passSuccess']
            player_stats = {u'name': player['name'], u'id': player['playerId'],
                            u'position': player['position'], u'team': data[team]['name']}
            for key, values in player['stats'].items():
                if key not in [u'ratings', u'errors']:
                    player_stats[key] = sum(values.values())
                player_stats[u'errorsCount'] = sum(
                    player['stats'].get(u'errors', {}).values())
            player_stats['goals'] = goals.get(player['playerId'], 0)
            player_stats['penaltyConceded'] = penaltyConceded.get(
                player['playerId'], 0)
            player_stats['assists'] = assists.get(player['playerId'], 0)
            if 'isFirstEleven' in player:
                player_stats['playMins'] = player.get(
                    'subbedOutExpandedMinute', 90)
                player_stats['goalsConceded'] = sum(x <= player.get(
                    'subbedOutExpandedMinute', data['expandedMaxMinute']) for x in goals_mins[other_team])
            else:
                player_stats['playMins'] = abs(
                    data['expandedMaxMinute'] - player.get('subbedInExpandedMinute', data['expandedMaxMinute']))
                player_stats['goalsConceded'] = sum(x >= player.get(
                    'subbedInExpandedMinute', data['expandedMaxMinute']) for x in goals_mins[other_team])
            stats.append(player_stats)
    return stats


if __name__ == '__main__':
    file = '..\\\\matches\\England-FA-Cup\\2019-2020\\2020-01-05\\Liverpool-Everton\\match.json'
    with open(file, encoding="utf-8") as json_data:
        d = json.load(json_data)
        stats = parse_stats(d)
        with open(file.replace('.json', '.csv'), 'w') as output_file:
            dict_writer = csv.DictWriter(
                output_file, fieldnames=STATS_KEYS, restval=0)
            dict_writer.writeheader()
            dict_writer.writerows(stats)
