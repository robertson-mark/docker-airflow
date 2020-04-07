"""
Code that goes along with the Airflow located at:
http://airflow.readthedocs.org/en/latest/tutorial.html

DAG settings and basin-specific settings are read from the config file in
/home/ops/wy2020/docker-airflow_dag_config.ini

"""
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import os

from basin import Basin
from config import Config


core_config = os.path.abspath(os.path.join(os.getcwd(),
                                           "..",
                                           "config/",
                                           "docker-airflow_CoreConfig.ini"))
config_file = "/home/ops/wy2020/docker-airflow_dag_config.ini"
cfg = Config(core_config, config_file)
args = cfg.args
snowav_args = cfg.snowav_args

###############################################################################
#                               Tuolumne
###############################################################################
ts = Config(core_config, config_file, 'tuolumne')
tuolumne = Basin(cfg.settings, ts.basin_settings)
dag = DAG('tuolumne', catchup=True, default_args=args, schedule_interval='0 8 * * *')

t1 = PythonOperator(
    task_id='katana',
    provide_context=True,
    python_callable=tuolumne.run_katana_daily,
    dag=dag,
    depends_on_past=True,
    wait_for_downstream=False)

t2 = PythonOperator(
    task_id='awsm',
    provide_context=True,
    python_callable=tuolumne.full_awsm_day,
    dag=dag,
    depends_on_past=True,
    wait_for_downstream=True)

t3 = PythonOperator(
    task_id='backup',
    provide_context=True,
    python_callable=tuolumne.backup_ops,
    dag=dag,
    depends_on_past=True)

t4 = PythonOperator(
    task_id='commit',
    provide_context=True,
    python_callable=tuolumne.commit_backup,
    dag=dag,
    depends_on_past=True)

t5 = PythonOperator(
    task_id='geoserver',
    provide_context=True,
    python_callable=tuolumne.do_guds,
    dag=dag,
    depends_on_past=True)

t1.set_downstream(t2)
t2.set_downstream(t3)
t3.set_downstream(t4)
t4.set_downstream(t5)

###############################################################################
#                               San Joaquin
###############################################################################
ss = Config(core_config, config_file, 'sanjoaquin')
sanjoaquin = Basin(cfg.settings, ss.basin_settings)
dag_sanjoaquin = DAG('sanjoaquin', catchup=True, default_args=args, schedule_interval='0 8 * * *')

s1 = PythonOperator(
    task_id='katana',
    provide_context=True,
    python_callable=sanjoaquin.run_katana_daily,
    dag=dag_sanjoaquin,
    depends_on_past=True,
    wait_for_downstream=False)

s2 = PythonOperator(
    task_id='awsm',
    provide_context=True,
    python_callable=sanjoaquin.full_awsm_day,
    dag=dag_sanjoaquin,
    retries=0,
    depends_on_past=True,
    wait_for_downstream=True)

s3 = PythonOperator(
    task_id='backup',
    provide_context=True,
    python_callable=sanjoaquin.backup_ops,
    dag=dag_sanjoaquin,
    depends_on_past=True,
    wait_for_downstream=True)

s4 = PythonOperator(
    task_id='commit',
    provide_context=True,
    python_callable=sanjoaquin.commit_backup,
    dag=dag_sanjoaquin,
    depends_on_past=True,
    wait_for_downstream=True)

s5 = PythonOperator(
    task_id='geoserver',
    provide_context=True,
    python_callable=sanjoaquin.do_guds,
    dag=dag_sanjoaquin,
    depends_on_past=True)

s1.set_downstream(s2)
s2.set_downstream(s3)
s3.set_downstream(s4)
s4.set_downstream(s5)

###############################################################################
#                               Kings
###############################################################################
ks = Config(core_config, config_file, 'kings')
kings = Basin(cfg.settings, ks.basin_settings)
dag_kings = DAG('kings', catchup=True, default_args=args, schedule_interval='0 8 * * *')

k1 = PythonOperator(
    task_id='katana',
    provide_context=True,
    python_callable=kings.run_katana_daily,
    dag=dag_kings,
    depends_on_past=True,
    wait_for_downstream=False)

k2 = PythonOperator(
    task_id='awsm',
    provide_context=True,
    python_callable=kings.full_awsm_day,
    dag=dag_kings,
    retries=0,
    depends_on_past=True,
    wait_for_downstream=True)

k3 = PythonOperator(
    task_id='backup',
    provide_context=True,
    python_callable=kings.backup_ops,
    dag=dag_kings,
    depends_on_past=True,
    wait_for_downstream=True)

k4 = PythonOperator(
    task_id='commit',
    provide_context=True,
    python_callable=kings.commit_backup,
    dag=dag_kings,
    depends_on_past=True,
    wait_for_downstream=True)

k5 = PythonOperator(
    task_id='geoserver',
    provide_context=True,
    python_callable=kings.do_guds,
    dag=dag_kings,
    depends_on_past=True)

k1.set_downstream(k2)
k2.set_downstream(k3)
k3.set_downstream(k4)
k4.set_downstream(k5)

###############################################################################
#                               Lakes
###############################################################################
ls = Config(core_config, config_file, 'lakes')
lakes = Basin(cfg.settings, ls.basin_settings)
dag_lakes = DAG('lakes', catchup=True, default_args=args, schedule_interval='0 8 * * *')

l1 = PythonOperator(
    task_id='katana',
    provide_context=True,
    python_callable=lakes.run_katana_daily,
    dag=dag_lakes,
    depends_on_past=True,
    wait_for_downstream=False)

