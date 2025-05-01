# %%
import pandas as pd
import sqlalchemy

import mlflow

from sklearn import model_selection
from sklearn import ensemble
from sklearn import pipeline
from sklearn import metrics

from feature_engine import encoding

# %%

# Conexão com o banco
engine = sqlalchemy.create_engine("sqlite:///..//../data/feature_store.db")

with open("abt.sql", "r") as file:
    query = file.read()

# Processa e trás os dados
df = pd.read_sql(query, engine)

df.head()

# %%

# Separação de bases entre treino e OOT
df_oot = df[df["dtRef"] == df["dtRef"].max()]
df_train = df[df["dtRef"] < df["dtRef"].max()]

# %%

target = "flChurn"
features = df_train.columns[3:].to_list()

# %%

X_train, X_test, y_train, y_test = model_selection.train_test_split(df_train[features],
                                                    df_train[target],
                                                    train_size=0.8,
                                                    random_state=42,
                                                    stratify=df_train[target])

print(f"Taxa de resposta na base de treino: {y_train.mean()}")
print(f"Taxa de resposta na base de teste: {y_test.mean()}")

# %%

categorical_features = X_train.dtypes[X_train.dtypes == "object"].index.to_list()
numerical_features = list(set(features) - set(categorical_features))

# %%

X_train[categorical_features].describe()

# %%

X_train[numerical_features].describe().T

# %%

X_train[numerical_features].isna().sum().max()

# %%

mlflow.set_tracking_uri("http://127.0.0.1:8080")
mlflow.set_experiment(experiment_id=731855451777011968)

# Ativa o registro automático de parâmetros, métricas e artefatos do modelo durante o treinamento
mlflow.autolog()

# %%

def report_metrics(y_true, y_proba, base, cohort=0.5):

    y_pred = (y_proba[:,1]>cohort).astype(int)

    acc = metrics.accuracy_score(y_true, y_pred)
    auc = metrics.roc_auc_score(y_true, y_proba[:,1])
    precision = metrics.precision_score(y_true, y_pred)
    recall = metrics.recall_score(y_true, y_pred)

    res = {
        f"{base}_Acurácia": acc,
        f"{base}_Curva Roc": auc,
        f"{base}_Precisão": precision,
        f"{base}_Recall": recall,
        }

    return res

# %%

with mlflow.start_run():
    onehot = encoding.OneHotEncoder(
        variables=categorical_features,
        drop_last=True
    )

    model = ensemble.GradientBoostingClassifier(random_state=42)

    params = {
        "learning_rate": [0.01, 0.1, 0.5, 0.75, 0.9],
        "n_estimators": [100, 200, 500],
        "subsample": [0.1, 0.5, 0.75, 0.9],
        "min_samples_leaf": [5, 10, 25, 50, 100],
    }

    grid = model_selection.GridSearchCV(
        model,
        param_grid=params,
        cv=3,
        scoring="roc_auc",
        verbose=3
    )

    model_pipeline = pipeline.Pipeline(steps=[
        ("One Hot Encoder", onehot),
        ("Modelo", grid)
    ])

    # Ajusta o modelo
    model_pipeline.fit(X_train, y_train)

    y_train_proba = model_pipeline.predict_proba(X_train)
    y_test_proba = model_pipeline.predict_proba(X_test)
    y_oot_proba = model_pipeline.predict_proba(df_oot[features])

    report = {}
    report.update(report_metrics(y_train, y_train_proba, "treino"))
    report.update(report_metrics(y_test, y_test_proba, "teste"))
    report.update(report_metrics(df_oot[target], y_oot_proba, "oot"))

    mlflow.log_metrics(report)

# %%
