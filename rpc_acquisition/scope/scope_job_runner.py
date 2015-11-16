import sys
import time
import subprocess
import pathlib
import os.path
import signal
import json
import collections
import smtplib
import email.mime.text as mimetext

import lockfile

from .util import json_encode
from .util import base_daemon
from .util import logging
logger = logging.get_logger(__name__)

STATUS_QUEUED = 'queued'
STATUS_ERROR = 'error'
STATUS_SUSPENDED = 'suspended'

MAIL_RELAY = 'mailrelay.wustl.edu'
MAIL_SENDER = 'scope-daemon@zplab.wustl.edu'

def main(timepoint_function):
    """Example main function designed to interact with the job running daemon, which
    starts a process with the timestamp of the scheduled start time as the first
    argument, and expects stdout to contain the timestamp of the next scheduled
    run-time.

    Parameters:
        timepoint_function: function to call to do whatever the job is supposed
            to do during its invocation. Usually it will be the run_timepoint
            method of a TimepointHandler subclass. The function must return
            the number of seconds the job-runner should wait before running
            the job again. If None is returned, then the job will not be re-run.
            The scheduled starting timestamp will be passed to timepoint_function
            as a parameter.
    """
    if len(sys.argv) > 1:
        scheduled_start = float(sys.argv[1])
    else:
        scheduled_start = time.time()
    next_run_time = timepoint_function(scheduled_start)
    if next_run_time:
        print(next_run_time)

