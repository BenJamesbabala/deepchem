"""
Train low-data siamese models on Tox21. Test on SIDER. Test last fold only.
"""
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import numpy as np
import deepchem as dc
import tensorflow as tf
from datasets import load_sider_convmol
from datasets import load_tox21_convmol
from datasets import to_numpy_dataset

# Number of folds for split 
K = 4 
# num positive/negative ligands
n_pos = 10
n_neg = 10
# Set batch sizes for network
test_batch_size = 128
support_batch_size = n_pos + n_neg
nb_epochs = 1
n_train_trials = 2000
n_eval_trials = 20 
n_steps_per_trial = 1
learning_rate = 1e-4
log_every_n_samples = 50
# Number of features on conv-mols
n_feat = 71

sider_tasks, sider_dataset, _ = load_sider_convmol()
sider_dataset = to_numpy_dataset(sider_dataset)
tox21_tasks, tox21_dataset, _ = load_tox21_convmol()
tox21_dataset = to_numpy_dataset(tox21_dataset)

# Define metric
metric = dc.metrics.Metric(
    dc.metrics.roc_auc_score, verbosity="high", mode="classification")

# Train support model on train
support_model = dc.nn.SequentialSupportGraph(n_feat)

# Add layers
support_model.add(dc.nn.GraphConv(64, activation='relu'))
support_model.add(dc.nn.GraphPool())
support_model.add(dc.nn.GraphConv(128, activation='relu'))
support_model.add(dc.nn.GraphPool())
support_model.add(dc.nn.GraphConv(64, activation='relu'))
support_model.add(dc.nn.GraphPool())
support_model.add(dc.nn.Dense(128, activation='tanh'))

support_model.add_test(dc.nn.GraphGather(test_batch_size, activation='tanh'))
support_model.add_support(dc.nn.GraphGather(support_batch_size, activation='tanh'))

with tf.Session() as sess:
  model = dc.models.SupportGraphClassifier(
    sess, support_model, test_batch_size=test_batch_size,
    support_batch_size=support_batch_size, learning_rate=learning_rate,
    verbosity="high")

  ############################################################ DEBUG
  print("FIT")
  ############################################################ DEBUG
  model.fit(tox21_dataset, nb_epochs=nb_epochs,
            n_episodes_per_epoch=n_train_trials,
            n_pos=n_pos, n_neg=n_neg, log_every_n_samples=log_every_n_samples)
  ############################################################ DEBUG
  print("EVAL")
  ############################################################ DEBUG
  scores = model.evaluate(
      sider_dataset, metric, n_pos, n_neg, n_trials=n_eval_trials)
  print("Scores on evaluation dataset")
  print(scores)
