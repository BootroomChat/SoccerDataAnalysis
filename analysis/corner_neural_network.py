import numpy as np
from sklearn import neural_network
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier as DNN
from sklearn.metrics import accuracy_score
from sklearn.model_selection import cross_val_score as cv, train_test_split
import matplotlib.pyplot as plt
from sklearn.datasets import load_breast_cancer
from sklearn.tree import DecisionTreeClassifier as DTC
from sklearn.model_selection import train_test_split as TTS
import pandas as pd


def get_classied_data():
    corner = pd.read_csv("corner_input_5_liv.csv").drop('Unnamed: 0', axis=1)
    corner['c_corner'] = corner['total_corner'].apply(lambda x: 1 if x > 11.5 else 0)
    y = np.array(corner['c_corner'])
    X = np.array(corner.drop(['c_corner', "total_corner"], axis=1))
    columns = np.array(corner.columns)
    return X, y, columns


def GetNewDataByPandas():
    corner = pd.read_csv("corner_input.csv").drop('Unnamed: 0', axis=1)
    y = np.array(corner['total_corner'])
    X = np.array(corner.drop("total_corner", axis=1))
    columns = np.array(corner.columns)
    return X, y, columns


if __name__ == '__main__':
    X, y, corner_names = get_classied_data()
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.20)
    model = LogisticRegression(solver='liblinear')
    model.fit(x_train, y_train)
    # 训练模型的系数
    print('Coefficient of model :', model.coef_)
    # 拦截模型
    print('Intercept of model', model.intercept_)
    # In[35]:
    # 预测训练数据集
    predict_train = model.predict(x_train)
    # 训练数据集得分
    accuracy_train = accuracy_score(y_train, predict_train)
    print('accuracy_score on train dataset : ', accuracy_train)
    # In[36]:
    # 预测测试数据集
    predict_test = model.predict(x_test)
    # 测试数据集得分
    accuracy_test = accuracy_score(y_test, predict_test)
    print('accuracy_score on test dataset : ', accuracy_test)
    # dnn = DNN(hidden_layer_sizes=(100,), random_state=420)
    # dnn = DNN(hidden_layer_sizes=(100,), random_state=420).fit(x_train, y_train)
    # print("准确率为：", dnn.score(x_test, y_test))
    s = []
    for i in range(5, 200, 5):
        dnn = DNN(hidden_layer_sizes=(int(i),), activation="relu",
                  solver='adam', alpha=0.0001,
                  batch_size='auto', learning_rate="constant",
                  learning_rate_init=0.001, power_t=0.5, max_iter=200, tol=1e-4).fit(x_train, y_train)
        s.append(dnn.score(x_test, y_test))
        print(i, max(s))
    plt.figure(figsize=(20, 5))
    plt.plot(range(5, 200, 5), s)
    plt.show()
    # 增加隐藏层，控制神经元个数
    # s = []
    # layers = [(170,), (170, 170), (170, 170, 170), (170, 170, 170, 170), (170, 170, 170, 170, 170),
    #           (170, 170, 170, 170, 170, 170)]
    # for i in layers:
    #     dnn = DNN(hidden_layer_sizes=(i), random_state=420).fit(x_train, y_train)
    #     s.append(dnn.score(x_test, y_test))
    #     print(i, max(s))
    # plt.figure(figsize=(20, 5))
    # plt.plot(range(3, 9), s)
    # plt.xticks([3, 4, 5, 6, 7, 8])
    # plt.xlabel("Total number of layers")
    # plt.show()
    # # 增加隐藏层，控制神经元个数
    # s = []
    # layers = [(10,10), (15, 15), (20, 20, 20), (30, 30, 30, 30)]
    # for i in layers:
    #     dnn = DNN(hidden_layer_sizes=(i), random_state=420).fit(x_train, y_train)
    #     s.append(dnn.score(x_test, y_test))
    #     print(i, max(s))
    # plt.figure(figsize=(20, 5))
    # plt.plot(range(3, 7), s)
    # plt.xticks([3, 4, 5, 6])
    # plt.xlabel("Total number of layers")
    # plt.show()

    mlp = neural_network.MLPRegressor(hidden_layer_sizes=(10), activation="relu",
                                      solver='adam', alpha=0.0001,
                                      batch_size='auto', learning_rate="constant",
                                      learning_rate_init=0.001,
                                      power_t=0.5, max_iter=200, tol=1e-4)

    X, y, corner_names = GetNewDataByPandas()
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.20)
    mlp.fit(x_train, y_train)
    pre = mlp.predict(x_test)
    plt.plot(np.asarray(x_train), np.asarray(y_train), 'bo')
    plt.plot(np.asarray(x_test), np.asarray(pre), 'ro')
    plt.show()
