# %%
from pathlib import Path
import argparse
from datetime import datetime, timedelta

import pandas as pd
import sqlalchemy
from sqlalchemy import exc

from tqdm import tqdm

def import_query(path):
    # Diretório onde o script está localizado
    base_path = Path(__file__).resolve().parent
    full_path = base_path / path

    with open(full_path, 'r') as file:
        return file.read()

def date_range(start, stop):
    dt_start = datetime.strptime(start, '%Y-%m-%d')
    dt_stop = datetime.strptime(stop, '%Y-%m-%d')
    dates = []

    while dt_start <= dt_stop:
        dates.append(dt_start.strftime('%Y-%m-%d'))
        dt_start = dt_start + timedelta(days=1)

    return dates

def ingest_date(query, table, dt):
    # Substitui de '{date}' por uma data no formato yyyy-mm-dd
    query_formatted = query.format(date=dt)

    # Executa e trás o resultado para Python
    df = pd.read_sql(query_formatted, ORIGIN_ENGINE)

    # Deleta os dados com a data de referência para garantir integridade
    with TARGET_ENGINE.connect() as conn:
        try:
            statement = f"DELETE FROM {table} WHERE dtRef = '{dt}';"
            conn.execute(sqlalchemy.text(statement))
            conn.commit()
        except exc.OperationalError:
            print('\nTabela não existe. Criando...')

    # Envia os dados para o novo database
    df.to_sql(table, TARGET_ENGINE, index=False, if_exists='append')

# %%

ORIGIN_ENGINE = sqlalchemy.create_engine("sqlite:///../../data/database.db")
TARGET_ENGINE = sqlalchemy.create_engine("sqlite:///../../data/feature_store.db")

# %%

now = datetime.now().strftime('%Y-%m-%d')

parser = argparse.ArgumentParser()
parser.add_argument("--feature_store", "-f", help="Nome da feature store", type=str)
parser.add_argument("--start", "-s", help="Data de início", default=now, type=str)
parser.add_argument("--stop", "-p", help="Data de fim", default=now, type=str)
args = parser.parse_args()

query = import_query(f'{args.feature_store}.sql')
dates = date_range(args.start, args.stop)

for i in tqdm(dates):
    ingest_date(query, args.feature_store, i)

# %%
