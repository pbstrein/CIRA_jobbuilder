import argparse
import sys
from os.path import isdir

import jb_functions

# run argparse commands
parser = argparse.ArgumentParser()

parser.add_argument('-fc', '--filesconfig',
                    help='Location of the files database config file')
parser.add_argument('-jc', '--jobsconfig',
                    help='Location of the jobs database config file')
parser.add_argument('-j', '--jobname',
                    help='The name of the job that will be run')
parser.add_argument('-tl', '--templatelocation',
                    help='Location of the template folder')
parser.add_argument('-v', '--verbosity', action='count',
                    help=('Controls how much information outputs to the '
                          'console while running the program'))

args = parser.parse_args()

# default values
job_name = ''  # will be set by -j, if not, then the program will not run
# files_config_loc = 'filesdbconfig.json'
files_config_loc = 'Config/filesdbconfig.json'
jobs_config_loc = 'Config/jobsdbconfig.json'
template_location = 'templates/'
verbosity = 0

# no command line arguements, runs default values
if (not len(sys.argv) > 1) | (not args.jobname):
    print("Cannot run program --- need to specifiy a template")
    print("Use -j to specify which job template to use")
    sys.exit()

if args.filesconfig:  # -fc
    files_config_loc = args.filesconfig
if args.jobsconfig:  # -jc
    jobs_config_loc = args.jobsconfig

if(args.jobname):  # -j
    job_name = args.jobname

if args.templatelocation:  # -tl
    if not isdir(args.templatelocation):
        raise FileNotFoundError(args.templatelocation + " was not found")
    else:
        template_location = args.templatelocation

if args.verbosity:  # -v; sets verbosity, if any
    verbosity = args.verbosity

# prints program specificatoins of level 1
if verbosity >= 1:
    print()
    print("\tProgram Specifications:")
    print("\tFiles Config location:", files_config_loc)
    print("\tJobs Database config location:", jobs_config_loc)
    print("\tJobname:", job_name)
    print("\tTemplate files location:", template_location)

    print()
# runs main function with values given - values changed based on defaluts
# and/or if they were any commandline arguments
jb_functions.main(files_config_loc, jobs_config_loc, job_name,
                 template_location, verbosity)