l2 = PythonOperator(
    task_id='awsm',
    provide_context=True,
    python_callable=lakes.full_awsm_day,
    dag=dag_lakes,
    depends_on_past=True,
    wait_for_downstream=True)

l3 = PythonOperator(
    task_id='backup',
    provide_context=True,
    python_callable=lakes.backup_ops,
    dag=dag_lakes,
    depends_on_past=True,
    wait_for_downstream=True)

l4 = PythonOperator(
    task_id='commit',
    provide_context=True,
    python_callable=lakes.commit_backup,
    dag=dag_lakes,
    depends_on_past=True,
    wait_for_downstream=True)

l5 = PythonOperator(
    task_id='geoserver',
    provide_context=True,
    python_callable=lakes.do_guds,
    dag=dag_lakes,
    depends_on_past=True)

l1.set_downstream(l2)
l2.set_downstream(l3)
l3.set_downstream(l4)
l4.set_downstream(l5)

###############################################################################
#                               Merced
###############################################################################
ms = Config(core_config, config_file, 'merced')
merced = Basin(cfg.settings, ms.basin_settings)
dag_merced = DAG('merced', catchup=True, default_args=args, schedule_interval='0 8 * * *')

m1 = PythonOperator(
    task_id='katana',
    provide_context=True,
    python_callable=merced.run_katana_daily,
    dag=dag_merced,
    depends_on_past=True,
    wait_for_downstream=False)

m2 = PythonOperator(
    task_id='awsm',
    provide_context=True,
    python_callable=merced.full_awsm_day,
    dag=dag_merced,
    depends_on_past=True,
    wait_for_downstream=True)

m3 = PythonOperator(
    task_id='backup',
    provide_context=True,
    python_callable=merced.backup_ops,
    dag=dag_merced,
    depends_on_past=True,
    wait_for_downstream=True)

m4 = PythonOperator(
    task_id='commit',
    provide_context=True,
    python_callable=merced.commit_backup,
    dag=dag_merced,
    depends_on_past=True,
    wait_for_downstream=True)

m5 = PythonOperator(
    task_id='geoserver',
    provide_context=True,
    python_callable=merced.do_guds,
    dag=dag_merced,
    depends_on_past=True)

m1.set_downstream(m2)
m2.set_downstream(m3)
m3.set_downstream(m4)
m4.set_downstream(m5)

###############################################################################
#                               Kaweah
###############################################################################
kas = Config(core_config, config_file, 'kaweah')
kaweah = Basin(cfg.settings, kas.basin_settings)
dag_kaweah = DAG('kaweah', catchup=True, default_args=args, schedule_interval='0 8 * * *')

ka1 = PythonOperator(
    task_id='katana',
    provide_context=True,
    python_callable=kaweah.run_katana_daily,
    dag=dag_kaweah,
    depends_on_past=True,
    wait_for_downstream=False)

ka2 = PythonOperator(
    task_id='awsm',
    provide_context=True,
    python_callable=kaweah.full_awsm_day,
    dag=dag_kaweah,
    depends_on_past=True,
    wait_for_downstream=True)

ka3 = PythonOperator(
    task_id='backup',
    provide_context=True,
    python_callable=kaweah.backup_ops,
    dag=dag_kaweah,
    depends_on_past=True,
    wait_for_downstream=True)

ka4 = PythonOperator(
    task_id='commit',
    provide_context=True,
    python_callable=kaweah.commit_backup,
    dag=dag_kaweah,
    depends_on_past=True,
    wait_for_downstream=True)

ka5 = PythonOperator(
    task_id='geoserver',
    provide_context=True,
    python_callable=kaweah.do_guds,
    dag=dag_kaweah,
    depends_on_past=True)

ka1.set_downstream(ka2)
ka2.set_downstream(ka3)
ka3.set_downstream(ka4)
ka4.set_downstream(ka5)

###############################################################################
#                               Reports
###############################################################################
dag_report = DAG('reports', catchup=False, default_args=snowav_args,
                 schedule_interval='0 13 * * *')

tuolumne_report = PythonOperator(
    task_id='tuolumne',
    provide_context=True,
    python_callable=tuolumne.snowav,
    dag=dag_report,
    depends_on_past=False,
    wait_for_downstream=False)

sanjoaquin_report = PythonOperator(
    task_id='sanjoaquin',
    provide_context=True,
    python_callable=sanjoaquin.snowav,
    dag=dag_report,
    depends_on_past=False,
    wait_for_downstream=False)

kings_report = PythonOperator(
    task_id='kings',
    provide_context=True,
    python_callable=kings.snowav,
    dag=dag_report,
    depends_on_past=False,
    wait_for_downstream=False)

lakes_report = PythonOperator(
    task_id='lakes',
    provide_context=True,
    python_callable=lakes.snowav,
    dag=dag_report,
    depends_on_past=False,
    wait_for_downstream=False)

merced_report = PythonOperator(
    task_id='merced',
    provide_context=True,
    python_callable=merced.snowav,
    dag=dag_report,
    depends_on_past=False,
    wait_for_downstream=False)

kaweah_report = PythonOperator(
    task_id='kaweah',
    provide_context=True,
    python_callable=kaweah.snowav,
    dag=dag_report,
    depends_on_past=False,
    wait_for_downstream=False)

tuolumne_report.set_downstream(sanjoaquin_report)
sanjoaquin_report.set_downstream(lakes_report)
lakes_report.set_downstream(kings_report)
kings_report.set_downstream(merced_report)
merced_report.set_downstream(kaweah_report)