class JobRunner(base_daemon.Runner):
    def __init__(self):
        self.base_dir = pathlib.Path(scope_configuration.CONFIG_DIR)
        self.jobs = _JobList(self.base_dir / 'scope_jobs.json')
        self.current_job = _JobFile(self.base_dir / 'scope_job_current')
        self.log_dir = self.base_dir / 'scope_job_logs'
        super().__init__(name='Scope Job Manager', pidfile_path=self.base_dir / 'scope_job_runner.pid')

    # THE FOLLOWING FUNCTIONS ARE FOR COMMUNICATING WITH / STARTING A RUNNING DAEMON
    def add_job(self, exec_file, alert_emails, next_run_time='now'):
        """Add a job to the queue.

        Parameters:
            exec_file: path to python file to run. The requested run-time is passed
                to the exec_file as the first argument as a time.time() timestamp.
                (The requested run-time might not be the actual time the file is run
                if a previous job takes over-long.) The standard output from running
                this file, if present, will be interpreted as the timestamp to run
                the job again.
            alert_emails: one email address as a string, list/tuple of multiple emails, or None.
                If not None, then these email addresses will be alerted if the job fails.
            next_run_time: either a time.time() style timestamp, or 'now'.
            """
        self.jobs.add(exec_file, alert_emails, next_run_time, STATUS_QUEUED)
        if self.is_running():
            self._awaken_daemon()

    def remove_job(self, exec_file):
        """Remove the job specified by the given exec_file.

        Note: this will NOT terminate a currenlty-running job."""
        exec_file = canonical_path(exec_file)
        self.jobs.remove(exec_file)
        print('Job {} has been removed from the queue for future execution.'.format(exec_file))
        if self.current_job.get() == exec_file:
            print('This job is currently running. This run has NOT been terminated.')
        if self.is_running():
            self._awaken_daemon()

    def suspend_job(self, exec_file):
        """Suspend further execution of the job specified by the given exec_file.

        Note: If the job is currently running, it will complete but further runs
        will not be executed."""
        exec_file = canonical_path(exec_file)
        self.jobs.update(exec_file, status=STATUS_SUSPENDED)
        print('Job {} has been suspended and will not be executed in the future unless resumed.'.format(exec_file))
        if self.current_job.get() == exec_file:
            print('This job is currently running. This run has NOT been terminated.')
        if self.is_running():
            self._awaken_daemon()

    def resume_job(self, exec_file, next_run_time=None):
        """Resume a job that was suspended manually or for reasons of error.

        If next_run_time is not None, it will be used as the new next_run_time,
        otherwise the previous run-time will be used. 'now' can be used to
        run the job immediately."""
        if next_run_time is None:
            # don't specify next_run_time to use the old value
            self.jobs.update(exec_file, status=STATUS_QUEUED)
        else:
            self.jobs.update(exec_file, status=STATUS_QUEUED, next_run_time=next_run_time)
        print('Job {} has been placed in the active job queue.'.format(exec_file))
        if self.is_running():
            self._awaken_daemon()
        else:
            print('NOTE: The job-runner is NOT CURRENTLY RUNNING. Until it is started again, queued jobs WILL NOT BE RUN.')


    def suspend_all(self):
        """Suspend further execution of all queued jobs."""
        self._change_all_status(STATUS_QUEUED, STATUS_SUSPENDED)
        print('All jobs have been suspended and will not be executed in the future unless resumed.')
        exec_file = self.current_job.get()
        if exec_file:
            print('Job {} is currently running. This run has NOT been terminated.'.format(exec_file))


    def resume_all(self):
        """Resume all suspended jobs.

        Note that only jobs with 'suspended' status will be resumed. Thus jobs
        that are not running due to errors and are marked with 'error' status
        will not be resumed except by specifically calling resume_job()."""
        self._change_all_status(STATUS_SUSPENDED, STATUS_QUEUED)
        if not self.is_running():
            print('NOTE: The job-runner is NOT CURRENTLY RUNNING. Until it is started again, queued jobs WILL NOT BE RUN.')


    def _change_all_status(self, status_from, status_to):
        """Change all jobs with status_from to have status_to instead."""
        jobs = self.jobs.get_jobs()
        for job in jobs:
            if job.status == status_from:
                self.jobs.update(job.exec_file, status=status_to)
        if self.is_running():
            self._awaken_daemon()

    def status(self):
        """Print a status message listing the running and queued jobs, if any."""
        is_running = self.is_running()
        if is_running:
            print('Job-runner daemon is running (PID {}).'.format(self.get_pid()))
            current_job = self.current_job.get()
        else:
            print('Job-runner daemon is NOT running.')
            # In the unlikely event that the current_job file didn't get cleared before the daemon exited
            # we should just ignore any stale entries in current_job.
            current_job = None
        if current_job:
            print('Running job {}.'.format(current_job))
        jobs = self.jobs.get_jobs()
        upcoming_jobs = []
        non_queued_jobs = []
        for job in jobs:
            if job.exec_file == current_job:
                continue
            if job.status == STATUS_QUEUED and job.next_run_time is not None:
                upcoming_jobs.append(job)
            else:
                non_queued_jobs.append(job)
        now = time.time()
        if current_job and not upcoming_jobs:
            print('No other queued jobs.')
        elif not upcoming_jobs:
            print('No queued jobs.')
        else:
            print('Queued jobs:')
            if not is_running:
                print('NOTE: As the job-runner is NOT CURRENTLY RUNNING, queued jobs WILL NOT BE RUN until the runner is started.')
            for job in upcoming_jobs:
                blurb = self._format_job_blurb(now, job)
                print('{}: {} (status: {})'.format(blurb, job.exec_file, job.status))
        if non_queued_jobs:
            print('Jobs not queued:')
            for job in non_queued_jobs:
                blurb = self._format_job_blurb(now, job)
                print('{}: {} (status: {})'.format(blurb, job.exec_file, job.status))

    def _format_job_blurb(self, now, job):
        if job.next_run_time is None:
             return 'no additional runs scheduled'
        interval = (job.next_run_time - now)
        past = interval < 0
        if past:
            interval = -interval
        hours = int(interval // 60**2)
        minutes = int(interval % 60**2 // 60)
        seconds = int(interval % 60)
        timediff = ''
        if hours:
            timediff += str(hours) + 'h '
        if hours or minutes:
            timediff += str(minutes) + 'm '
        timediff += str(seconds) + 's'
        if past:
            return 'scheduled for {} ago'.format(timediff)
        else:
            return 'scheduled in {}'.format(timediff)

    def start(self, verbose):
        super().start(self.log_dir, verbose, SIGINT=self.sigint_handler, SIGHUP=self.sighup_handler)

    def stop(self):
        """Gracefully terminate job daemon.

        Note: If a job is currently running, it will complete."""
        self.assert_daemon()
        self.signal(signal.SIGINT)
        current_job = self.current_job.get()
        if current_job:
            print('Waiting for job {} to complete.'.format(current_job))
        self.current_job.wait()

    def _awaken_daemon(self):
        """Wake the daemon up if it is sleeping, so that it will reread the
        job file."""
        self.signal(signal.SIGHUP)

    # FOLLOWING FUNCTIONS ARE FOR USE WHEN DAEMONIZED

    def sigint_handler(self, signal_number, stack_frame):
        """Stop running, but allow existing jobs to finish. If received twice,
        forcibly terminate."""
        logger.info('Caught SIGINT')
        if self.running:
            logger.info('Attempting to terminate gracefully.')
            self.running = False
            if self.asleep:
                raise InterruptedError()
        else: # not running: we already tried to end this
            logger.warning('Forcibly terminating.')
            raise SystemExit()

    def sighup_handler(self, signal_number, stack_frame):
        """If sleeping, break out of sleep."""
        logger.debug('Caught SIGHUP')
        if self.asleep:
            raise InterruptedError()

    def initialize_daemon(self):
        self.jobs.update_job_lock()
        self.current_job.clear()

    def run_daemon(self):
        """Main loop: get a job to run and run it, or sleep until the next run
        time (or forever) otherwise."""
        self.asleep = False
        self.running = True
        while self.running:
            job = self._get_next_job() # may be None
            if job and job.next_run_time > time.time():
                # not ready to run job yet
                sleep_time = job.next_run_time - time.time()
                job = None
            else:
                sleep_time = 60*60*24 # sleep for a day
            if job:
                # Run a job if there was one
                self.current_job.set(job)
                try:
                    self._run_job(job)
                finally:
                    self.current_job.clear()
            else:
                # if we're out of jobs, sleep for a while
                self.asleep = True
                logger.debug('Sleeping for {}s', sleep_time)
                try:
                    time.sleep(sleep_time)
                except InterruptedError:
                    logger.debug('Awoken by HUP')
                self.asleep = False

    def _run_job(self, job):
        """Actually run a given job and interpret the output"""
        logger.info('Running job {}', job.exec_file)
        args = [sys.executable, str(job.exec_file), str(job.next_run_time)]
        logger.debug('Parameters: {}', args)
        start_time = time.time()
        sub = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        stdout_data, stderr_data = sub.communicate()
        elapsed_time = time.time() - start_time
        logger.info('Job done (elapsed time: {:.0f} min)', elapsed_time/60)
        logger.debug('Stdout {}', stdout_data)
        logger.debug('Stderr {}', stderr_data)
        logger.debug('Retcode {}', sub.returncode)
        if sub.returncode != 0:
            self._job_broke(job, 'Calling: {}\nReturn code: {}\nStandard Error output:\n{}'.format(' '.join(args), sub.returncode, stderr_data))
            return
        if stdout_data:
            try:
                next_run_time = float(stdout_data)
            except Exception as e:
                self._job_broke(job, 'Could not parse next run time from job response "{}": {}'.format(next_run_time, e))
                return
        else:
            next_run_time = None
        try:
            self.jobs.update(job.exec_file, next_run_time=next_run_time)
        except ValueError:
            logger.info('Could not update job {}: perhaps it was removed while running?', job.exec_file)

        log_run_time = 'in {:.0f} seconds'.format(next_run_time - time.time()) if next_run_time else 'never'
        logger.info('Next run time: {}', log_run_time)

    def _get_next_job(self):
        """Get the job that should be run next."""
        for job in self.jobs.get_jobs():
            if job.status == STATUS_QUEUED and job.next_run_time is not None:
                return job

    def _job_broke(self, job, error_text, new_status=STATUS_ERROR):
        """Alert the world that the job errored out."""
        self.jobs.update(job.exec_file, status=new_status)
        logger.error('Could not run acquisition job in {}:\n {}\n', job.exec_file, error_text)
        if job.alert_emails:
            message = mimetext.MIMEText(error_text)
            message['From'] = MAIL_SENDER
            message['To'] = ', '.join(job.alert_emails)
            message['Subject'] = '[zplab-scope] Job {} failed.'.format(job.exec_file)
            try:
                with smtplib.SMTP(MAIL_RELAY) as s:
                    s.sendmail(MAIL_SENDER, job.alert_emails, message.as_string())
            except:
                logger.error('Could not send alert email.', exc_info=True)


_Job = collections.namedtuple('Job', ('exec_file', 'alert_emails', 'next_run_time', 'status'))

def _validate_alert_emails(alert_emails):
    if alert_emails is None:
        return alert_emails
    if isinstance(alert_emails, str):
        alert_emails = (alert_emails,)
    for email in alert_emails:
        if not isinstance(email, str):
            raise ValueError('Email address {} must be a string.'.format(email))
    return alert_emails

def canonical_path(path):
    return pathlib.Path(os.path.realpath(str(path)))

class RLockFile(lockfile.LockFile):
    def __init__(self, path, timeout=None):
        super().__init__(path, threaded=False, timeout=timeout)
        self.acquisitions = 0

    def acquire(self, timeout=None):
        if not self.acquisitions:
            super().acquire(timeout)
        self.acquisitions += 1

    def release(self):
        if self.acquisitions: # if it's already zero, don't decrement, but allow the release() below, which will error out in the usual way
            self.acquisitions -= 1
        if not self.acquisitions:
            super().release()

class _JobList:
    """Manage a list of jobs that is always stored as a file on disk. No in-memory
    mutation is allowed, so this job list is effectively stateless."""
    def __init__(self, backingfile_path):
        self.backing_file = canonical_path(backingfile_path)
        self.update_job_lock()
        if not self.backing_file.exists():
            self._write({})

    def update_job_lock(self):
        """Re-create a new job-lock. Necessary after daemonization because the lockfile
        workes based on process PID, which changes after daemonization. So make a new
        lock object that knows about the new PID."""
        self.jobs_lock = RLockFile(str(self.backing_file))

    def _read(self):
        """Return dict mapping exec_file to full Job tuples, read from self.backing_file."""
        with self.jobs_lock, self.backing_file.open('r') as bf:
            job_list = json.load(bf)
        job_dict = {}
        for exec_file, *rest in job_list:
            exec_file = pathlib.Path(exec_file)
            job_dict[exec_file] = _Job(exec_file, *rest)
        return job_dict

    def _write(self, jobs):
        """Write Job tuples as json to self.backing_file."""
        job_list = [[str(exec_file)] + rest for exec_file, *rest in jobs.values()]
        with self.jobs_lock, self.backing_file.open('w') as bf:
            json_encode.encode_legible_to_file(job_list, bf)

    def remove(self, exec_file):
        """Remove the job specified by exec_file from the list."""
        with self.jobs_lock: # lock is reentrant so it's OK to lock it here and in the _read/_write calls
            exec_file = canonical_path(exec_file)
            jobs = self._read()
            if exec_file in jobs:
                del jobs[exec_file]
                self._write(jobs)
            else:
                raise ValueError('No job queued for {}'.format(exec_file))

    def add(self, exec_file, alert_emails, next_run_time, status):
        """Add a new job to the list.

        Parameters:
            exec_file: required path to existing file
            alert_emails: None, tuple-of-strings, or single string
            next_run_time: timestamp float, 'now' or None
            status: current job status

        """
        exec_file = canonical_path(exec_file)
        if not exec_file.exists():
            raise ValueError('Executable file {} does not exist.'.format(exec_file))
        alert_emails = _validate_alert_emails(alert_emails)
        if next_run_time is 'now':
            next_run_time = time.time()
        elif next_run_time is not None:
            next_run_time = float(next_run_time)

        with self.jobs_lock:
            jobs = self._read()
            jobs[exec_file] = _Job(exec_file, alert_emails, next_run_time, status)
            self._write(jobs)

    def update(self, exec_file, **kws):
        """Update the values of an existing job. Any parameter not in keyword args
        will be copied from the old job."""
        with self.jobs_lock:
            old_job = self._get_job(exec_file)
            for field in _Job._fields[1:]: # all fields but exec_file
                if field not in kws:
                    kws[field] = getattr(old_job, field)
            self.add(exec_file, **kws)

    def get_jobs(self):
        """Return a list of Job objects, sorted by their next_run_time attribute.

        Note: if next_run_time is None, the job will appear at the end of the list."""
        jobs = self._read()
        return sorted(jobs.values(), key=lambda job: job.next_run_time if job.next_run_time is not None else float('inf'))

    def _get_job(self, exec_file):
        """Get the Job specified by exec_file"""
        exec_file = canonical_path(exec_file)
        jobs = self._read()
        if exec_file in jobs:
            return jobs[exec_file]
        else:
            raise ValueError('No job queued for {}'.format(exec_file))

class _JobFile:
    def __init__(self, jobfile_path):
        self.job_file = canonical_path(jobfile_path)

    def get(self):
        """Return the contents of the job_file if it exists, else None."""
        if self.job_file.exists():
            with self.job_file.open('r') as f:
                return canonical_path(f.read())

    def set(self, job):
        """Write the given string to the jobfile."""
        with self.job_file.open('w') as f:
            f.write(str(job.exec_file))

    def clear(self):
        """Remove the jobfile if it exists."""
        if self.job_file.exists():
            self.job_file.unlink()

    def wait(self):
        """Wait until the jobfile has been cleared."""
        while self.job_file.exists():
            time.sleep(1)
