
from inicheck.tools import get_user_config, check_config, cast_all_variables
from inicheck.output import generate_config, print_config_report
from inicheck.config import MasterConfig
from datetime import timedelta

class Config(object):
    """
    Read in docker-airflow config and apply inicheck. As of wy2020, the
    docker-airflow config and CoreConfig are in /home/ops/wy2020.
    """

    def __init__(self, core_config, config_file, basin=None):
        """Read in docker-airflow config. """

        mcfg = MasterConfig(path = core_config)
        ucfg = get_user_config(config_file, mcfg=mcfg)
        ucfg.apply_recipes()
        ucfg = cast_all_variables(ucfg, ucfg.mcfg)

        warnings, errors = check_config(ucfg)
        if errors != [] or warnings != []:
            print_config_report(warnings, errors)

        # from basin_arguments section
        self.args = {
            "owner": ucfg.cfg['basin_arguments']['owner'],
            "depends_on_past": ucfg.cfg['basin_arguments']['depends_on_past'],
            "start_date": ucfg.cfg['basin_arguments']['start_date'],
            "email": ucfg.cfg['basin_arguments']['email'],
            "email_on_failure": ucfg.cfg['basin_arguments']['email_on_failure'],
            "email_on_retry": ucfg.cfg['basin_arguments']['email_on_retry'],
            "retries": ucfg.cfg['basin_arguments']['retries'],
            "retry_delay": timedelta(hours=ucfg.cfg['basin_arguments']['retry_delay'])
        }

        self.snowav_args = {
            "owner": ucfg.cfg['snowav_arguments']['owner'],
            "depends_on_past": ucfg.cfg['snowav_arguments']['depends_on_past'],
            "start_date": ucfg.cfg['snowav_arguments']['start_date'],
            "email": ucfg.cfg['snowav_arguments']['email'],
            "email_on_failure": ucfg.cfg['snowav_arguments']['email_on_failure'],
            "email_on_retry": ucfg.cfg['snowav_arguments']['email_on_retry'],
            "retries": ucfg.cfg['snowav_arguments']['retries'],
            "retry_delay": timedelta(hours=ucfg.cfg['snowav_arguments']['retry_delay'])
        }

        # settings
        aimage = ucfg.cfg['settings']['awsm_image']
        atag = ucfg.cfg['settings']['awsm_tag']
        kimage = ucfg.cfg['settings']['katana_image']
        ktag = ucfg.cfg['settings']['katana_tag']

        self.settings = {
            "awsm_image": aimage + ':' + atag,
            "katana_image": kimage + ':' + ktag,
            "forecast_path": ucfg.cfg['settings']['forecast_path'],
            "geojson": ucfg.cfg['settings']['geojson'],
            "docker_call_backup": ucfg.cfg['settings']['docker_call_backup'],
            "windninja_nthreads": ucfg.cfg['settings']['windninja_nthreads'],
            "katana_zone_letter": ucfg.cfg['settings']['katana_zone_letter'],
            "katana_zone_number": ucfg.cfg['settings']['katana_zone_number'],
            "wy": ucfg.cfg['settings']['wy'],
            "backup_path": ucfg.cfg['settings']['backup_path']
            }

        # basin sections
        if basin is not None:
            self.basin_settings = {
                "basin": ucfg.cfg[basin]['basin'],
                "base_path": ucfg.cfg[basin]['base_path'],
                "awsm_config": ucfg.cfg[basin]['awsm_config'],
                "snowav_config": ucfg.cfg[basin]['snowav_config'],
                "katana_pixel": ucfg.cfg[basin]['katana_pixel'],
                "awsm_path": ucfg.cfg[basin]['awsm_path'],
                "topo_file": ucfg.cfg[basin]['topo_file'],
                "results_path": ucfg.cfg[basin]['results_path']
                }
