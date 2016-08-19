# Python Jobbuilder

### Summary
The Jobbuilder functionally does the same thing as Phil’s PHP job builder, but in Python. It reads in an INI formatted file, finds the xml code, finds the input_file wildcards from the xml code, and finds all of the input files based on the wildcard. If all the input files exist, and there is not existing job or existing end file, then a job is created to a jobs table in a database, containing all the information needed to then create the specific file through the algorithm in the INI file.

### Program Requirements
To run, this program needs 4 things -
  1. A json file that contains the config information to connect to the database that has all the cloudsat data
    - **Note**: By default the program searches for the file at `config/filesdbconfig.json`, to change that, use `-fc [file_loc]` in the command line
  2. A json file that contains the config information to connect to the jobs database, where the jobs will be outputed.
    - by default it finds the file at `config/jobsdbconfig.json`, to change the location, use `-jc [file_loc]` in the command line
along
  3. An INI file that contains 
    - `write_file` command which has inside of it `contents` which is the xml file holding all the wildcards for the job
    - **IMPORTANT** - for this job builder to work, contents must only have one = sign, all the xml portion of the INI file must have at least one tab, and there cannot be any double equal signs after the xml portion of the file
  3. In the command line, `python3 jobbuilder.py -j [job_name]
    - You cannot use jb_functions, it will not work, only jobbuilder.py
    - `-j [job_name]`is the name of the job with the R04 and epic
    - *Important* - you cannot run job builder in python 2.7, only python 3

#### Example
`python3 jobbuilder.py -j 2BGEO.R04.E06` 
Using python3, will create all the possible jobs based on the template file `production_sys_2BGEO.RO$.E06`
  - **Important** - you CANNOT use python 2.7, it will not work
    -**i.e. - CANNOT type `python jobbuilder.py -j 2BGEO.RO4.E06`

### Output
Will create “jobs” in the job database given in the job database config file. 
Each “job” is a row in the database with these attributes:
- `output_file` - the xml file containing all the new information (not wildcard information) to create the product
- `filename` - the name of the job
- `jobinfoid` - an id that retrieves the product name from another table
- `jobfilecreated` - unix timestamp of when the file was created
- `job status` - current status of the job
- `checksum` - name of the product when the file has been created through the algorithm

### Tips and Warnings
  1. The `-j` is not just the product name, but also includes R04 and the epic - if the R04 and the epic are not included, then the program will not be able to find the template file and will fail
    - **EX** - `2BGEO.R04.E06` when the template file is `production_sys_2BGEO.R04.E06 
  2. The program runs based on the templates found in the given templates directory. If there are no templates, or if it cannot find the template based on `-j [jobname]`, then the program will not run


### Command Line Arguments
- `-h` `—-help` - access the help menu for the command line arguments
- `-fc` `—-filesconfig` -Location of the files database config file
- `-jc` `—-jobsconfig` - Location of the jobs database config file
- `-j` `—-jobname` - Name of the job that will be run
  - **Note** - the job name depends on the template file, you only need to give the job name, the R04, and epic 
    - **EX** - template name = production_sys_2BGEO.R04.E06, you only need to put `2BGEO.R04.E06` into the command line
- `-tl` `—-templatelocation` - Location of the folder where the program will search for the wildcard templates
- `-v` `—-verbosity` - Inputing will increase information in the console while running the job builder. MAX is -v.

### Default values
```
files_config_location = Config/filesdbconfig.json
jobs_config_loc = Config/jobsdbconfig.json
template_location = templates/
verbosity = 0
```
