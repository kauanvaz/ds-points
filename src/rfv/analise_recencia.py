# %%

import pandas as pd
import sqlalchemy
import matplotlib.pyplot as plt

def ciclo_vida(row):

    if row['idadeBaseDias'] <=7:
        return '01-Nova'
    
    elif row['recenciaDias'] <= 2:
        return '02-Super Ativa'
    
    elif row['recenciaDias'] <= 6:
        return '03-Ativa Comum'
    
    elif row['recenciaDias'] <= 12:
        return '04-Ativa Fria'
    
    elif row['recenciaDias'] <= 18:
        return '05-Desiludida'
    
    else:
        return '06-Pre Churn'

# %%

engine = sqlalchemy.create_engine("sqlite:///../../data/feature_store.db")

query = """

SELECT *
FROM fs_general
WHERE dtRef = (SELECT MAX(dtRef) FROM fs_general)

"""

df = pd.read_sql(query, engine)

# %%

plt.figure(dpi=400)
df['recenciaDias'].hist()
plt.show()

# %%

df_recencia = df[["recenciaDias", "idadeBaseDias"]].sort_values(by="recenciaDias").reset_index()
df_recencia["unit"] = 1
df_recencia["acum"] = df_recencia["unit"].cumsum()
df_recencia["perc_acum"] = df_recencia["acum"] / df_recencia["acum"].max()

plt.plot(df_recencia["recenciaDias"], df_recencia["perc_acum"])
plt.grid(True)
plt.title("Dist. Recência Acumulada")
plt.xlabel("Recência")
plt.ylabel("Pct Acum")

# %%

df_recencia['CicloVida'] = df_recencia.apply(ciclo_vida, axis=1)

df_recencia.groupby(by=['CicloVida']).agg({
    "recenciaDias":['mean', 'count'],
    "idadeBaseDias":['mean'],
    })

# %%
