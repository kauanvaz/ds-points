# %%

import mlflow
import mlflow.sklearn
import mlflow.models

import pandas as pd
import sqlalchemy
from sqlalchemy import exc
import json


# %%

print("Script para execução de modelos iniciado.")

print("Carregando modelo...")
mlflow.set_tracking_uri("http://127.0.0.1:8080")

model_name = "churn"
model_version_alias = "champion"
model_uri = f"models:/{model_name}@{model_version_alias}"

# pyfunc é uma abstração de modelo genérico, que pode ser usado para qualquer framework
# model = mlflow.pyfunc.load_model(model_uri=model_uri)
model = mlflow.sklearn.load_model(model_uri)

# %%

print("Carregando features do modelo...")
model_info = mlflow.models.get_model_info(model_uri)
features = [f["name"] for f in json.loads(model_info._signature_dict["inputs"])]
features

# %%

print("Carregando dados para score...")
engine = sqlalchemy.create_engine("sqlite:///../../data/feature_store.db")

with open("etl.sql", "r") as file:
    query = file.read()

df = pd.read_sql(query, engine)

# %%

print("Realizando predição...")
pred = model.predict_proba(df[features])
proba_churn = pred[:, 1]

# %%

print("Persistindo dados...")
df_predict = df[["dtRef", "idCustomer"]].copy()
df_predict["probaChurn"] = proba_churn.copy()

df_predict = df_predict.sort_values(
    by="probaChurn",
    ascending=False,
)

# %%

table_name = "tb_churn"

with engine.connect() as conn:
    statement = f"DELETE FROM {table_name} WHERE dtRef = '{df_predict['dtRef'].iloc[0]}'"
    try:
        conn.execute(sqlalchemy.text(statement))
        conn.commit()
    except exc.OperationalError as e:
        print(f"Tabela ainda não existe. Criando tabela...")

df_predict.to_sql(
    table_name,
    engine,
    if_exists="append",
    index=False,
)

print("Finalizado!")

# %%
