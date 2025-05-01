# %%

import pandas as pd
import sqlalchemy
from sqlalchemy import exc

# %%

print("Script para execução de modelos iniciado.")

print("Carregando modelo...")
model_series = pd.read_pickle("../../models/random_forest.pkl")

# %%

print("Carregando dados para score...")
engine = sqlalchemy.create_engine("sqlite:///../../data/feature_store.db")

with open("etl.sql", "r") as file:
    query = file.read()

df = pd.read_sql(query, engine)

# %%

print("Realizando predição...")
pred = model_series["model"].predict_proba(df[model_series["features"]])
proba_churn = pred[:, 1]

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
