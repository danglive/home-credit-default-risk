# Copyright 2018 Mamy André-Ratsimbazafy. All rights reserved.

import numpy as np
import xgboost as xgb
import logging
from sklearn.metrics import roc_auc_score
from src.xgb_cross_val import xgb_cross_val

## Get the same logger from main"
logger = logging.getLogger("HomeCredit")

def _clf_xgb(x_trn, x_val, y_trn, y_val, xgb_params, seed_val=0, num_rounds=4096):

    num_rounds = num_rounds
    xgtrain = xgb.DMatrix(x_trn, label=y_trn)
    xgtest = xgb.DMatrix(x_val, label=y_val)

    logger.info('Start Validation training on 80% of the dataset...')
    # train
    watchlist = [ (xgtest, 'test') ]
    model = xgb.train(xgb_params, xgtrain, num_rounds, watchlist, early_stopping_rounds=50)
    logger.info('End trainind on 80% of the dataset...')
    logger.info('Start validating prediction on 20% unseen data')
    # predict
    y_pred = model.predict(xgtest, ntree_limit=model.best_ntree_limit)

    return model, y_pred, model.best_ntree_limit

def xgb_train_cv(x_trn, x_val, y_trn, y_val, X_train, y_train, xgb_params, folds):

    clf, y_pred, n_stop = _clf_xgb(x_trn, x_val, y_trn, y_val, xgb_params)

    # eval
    metric = roc_auc_score(y_val, y_pred)
    logger.info(f'We stopped at boosting round:  {n_stop}')
    logger.info(f'The ROC AUC on validation set is: {metric}\n')

    xgtrain = xgb.DMatrix(X_train, label=y_train)

    logger.info('Cross validating Stratified 7-fold... and retrieving best stopping round')

    mean_round = xgb_cross_val(xgb_params, X_train, y_train, folds, metric)

    logger.info('Start Training on the whole dataset...')
    n_stop = np.int(mean_round * 1.1) # Full dataset is 25% bigger, so we want a bit of leeway on stopping round to avoid overfitting.
    final_clf = xgb.train(xgb_params, xgtrain, n_stop)

    return final_clf, metric, n_stop
