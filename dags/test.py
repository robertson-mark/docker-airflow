

from datetime import datetime, timedelta
import os
from basin import Basin
from config import Config

# This gets fields from /home/ops/wy2020/docker-airflow_dag_config.ini
core_config = "/home/ops/wy2020/docker-airflow_CoreConfig.ini"
config_file = "/home/ops/wy2020/docker-airflow_dag_config.ini"
cfg = Config(core_config, config_file)
args = cfg.args
snowav_args = cfg.snowav_args
