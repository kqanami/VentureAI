# analysis/transformers.py

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

class LogBudgetTransformer(BaseEstimator, TransformerMixin):
    """Логарифмируем budget (колонка) через log1p."""
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        X_ = X.copy()
        if isinstance(X_, pd.DataFrame):
            if 'budget' in X_.columns:
                X_['budget'] = np.log1p(X_['budget'])
            else:
                X_.iloc[:,0] = np.log1p(X_.iloc[:,0])
        else:
            X_[:,0] = np.log1p(X_[:,0])
        return X_

class GeoDistanceTransformer(BaseEstimator, TransformerMixin):
    """
    Убираем latitude, longitude, заменяем их distance_km от (55.7558,37.6173).
    """
    def fit(self, X, y=None):
        return self
    def transform(self, X):
        X_ = X.copy()
        if isinstance(X_, pd.DataFrame):
            if 'latitude' in X_.columns and 'longitude' in X_.columns:
                clat, clon = 55.7558, 37.6173
                dlat = (X_['latitude'] - clat)*111.0
                dlon = (X_['longitude'] - clon)*67.5
                dist_km = np.sqrt(dlat**2 + dlon**2)
                X_['distance_km'] = dist_km
                X_.drop(['latitude','longitude'], axis=1, inplace=True)
        return X_
