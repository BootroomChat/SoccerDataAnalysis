from datetime import date

import lightgbm as lgb
from sklearn import metrics
from sklearn.metrics import mean_squared_error
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split, GridSearchCV
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
    corner = pd.read_csv("corner_input_3.csv").drop('Unnamed: 0', axis=1)
    corner['c_corner'] = corner['total_corner'].apply(lambda x: 1 if x > 11.5 else 0)
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
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.20)
    train_data = lgb.Dataset(data=x_train, label=y_train)
    test_data = lgb.Dataset(data=x_test, label=y_test)
    train_data.save_binary("wine_lightgbm_train.bin")

    params = {
        'boosting_type': 'gbdt',
        'objective': 'binary',
        'metric': 'auc',
        'verbose': -1,
        'learning_rate': 0.1,
        'max_depth': 2,
        'num_leaves': 2,
    }
    # params['metric'] = 'rmse'
    #
    # # Training a model requires a parameter list and data set:
    num_round = 10
    bst = lgb.train(params, train_data, num_round, valid_sets=[test_data])
    # # # After training, the model can be saved:
    # bst.save_model('model.txt')
    # # A saved model can be loaded:
    # bst = lgb.Booster(model_file='model.txt')

    #
    # estimator = lgb.sklearn.LGBMClassifier()
    # estimator.fit(x_train, y_train)
    # pre = estimator.predict(x_test)
    # print(pre)
    # # Accuracy
    # estimator = lgb.sklearn.LGBMClassifier()
    # estimator.fit(x_train, y_train)
    # train_trained = bst.predict(x_train)
    # train_test = bst.predict(x_test)
    # print(metrics.accuracy_score(y_train, train_trained))
    # print(metrics.accuracy_score(y_test, train_test))
    # # Importance
    corner = pd.read_csv("corner_input.csv").drop('Unnamed: 0', axis=1)
    corner['c_corner'] = corner['total_corner'].apply(lambda x: 1 if x > 11.5 else 0)
    X = corner.drop(['c_corner', "total_corner"], axis=1)
    plot_feature_importance(X, bst)

    # Use GridSearchCV to adjust params

    parameters = {
        'max_depth': range(2, 8, 1),
        'num_leaves': range(2, 16, 2),
        'learning_rate': np.array([0.1, 0.05]),

    }
    gbm = lgb.LGBMClassifier(boosting_type='gbdt',
                             objective='binary',
                             metric='auc',
                             verbose=-1,
                             learning_rate=0.1,
                             max_depth=4,
                             num_leaves=8,
                             min_data_in_leaf=20)
    gsearch = GridSearchCV(gbm, param_grid=parameters, scoring='accuracy', cv=5)
    gsearch.fit(x_train, y_train)

    print("Best score: %0.3f" % gsearch.best_score_)
    print("Best parameters set:")
    best_parameters = gsearch.best_estimator_.get_params()
    for param_name in sorted(parameters.keys()):
        print("\t%s: %r" % (param_name, best_parameters[param_name]))

    # Use the fit params
    gbm = lgb.LGBMClassifier(boosting_type='gbdt',
                             objective='binary',
                             metric='auc',
                             verbose=-1,
                             learning_rate=0.1,
                             max_depth=4,
                             num_leaves=8,
                             min_data_in_leaf=20)
    bst = gbm.fit(x_train, y_train)
    y_train_predict = bst.predict(x_train)
    y_test_predict = bst.predict(x_test)
    print(metrics.accuracy_score(y_train, y_train_predict))
    print(metrics.accuracy_score(y_test, y_test_predict))
    # plot_feature_importance(X, bst)

    # Predict
    data = get_match_data(match_date=date(2021, 9, 18), home_name='Liverpool', away_name='Crystal Palace',
                          filter_='Premier',n=3).values
    result = bst.predict(data)
    print(result)