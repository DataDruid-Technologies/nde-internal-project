# import python and posgres libraries
import numpy as np
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# set up db credentials 
# db creds:
# DB_USERNAME=ibukun_npc_db_user
# DB_PASSWORD=umIldFN19UXEGVdt
# DB_HOST=ecrvs-staging-db.cluster-cattiozvrzdj.eu-west-3.rds.amazonaws.com
# DB_PORT=5432
# DB_NAME=ecrvs
# VPN creds:
# username: ibukun_npc
# password: 8AdVpdtQpm03FZCb

username = 'ibukun_npc_db_user'
password = 'umIldFN19UXEGVdt'
host = 'ecrvs-staging-db.cluster-cattiozvrzdj.eu-west-3.rds.amazonaws.com'
port = 5432
database = 'ecrvs'

connection = psycopg2.connect(user=username, password=password, host=host, port=port, database=database)
cursor = connection.cursor()