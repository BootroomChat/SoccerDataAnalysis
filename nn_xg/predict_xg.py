import csv
import json
import os

import numpy as np
import pandas as pd
import tensorflow as tf

HIDDEN_UNITS = [16]
OPTIMIZER = "Adam"

TRAINING_SET_FRACTION = 0.95
num_columns = ['x', 'y']
category_columns = ['shot_type', 'is_big_chance', 'is_from_corner',
                    'is_open_play', 'is_counter',
                    'is_set_piece', 'is_freekick', 'is_penalty', 'is_on_target', 'is_blocked', ]


def feature_columns():
    _feature_columns = []
    for key in num_columns:
        _feature_columns.append(tf.feature_column.numeric_column(key))

    for key in category_columns:
        category_column = tf.feature_column.categorical_column_with_vocabulary_list(key, ['0', '1'])
        _feature_columns.append(tf.feature_column.indicator_column(category_column))
    return _feature_columns


def load_json(file_name):
    try:
        with open(file_name, encoding="utf-8") as json_data:
            d = json.load(json_data)
            return d
    except Exception as e:
        print(e)
        return {}


def write_json(file_name, json_data):
    with open(file_name, 'w') as outfile:
        json.dump(json_data, outfile, ensure_ascii=False)
        return json_data


def map_results(results):
    features = {}

    for result in results:
        for key in result.keys():
            if key not in features:
                features[key] = []

            features[key].append(result[key])

    for key in features.keys():
        features[key] = np.array(features[key])

    return features, features['result']


def parse_data(data: dict):
    result = []
    for item in data.values():
        new_item = {key: item[key] for key in num_columns}
        new_item['shot_type'] = item['shot_type'] - 1
        for key in category_columns:
            new_item[key] = str(item[key])
        new_item['result'] = str(item['is_goal'])
        result.append(new_item)
    return result


xg_model_dir = 'xg_model'
if xg_model_dir not in os.listdir():
    xg_model_dir = os.path.join('nn_xg', xg_model_dir)
xg_model = tf.estimator.DNNClassifier(
    model_dir=xg_model_dir,
    hidden_units=HIDDEN_UNITS,
    feature_columns=feature_columns(),
    n_classes=2,
    label_vocabulary=['0', '1'],
    optimizer=OPTIMIZER)


def predict_shots(origin_test_data):
    test_data = parse_data(origin_test_data)
    test_results = test_data
    test_features, test_labels = map_results(test_results)

    tf.get_logger().setLevel('ERROR')
    test_input_fn = tf.compat.v1.estimator.inputs.numpy_input_fn(
        x=test_features,
        y=test_labels,
        num_epochs=1,
        shuffle=False
    )

    # evaluation_result = xg_model.evaluate(input_fn=test_input_fn)
    predictions = list(xg_model.predict(input_fn=test_input_fn))
    for i, prediction in enumerate(predictions):
        if i not in origin_test_data:
            i = str(i)
        origin_test_data[i]['xG'] = prediction['probabilities'][1]
    df = pd.DataFrame(origin_test_data).T
    return df


def predict():
    origin_test_data = load_json('test_shots.json')
    predict_shots(origin_test_data)


def main(argv):
    origin_data = load_json('shots.json')
    data = parse_data(origin_data)
    train_results_len = int(TRAINING_SET_FRACTION * len(data))
    train_results = data[:train_results_len]
    test_results = data[train_results_len:]

    train_features, train_labels = map_results(train_results)
    test_features, test_labels = map_results(test_results)

    train_input_fn = tf.compat.v1.estimator.inputs.numpy_input_fn(
        x=train_features,
        y=train_labels,
        batch_size=500,
        num_epochs=None,
        shuffle=True
    )

    test_input_fn = tf.compat.v1.estimator.inputs.numpy_input_fn(
        x=test_features,
        y=test_labels,
        num_epochs=1,
        shuffle=False
    )

    model = tf.estimator.DNNClassifier(
        model_dir='xg_model/',
        hidden_units=HIDDEN_UNITS,
        feature_columns=feature_columns(),
        n_classes=2,
        label_vocabulary=['0', '1'],
        optimizer=OPTIMIZER)

    with open('training-log.csv', 'w') as stream:
        csvwriter = csv.writer(stream)

        for i in range(0, 200):
            model.train(input_fn=train_input_fn, steps=100)
            evaluation_result = model.evaluate(input_fn=test_input_fn)

            predictions = list(model.predict(input_fn=test_input_fn))
            prediction_result = test_betting_stategy(predictions, test_features, test_labels)

            csvwriter.writerow([(i + 1) * 100, evaluation_result['accuracy'], evaluation_result['average_loss'],
                                prediction_result['performance']])


def test_betting_stategy(predictions, test_features, test_labels, bet_difference=0.05):
    result = {
        'spend': 0,
        'return': 0,
    }

    for i in range(0, len(predictions)):
        probabilities = predictions[i]['probabilities']
        result['spend'] = result['spend'] + int(test_labels[i])
        result['return'] = result['return'] + probabilities[1]
        # if probabilities[1] > (1 / test_features['odds-draw'][i]) + bet_difference:
        #     result['spend'] = result['spend'] + 1
        #
        #     if test_labels[i] == 'D':
        #         result['return'] = result['return'] + test_features['odds-draw'][i]
    print(result['return'])
    result['performance'] = result['return'] / result['spend']

    return result


if __name__ == '__main__':
    # tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.INFO)
    # tf.compat.v1.app.run(main=main)
    predict()
