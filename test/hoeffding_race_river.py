"""
This is an informal implementation of hoeffding race idea, but instead of hoeffding bounds, we simply use a 
heuristic (i.e. constant) error as the point at which we switch over, with a linear penalty over time. 
"""

import numpy as np
from river import datasets
from river import linear_model
from river import metrics
from sklearn.preprocessing import StandardScaler
import copy


def train_test_split_indices(batch_size = 100, test_size = 0.3, seed=14):
    if test_size is None:
        test_size = 0.3

    if test_size < 1.:
        target_size = max(int(batch_size * test_size), 1)
    np.random.seed(seed)
    return np.random.choice(np.arange(batch_size), size=target_size, replace=False).flatten()


base_model = linear_model.LogisticRegression()
train_metric = metrics.ROCAUC()
test_metric = metrics.ROCAUC()

batch_size = 50
test_indx = train_test_split_indices(batch_size, 0.3, 14)

counter = None
for x, y in datasets.Phishing():
    if counter is None:
        counter = 0
        test_metric = metrics.ROCAUC()  # reset to compare fairly

    y_pred = base_model.predict_proba_one(x)
    if counter % batch_size in test_indx:
        test_metric.update(y, y_pred)
    else:
        train_metric = train_metric.update(y, y_pred)
        base_model = base_model.learn_one(x, y)

    counter += 1
    if counter == batch_size:
        counter = None
        print("Train ROC", train_metric, "\tTest ROC", test_metric, end="\r")
        break


# now freeze the model, and copy it over
print("Train ROC", train_metric, "\tTest ROC", test_metric)
print("Copying model over...", end="")
new_model = copy.deepcopy(base_model)
base_test_metric = metrics.ROCAUC()
new_test_metric = metrics.ROCAUC()

target_improvement = 5
print("[DONE]\n")

num_iters_no_improvement = 1
while True:
    base_test_hist = []
    new_test_hist = []
    for x, y in datasets.Phishing():
        if counter is None:
            counter = 0
            new_test_metric = metrics.ROCAUC()  # reset to compare fairly
            base_test_metric = metrics.ROCAUC()

        y_pred = base_model.predict_proba_one(x)
        new_y_pred = new_model.predict_proba_one(x)
        if counter % batch_size in test_indx:
            base_test_metric.update(y, y_pred)
            new_test_metric.update(y, new_y_pred)
        else:
            train_metric = train_metric.update(y, new_y_pred)
            new_model = new_model.learn_one(x, y)

        counter += 1
        if counter == batch_size:
            counter = None
            base_test_hist.append(base_test_metric.get())
            new_test_hist.append(new_test_metric.get())
            est_base = np.mean(base_test_hist)
            est_new = np.mean(new_test_hist)
            print("Iters", num_iters_no_improvement, "Train ROC", train_metric, "\th0 test ROC", est_base, "\th1 test ROC", est_new, end="\r")

            if (est_new - est_base) > (target_improvement/num_iters_no_improvement):
                num_iters_no_improvement = 1
                base_test_hist = []
                new_test_hist = []
                base_model = copy.deepcopy(new_model)
                print("\nModel has improved! Copyied over!")
            else:
                num_iters_no_improvement += 1

