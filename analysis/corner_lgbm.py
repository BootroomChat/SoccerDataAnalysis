from datetime import date

import lightgbm as lgb
from sklearn import metrics
from sklearn.metrics import mean_squared_error
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

from analysis.corner import get_match_data


def GetNewDataByPandas():
    corner = pd.read_csv("corner_input.csv").drop('Unnamed: 0', axis=1)
    y = np.array(corner['total_corner'])
    X = np.array(corner.drop("total_corner", axis=1))
    columns = np.array(corner.columns)
    return X, y, columns


def get_classied_data():
    corner = pd.read_csv("corner_input.csv").drop('Unnamed: 0', axis=1)
    corner['c_corner'] = corner['total_corner'].apply(lambda x: 1 if x > 10.5 else 0)
    y = np.array(corner['c_corner'])
    X = np.array(corner.drop(['c_corner', "total_corner"], axis=1))
    columns = np.array(corner.columns)
    return X, y, columns


def plot_feature_importance(dataset, model_bst):
    list_feature_name = list(dataset.columns)
    list_feature_importance = list(model_bst.feature_importance(
        importance_type='split', iteration=-1))
    dataframe_feature_importance = pd.DataFrame(
        {'feature_name': list_feature_name, 'importance': list_feature_importance})
    print(dataframe_feature_importance)
    x = range(len(list_feature_name))
    plt.xticks(x, list_feature_name, rotation=90, fontsize=14)
    plt.plot(x, list_feature_importance)
    for i in x:
        plt.axvline(i)
    plt.show()


if __name__ == '__main__':
    X, y, corner_names = get_classied_data()
    # split data to [[0.8,0.2],01]
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.10, random_state=100)
    train_data = lgb.Dataset(data=x_train, label=y_train)
    test_data = lgb.Dataset(data=x_test, label=y_test)
    train_data.save_binary("wine_lightgbm_train.bin")

    params = {
        'boosting_type': 'gbdt',
        'objective': 'regression',
        'learning_rate': 0.005,
        'max_depth': 7,
        'min_data_in_leaf': 20,
        'subsample': 1,
        'colsample_bytree': 0.7,
        'num_leaves': 310
    }
    params['metric'] = 'rmse'

    # Training a model requires a parameter list and data set:
    num_round = 10
    bst = lgb.train(params, train_data, num_round, valid_sets=[test_data])
    # After training, the model can be saved:
    bst.save_model('model.txt')
    # A saved model can be loaded:
    bst = lgb.Booster(model_file='model.txt')
    # Predict
    data = get_match_data(match_date=date(2021, 9, 17), home_name='Newcastle', away_name='Leeds',
                          filter_='Premier').values
    result = bst.predict(data)
    print(result)

    estimator = lgb.sklearn.LGBMClassifier()
    estimator.fit(x_train, y_train)
    pre = estimator.predict(x_test)
    print(pre)
    # Accuracy
    estimator = lgb.sklearn.LGBMClassifier()
    estimator.fit(x_train, y_train)
    train_trained = estimator.predict(x_train)
    train_test = estimator.predict(x_test)
    pre = estimator.predict(x_test)
    print(metrics.accuracy_score(y_train, train_trained))
    print(metrics.accuracy_score(y_test, train_test))
    # Importance
    corner = pd.read_csv("corner_input.csv").drop('Unnamed: 0', axis=1)
    corner['c_corner'] = corner['total_corner'].apply(lambda x: 1 if x > 10.5 else 0)
    X = corner.drop(['c_corner', "total_corner"], axis=1)
    plot_feature_importance(X, bst)
