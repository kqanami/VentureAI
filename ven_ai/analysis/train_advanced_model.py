import numpy as np
import pandas as pd
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV
from sklearn.metrics import roc_auc_score
import joblib

# ВАЖНО: импортируем кастомные трансформеры ИЗ analysis/transformers
from ven_ai.transformers import LogBudgetTransformer, GeoDistanceTransformer


#############################################################################################
# Генерация синтетических данных с учётом геолокации
#############################################################################################

def generate_data(n=80000, random_state=42):
    """
    Генерим синтетические данные о бизнесе:
      - budget (log-распределение 50k..3kk)
      - competition (0.1..2.0)
      - marketing_skill (0..1)
      - team_experience (0..1)
      - latitude (55.4..56.0) / longitude (37.0..38.2) (примерный квадрат около Москвы)
      - На основании (lat, lon) считаем dist от (55.7558, 37.6173). Чем ближе, тем "location_factor" выше.
      - Линейная комбинация => вероятность успеха => success=0/1
    """
    np.random.seed(random_state)
    budget = np.exp(np.random.uniform(np.log(50000), np.log(3000000), n))
    competition = np.random.uniform(0.1, 2.0, n)
    marketing_skill = np.random.uniform(0, 1, n)
    team_experience = np.random.uniform(0, 1, n)
    lat = np.random.uniform(55.4, 56.0, n)
    lon = np.random.uniform(37.0, 38.2, n)
    clat, clon = 55.7558, 37.6173
    dlat = (lat - clat) * 111.0
    dlon = (lon - clon) * 67.5
    dist_km = np.sqrt(dlat**2 + dlon**2)
    loc_factor = 1.0 - np.tanh(dist_km / 8.0)
    loc_factor = np.clip(loc_factor, 0, 1)

    lin = (0.000001*budget) + (-1.0*competition) + (2.0*loc_factor) \
          + (3.0*marketing_skill) + (2.5*team_experience) + 0.1
    prob = 1/(1 + np.exp(-lin))
    success = (np.random.rand(n) < prob).astype(int)

    df = pd.DataFrame({
        'budget': budget,
        'competition': competition,
        'marketing_skill': marketing_skill,
        'team_experience': team_experience,
        'latitude': lat,
        'longitude': lon,
        'location_factor': loc_factor,
        'success': success
    })
    return df

#############################################################################################
# RandomizedSearchCV
#############################################################################################

def random_search(pipe, param_dist, X, y, n_iter=15):
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    rs = RandomizedSearchCV(
        estimator=pipe,
        param_distributions=param_dist,
        n_iter=n_iter,
        scoring='roc_auc',
        cv=skf,
        verbose=1,
        n_jobs=-1,
        random_state=42
    )
    rs.fit(X, y)
    print("Best params:", rs.best_params_)
    print("Best score:", rs.best_score_)
    return rs.best_estimator_

#############################################################################################
# Тренируем 4 модели
#############################################################################################

def train_four_models(X, y):
    preproc = Pipeline([
        # Вместо того, чтобы объявлять LogBudgetTransformer здесь, мы берём его из analysis.transformers
        ('log_budget', LogBudgetTransformer()),
        ('geo', GeoDistanceTransformer()),
        ('poly', PolynomialFeatures(degree=2, include_bias=False)),
        ('scaler', StandardScaler())
    ])

    # XGB
    xgb_clf = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    xgb_pipe = Pipeline([
        ('prep', preproc),
        ('model', xgb_clf)
    ])
    xgb_params = {
        'model__n_estimators': [100,200],
        'model__max_depth': [3,4,5],
        'model__learning_rate': [0.01,0.05,0.1],
        'model__subsample': [0.6,0.8,1.0],
        'model__colsample_bytree': [0.6,0.8,1.0]
    }
    print("=== XGBoost ===")
    best_xgb = random_search(xgb_pipe, xgb_params, X, y, n_iter=10)

    # LightGBM
    lgb_clf = lgb.LGBMClassifier(random_state=42)
    lgb_pipe = Pipeline([
        ('prep', preproc),
        ('model', lgb_clf)
    ])
    lgb_params = {
        'model__n_estimators': [100,200],
        'model__max_depth': [-1,3,4,5],
        'model__learning_rate': [0.01,0.05,0.1],
        'model__subsample': [0.6,0.8,1.0],
        'model__colsample_bytree': [0.6,0.8,1.0]
    }
    print("=== LightGBM ===")
    best_lgb = random_search(lgb_pipe, lgb_params, X, y, n_iter=10)

    # CatBoost
    cat_clf = CatBoostClassifier(silent=True, random_state=42, thread_count=-1)
    cat_pipe = Pipeline([
        ('prep', preproc),
        ('model', cat_clf)
    ])
    cat_params = {
        'model__iterations': [100,200],
        'model__depth': [3,4,5],
        'model__learning_rate': [0.01,0.05,0.1],
        'model__l2_leaf_reg': [1,3,5]
    }
    print("=== CatBoost ===")
    best_cat = random_search(cat_pipe, cat_params, X, y, n_iter=10)

    # RandomForest
    rf_clf = RandomForestClassifier(random_state=42)
    rf_pipe = Pipeline([
        ('prep', preproc),
        ('model', rf_clf)
    ])
    rf_params = {
        'model__n_estimators': [100,200],
        'model__max_depth': [3,5,7,None],
        'model__min_samples_leaf': [1,2,5]
    }
    print("=== RandomForest ===")
    best_rf = random_search(rf_pipe, rf_params, X, y, n_iter=10)

    return best_xgb, best_lgb, best_cat, best_rf

#############################################################################################
# Собираем Stacking (XGB, LGB, Cat, RF -> LR)
#############################################################################################

def build_stacking(models):
    ests = [
        ('xgb', models[0]),
        ('lgb', models[1]),
        ('cat', models[2]),
        ('rf' , models[3])
    ]
    final_est = LogisticRegression(random_state=42, max_iter=1000)
    stack = StackingClassifier(
        estimators=ests,
        final_estimator=final_est,
        cv=5,
        n_jobs=-1,
        verbose=1
    )
    return stack

#############################################################################################
# train_all() - объединяем всё
#############################################################################################

def train_all(df):
    X = df.drop('success', axis=1)
    y = df['success']
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    b1, b2, b3, b4 = train_four_models(X_tr, y_tr)
    stack = build_stacking((b1,b2,b3,b4))
    stack.fit(X_tr, y_tr)
    preds = stack.predict_proba(X_te)[:,1]
    auc = roc_auc_score(y_te, preds)
    print(f"Stacking AUC on test: {auc:.4f}")
    return stack


#############################################################################################
# Запуск
#############################################################################################

if __name__ == "__main__":
    print("Generating data with geo-locations for ~80k samples...")
    df = generate_data(n=80000)
    print("Training ensemble models + stacking...")
    model = train_all(df)
    print("Saving model to model.pkl...")
    joblib.dump(model, "../model.pkl")
    print("model.pkl done!")
