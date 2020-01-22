
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import os
from subprocess import Popen, PIPE
import pytz
import copy
import shutil
import netCDF4 as nc
from airflow import AirflowException

class Basin():
    """
    Class for storing important basin attributes and methods for running
    AWSM and Katana on a daily basis using docker images. It is IMPORTANT to
    remember that the methods that will be called using PythonOperators should
    only take **kwargs as arguments as Airflow specifies what gets passed in
    and we don't really have say in what that is. That is why most of these
    functions using the already specified instance variables and the
    execution_date that Airflow assigns.
    """

    fmt = '%Y%m%d-%H-%M'
    fmt_dir = '%Y%m%d'

    def __init__(self, settings, basin_settings):

        """
        Important: this only modifies the times date dependant folders to
        account for running AWSM on a daily basis. The paths within the config
        need to be docker paths relative to the mounted docker directries

        Args
        ------
        settings : dict, see awsm.py
        basin_settings : dict, see awsm.py
        """

        # Settings for all basins
        self.nthreads = settings['windninja_nthreads']
        self.zone_letter = settings['katana_zone_letter']
        self.zone_number = settings['katana_zone_number']
        self.katana_image = settings['katana_image']
        self.awsm_image = settings['awsm_image']
        self.forecast_path = os.path.abspath(settings['forecast_path'])
        self.backup_path = os.path.abspath(settings['backup_path'])
        self.docker_call_backup = settings['docker_call_backup']
        self.geojson = settings['geojson']
        self.wy = settings['wy']
        # self.uid = int(os.getuid())
        self.uid = 1009
        self.gid = 4

        # Basin specific
        self.basin = basin_settings['basin']
        self.katana_pixel = basin_settings['katana_pixel']
        self.awsm_path = os.path.abspath(basin_settings['awsm_path'])
        self.awsm_config = os.path.abspath(basin_settings['awsm_config'])
        self.snowav_config = os.path.abspath(basin_settings['snowav_config'])
        self.topo_file = os.path.abspath(basin_settings['topo_file'])
        self.base_path = os.path.abspath(basin_settings['base_path'])
        self.results_path = os.path.abspath(basin_settings['results_path'])

        # Snow server paths
        self.topo_filename = os.path.split(self.topo_file)[1]
        self.topo_path = os.path.split(self.topo_file)[0]

        # Build docker paths and calls
        self.output_path_docker = '/data/output'
        self.topo_path_docker = '/data/topo'
        self.topo_file_docker = os.path.join('/data/topo', self.topo_filename)
        self.config_path_docker = '/data/config'
        self.docker_snowav_data = '/data/snowav'
        self.docker_path_input = '/data/input'
        self.cfg_name = os.path.basename(self.awsm_config)
        self.docker_cfg = os.path.join(self.config_path_docker, self.cfg_name)
        self.credentials_path = '/root/home_ops_token.json'

        # develop string for mounting directories into the docker
        self.awsm_path_data = os.path.join(self.awsm_path,'data')
        self.docker_path_data = '/data/output/{}/ops/wy{}/ops/data'.format(
            self.basin, str(self.wy))

        self.docker_path_run_data = '/data/output/{}/ops/wy{}/ops/runs/'.format(
            self.basin, str(self.wy))

        self.base_mount_call = ' -v {}:{} -v {}:{}  '.format(self.topo_path,
                                                             self.topo_path_docker,
                                                             self.forecast_path,
                                                             self.docker_path_input)

        self.snowav_mount_call = ' -v {}:{} -v /home/ops/wy2020:/home/ops/wy2020'.format(self.results_path,
                                                    self.docker_snowav_data)

        # add extra mounts for Katana
        self.wn_mount_call = self.base_mount_call + ' -v {}:{} '.format(self.awsm_path_data,
                                                                        '/data/output')

        # add extra mounts for AWSM
        self.mount_call = self.base_mount_call + ' -v {}:{} -v {}:{} '.format(self.base_path,
                                              self.output_path_docker,
                                              os.path.dirname(self.awsm_config),
                                              self.config_path_docker)
        # paths for the daily backup
        self.backup_location = os.path.join(self.backup_path, self.basin)
        self.backup_config = os.path.join(self.backup_location, 'awsm_config_backup.ini')
        self.backup_stat = os.path.join(self.backup_location, 'snow_latest.nc')

        # do we need to backup docker calls to text file?
        if self.docker_call_backup:
            self.backup_docker_calls = os.path.join(self.backup_location, 'docker_calls.txt')


    def __enter__(self):
        return self

    def __exit__(self):
        print('Done with full awsm docker {}'.format(datetime.now()))

    def get_start_date(self, kwargs):
        """
        Get 'start_date' pandas datetime argument for launching Katana and AWSM.
        We use the kwargs['execution_date'] that airflow specifies for the day
        it will be running
        Returns:
            start_date:     datetime for start_date
        """
        ex_date = pd.to_datetime(kwargs['execution_date'])
        midnight_date = pd.to_datetime(datetime.date(ex_date))
        start_date = midnight_date

        return start_date

    def run_katana_daily(self, **kwargs):
        """
        Assemble Katana docker call to run WindNinja for one day.
        Args:
            **kwargs:       We use the execution_date in kwargs
        Returns:
            boolean:        Whether or not the run was succesful
        """

        success = False

        # inputs
        buff = 6000
        start_date = self.get_start_date(kwargs)
        end_date = start_date + pd.to_timedelta(24, unit='h')
        wn_cfg = os.path.join(self.output_path_docker, 'windninjarun.cfg')
        nthreads = self.nthreads
        nthreads_w = 1
        dxy = self.katana_pixel

        # smrf params
        fp_dem = self.topo_file_docker
        zone_letter = self.zone_letter
        zone_number = self.zone_number

        # logging
        logfile = os.path.join(self.output_path_docker,
            'log_test_{}.txt'.format(start_date.strftime(self.fmt)))
        loglevel = 'info'

        # did we already make the new gribs?
        have_gribs = False

        # make entrypoint take in the run_katana call
        action = ' docker run --rm '

        action += self.wn_mount_call

        action += ' --user {}:{}'.format(self.uid, self.gid)

        # docker entrypoint feeds run_katana here
        action += ' {} --start_date {} --end_date {}'
        action = action.format(self.katana_image,
                               start_date.strftime(self.fmt),
                               end_date.strftime(self.fmt))

        action += ' --input_directory {} --output_directory {}'.format(self.docker_path_input,self.output_path_docker)
        action += ' --wn_cfg {}'.format(wn_cfg)
        action += ' --topo {} --zn_number {} --zn_letter {}'.format(self.topo_file_docker, zone_number, zone_letter)
        action += ' --buff {} --nthreads {} --nthreads_w {} --dxy {}'.format(buff, nthreads, nthreads_w, dxy)
        action += ' --loglevel {} --logfile {}'.format(loglevel, logfile)

        if have_gribs:
            action += ' --have_gribs'

         # update latest docker calls
        self.katana_docker_call = action

        print('Running: {}'.format(action))

        result = check_popen(action, 'Katana')

        if self.docker_call_backup:
            with open(self.backup_docker_calls, 'w') as f:
                f.write('Latest docker calls\n')
                f.write(self.katana_docker_call)

        success = True

        if not success:
            raise AirflowException('run_katana_daily failed')

        return success

    def full_awsm_day(self, **kwargs):
        """
        Assemble AWSM docker call for one day and run it.
        Args:
            **kwargs:       We use the execution_date in kwargs
        Returns:
            boolean:        Whether or not the run was succesful
        """

        success = True
        start_date = self.get_start_date(kwargs)

        # docker commands here
        action = ' docker run --rm '

        action += self.mount_call

        action += ' --user {}:{}'.format(self.uid, self.gid)
        action += ' {} awsm_daily_airflow '.format(self.awsm_image)
        action += ' --cfg {} --start_date {} '
        action = action.format(self.docker_cfg, start_date.strftime(self.fmt))

        # if we have nowhere to initialize from
        if start_date == pd.to_datetime('{}-10-01'.format(self.wy-1)):
            action += ' --no_previous'

        # update latest docker calls
        self.awsm_docker_call = action

        print('Running: {}'.format(action))
        result = check_popen(action, 'AWSM')
        print('From check_popen call: {}'.format(result))

        if 'Traceback' in str(result[1]):
            success = False

        if not success:
            raise AirflowException('run_awsm_daily failed')

        # Check for empty snow.nc and em.nc files that happen for certain
        # awsm<=0.10 crashes, in lieu of a fix in awsm
        start_date = self.get_start_date(kwargs)
        awsm_path_data = os.path.dirname(self.awsm_path_data)
        snow_file = os.path.join(awsm_path_data,
                'runs/run{}/snow.nc'.format(start_date.strftime(self.fmt_dir)))

        if not os.path.isfile(snow_file):
            raise AirflowException('Output awsm file {} does not '
                'exist'.format(snow_file))

        ncf = nc.Dataset(snow_file)

        if 'specific_mass' not in ncf.variables:
            ncf.close()
            success = False
            raise AirflowException("No 'specific_mass' variable in {}, awsm "
                "may have crashed and left empty snow.nc and em.nc "
                "files. These files must be deleted before awsm can be "
                "successfully re-run.".format(snow_file))

        ncf.close()

        if self.docker_call_backup:
            with open(self.backup_docker_calls, 'a') as f:
                f.write('\n')
                f.write(self.awsm_docker_call)

        return success

    def backup_ops(self, **kwargs):
        """
        /home/ops/backups
        Function to stay up to date on back up of config and model state for
        the running of Katana and AWSM for each basin.
        For each basin copy:
         - latest config file
         - latest model state
        """

        success = True

        start_date = self.get_start_date(kwargs)

        state = os.path.join(self.awsm_path,
            'runs/run{}/snow.nc'.format(start_date.strftime(self.fmt_dir)))

        config = os.path.join(self.awsm_path,
            'data/data{}/awsm_config_backup.ini'.format(start_date.strftime(self.fmt_dir)))

        if os.path.isfile(state):
            shutil.copyfile(state,
                '/data/backups/{}/latest_snow.nc'.format(self.basin))
        else:
            print(' {} not a valid file...'.format(state))
            print(' This may mean that katana and/or awsm did not successfully '
                'complete...')
            raise AirflowException('{} not a valid file'.format(state))
            success = False

        if os.path.isfile(config):
            shutil.copyfile(config,
                '/data/backups/{}/awsm_config_backup.ini'.format(self.basin))
        else:
            print(' {} not a valid file...'.format(config))
            print(' This may mean that katana and/or awsm did not successfully '
                'complete...')
            raise AirflowException('{} not a valid file'.format(config))
            success = False

        return success


    def commit_backup(self, **kwargs):
        """
        Commit all of the changes to the backup config files and the backup
        docker calls after we have run all of the basins each day.
        """

        success = True
        fmtgit = '%Y-%m-%d'
        fp_track = ['awsm_config_backup.ini', 'docker_calls.txt']
        start_date = self.get_start_date(kwargs)
        compare_date = start_date + pd.to_timedelta(1, 'd')
        today = datetime.now()

        # only commit if we're caught up
        # if compare_date.date() == today.date():

        cwd = os.getcwd()
        git_dir = os.path.abspath('/data/backups/{}'.format(self.basin))
        os.chdir(git_dir)

        call = 'eval "$(ssh-agent -s)"'
        result = call_git_functions(call)

        # run the calls
        action = 'git status'
        result = call_git_functions(action)

        # if there are changes
        need_commit = False
        if 'Changes not staged for commit' in result:
            for fp in fp_track:
                print('attempting ', fp)
                if fp in result:
                    need_commit = True
                    action2 = 'git add {}'.format(fp)
                    result2 = call_git_functions(action2)

            # if we added any files
            if need_commit:
                action3 = 'git commit -m "Updating backups for {}"'.format(start_date.date().strftime(fmtgit))
                result3 = call_git_functions(action3)

            # Moving this to try every time
            action4 = 'git push origin master'
            result4 = call_git_functions(action4, checkerr=False)
            print('Git stream complete')

        # move back
        os.chdir(cwd)

        return success


    def snowav(self, **kwargs):
        '''
        Function to make snowav call to process results.

        Error handling is weak, just parsing terminal output for 'traceback'

        '''

        success = True

        # get the start date
        start_date = self.get_start_date(kwargs)
        end_date = start_date + pd.to_timedelta(23, unit='h')
        end_date = end_date.strftime("%Y-%-m-%-d %H:%M")

        # snowav data location
        action = ' docker run --rm '
        action += self.snowav_mount_call
        action += self.mount_call
        action += ' --user {}:{}'.format(self.uid, self.gid)
        action += ' {} snowav -f {} -end_date "{}"'.format(self.awsm_image,
            self.snowav_config, end_date)

        print('Running: {}'.format(action))
        result = check_popen(action, 'SNOWAV')

        if 'Traceback' in str(result[1]):
            print(str(result[1]))
            success = False

        if not success:
            print('From check_popen call: {}'.format(result))
            raise AirflowException('snowav failed')

    def do_guds(self, **kwargs):
        """
        Upload netcdf results to geoserver using the guds python command
        line tool.
        """

        if self.geojson is None:
            raise ValueError('geojson credential file not given')

        start_date = self.get_start_date(kwargs)

        awsm_path_data = os.path.dirname(self.awsm_path_data)
        latest_output = os.path.join(awsm_path_data,
                'runs/run{}/snow.nc'.format(start_date.strftime(self.fmt_dir)))

        latest_output = os.path.abspath(latest_output)

        topo_file = os.path.join(self.topo_path, self.topo_filename)

        # formulate command
        cmd_base = "guds -f {} -t modeled -b {} -m {} -y -c {} --latest -e 32611"
        print("calling: ", cmd_base)
        cmd = cmd_base.format(latest_output, self.basin, topo_file,
                         self.geojson)

        # run cmd
        print('Running: {}'.format(cmd))
        s = Popen(cmd, shell=True)
        s.wait()

        return True

    def pass_true():
        return True


def call_git_functions(action, checkerr=True):
    """
    Use Popen to call git from the command line
    """
    s = Popen(action, shell=True,stdout=PIPE, stderr=PIPE)
    s.wait()
    stdout, stderr = s.communicate()

    if len(stderr) > 0:
        print('Error reported in git call {}\n\n'.format(action))
        print(stderr, '\n\n')
        if checkerr:
            raise Exception('git call failed')

    return stdout.decode()


def check_popen(cmd, function_name):
    """
    Use popen to run a command line call and see if it was succesful.
    This is not fully succesful, as in it does not catch every error.
    """

    s = Popen(cmd,shell=True, stdout=PIPE, stderr=PIPE)

    return s.communicate()

    # while True:
    #
    #     line = s.stdout.readline()
    #     eline = s.stderr.readline()
    #     if not line:
    #         break
    #
    #     print(line.decode())
    #
    #     if len(eline) > 0:
    #         print('Issue in {}'.format(function_name))
    #         this_err = eline.decode().lower()
    #         print(this_err)
    #         # exit with a failure if this is not a warning
    #         if 'error' in this_err:
    #             raise Exception(this_err)
    #         if 'traceback' in this_err and 'warning' not in this_err:
    #             raise Exception(this_err)
