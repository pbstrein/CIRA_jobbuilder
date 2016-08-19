
from os import path, listdir
from os.path import isfile, join
from fnmatch import fnmatch
import sys
import time
import xml.etree.ElementTree
import xml.etree.ElementTree as EleTree
import configparser
import json

import mysql.connector
from mysql.connector import errorcode


# --------------------------- Global Variables ----------------------------
verbosity = 0

# ---------------------------Jobbuilder Classes ----------------------------


class DBConnector():
    """Contains all the info to make a connection to the database, and contain
       the variables for a connection

       Attributes
       db_info - all of the login information needed to get into a database;
                 user, password host, port, and database
       cnx - myql.connecotr connection to database, set in make_connections()
       cursor - myql.cursor to make queries into the database, set in
                make_connections()
       make_connections() - sets cnx and cursor to the db_info, and  tries
                            connection to database - if it cant connect or
                            connection breaks, retries 5 times, then quits the
                            program if it does not connect
        close_connections - officially closes cnx and cursor to finish
                            connection to the database """

    def __init__(self, db_info):
        self.db_info = db_info
        self.make_connection()
        # cnx and cursor are public variables, but are set in make_connections,
        # not in __init__

    def make_connection(self):
        connection_tries = 0
        delay_time = 5  # reconnection time in seconds
        while (connection_tries < 5):
            try:
                cnx = mysql.connector.connect(**self.db_info)
                cursor = cnx.cursor()
            except mysql.connector.Error as err:
                # wrong hostname
                if err.errno == errorcode.CR_WRONG_HOST_INFO:
                    print(err)
                    # break
                # could not make initial server connection
                elif err.errno == errorcode.CR_CONN_HOST_ERROR:
                    print("Could not make initial connection. Retrying in 5",
                          "seconds...")
                # errors during the a query
                elif((err.errno == errorcode.CR_SERVER_LOST_EXTENDED) |
                     (err.errno == errorcode.CR_SERVER_LOST) |
                     (err.errno == errorcode.ER_SERVER_SHUTDOWN)):
                    print(err)
                    print("Database connection broke. Reconnecting...")
                    cursor.close()
                # errors in database access informatoin (password, name, etc.)
                elif ((err.errno == errorcode.ER_DBACCESS_DENIED_ERROR) |
                      (err.errno == errorcode.ER_ACCESS_DENIED_ERROR)):
                    print(err)
                # unknown or uncaught error
                else:
                    raise
                # wait for retry
                connection_tries += 1
                time.sleep(delay_time)
            # retrieve info from query and close query when there are no
            # connections problems
            else:
                self.cnx = cnx
                self.cursor = cursor
                break
        # failed to connect after retrying multiple times
        else:
            print("Could not reconnect at all. Exiting program")
            sys.exit()

    def close_connections(self):
        self.cursor.close()
        self.cnx.close()

# ----------------------------Jobbuilder Custom Exceptions-------------------


class NoTemplateError(Exception):
    pass


class MissingWildcardError(Exception):

    def __init__(self, file_loc):
        self.file_loc = file_loc


# -------------------------------Definations-------------------------------
def access_templates(folder_loc, wildcard_name):
    """Access all files with the given wildcard_name in a folder and returns
    a list with the files
    """
    files = []
    cnx_tries = 0
    while cnx_tries < 5:
        try:
            files = [f for f in listdir(
                folder_loc) if fnmatch(f, wildcard_name)]
        except FileNotFoundError as err:
            cnx_tries += 1
            print("Could not access", folder_loc)
            print("Retrying in 5 seconds")
            time.sleep(5)
        else:
            break
    # if template folder is empty, raise error and stops
    if not files:
        err_msg = "No template files were found in the folder '" + \
            join(folder_loc) + "'"
        raise NoTemplateError(err_msg)
    return files


def check_wildcards(wildcard_list, file_location):
    """
    Raises an error if any given files are misisng a wildcard; also returns
    number of files missing wildcards
    """
    errors = 0
    for i in range(len(wildcard_list)):
        try:
            if not (wildcard_list[i].startswith('*')):
                raise MissingWildcardError(file_location)
        except MissingWildcardError as err:
            errors += 1
    return errors


def check_wildcard_errors(input_wildcard_list,
                          output_wildcard_list,
                          file_name):
    """
    Checks if there are missing wildcards from the given input and output
    list. Returns true if are missing wildcards, returns false if given
    files are ok.
    """
    missing_cards = 0
    missing_cards += check_wildcards(input_wildcard_list, file_name)
    missing_cards += check_wildcards(output_wildcard_list, file_name)

    if (missing_cards > 0):
        print("ERROR: There are", missing_cards,
              "missing wildcards from", file_name)
        print("\t Skipping", file_name)
        return True
    else:
        return False


def import_input_wildcards(xml_element):
    """Creates and returns a  list of diffrent input wildcard names from the
       ElementTree xml element"""
    input_file_wildcards = []
    for filename_tags in xml_element.iter("input_files"):
        for f in range(len(filename_tags)):
            if(filename_tags[f].tag == 'filename'):
                str_file_name = filename_tags[f].text
                input_file_wildcards.append(str_file_name)
            elif(filename_tags[f].tag == 'file'):
                str_file_name = filename_tags[f].get('name')
                input_file_wildcards.append(str_file_name)
    return input_file_wildcards


def import_output_wildcards(xml_file_elements):
    """Creates and returns a a list of the different wildcard outputs from
     an ELementTree xml element"""
    output_file_wildcards = []
    for filename_elements in xml_file_elements.iter('file_io'):
        if (filename_elements.get('operation') == 'write'):
            for element in filename_elements.iter('filename'):
                str_file_name = element.text
                output_file_wildcards.append(str_file_name)
            for element in filename_elements.iter('file'):
                str_file_name = element.get('name')
                output_file_wildcards.append(str_file_name)
    return output_file_wildcards


def job_exists(DBConnector, table_name, checksum_name):
    """Checks if a job already exists in the job queue, returns if true"""
    search_query = ("SELECT * FROM {} "
                    "WHERE checksum={!r}") .format(table_name, checksum_name)
    searched_row = run_sql_command(DBConnector, search_query)
    if(searched_row):
        pass
    return searched_row


def end_prod_exists(DBConnector, table_name, end_prod_name):
    """Check to see if a product is already created - returns if true"""
    search_query = ("SELECT filename FROM {} "
                    "WHERE filename = {!r}") .format(table_name,
                                                     end_prod_name)

    searched_row = run_sql_command(DBConnector, search_query)
    return searched_row


def get_jobinfoid(DBConnector, jobinfo_tb_name,jobname):
    search_query = ("SELECT jobinfoid FROM {} "
                    "WHERE jobname = {!r}") .format(jobinfo_tb_name, jobname)
    searched_row = run_sql_command(DBConnector, search_query)
    return searched_row[0][0]


def create_new_xml_file(DBConnector, output_table_name, xml_string,
                        time_stamp, job_filename, jobname, checksum_name):
    """Creates new xml file from the given template based on time_stamp"""
    temp_tree = EleTree.ElementTree(EleTree.fromstring(xml_string))
    temp_root = temp_tree.getroot()
    # retrieves wildcard name, removes wildcard symbol and places timestamp
    for element in temp_root.iter('file'):
        g = element.get('name')
        g = g[1:]
        full_name = time_stamp + g
        element.attrib['name'] = full_name
    for element in temp_root.iter('filename'):
        str_name = element.text[1:]
        full_name = time_stamp + str_name
        element.text = full_name
    # names the outputed template file
    # file_name = time_stamp + '_config.xml'
    str_output = xml.etree.ElementTree.tostring(
        temp_root, encoding='unicode', method='xml')
    current_time = int(time.time())
    jobinfoid = get_jobinfoid(DBConnector, 'job_info', jobname)
    write_to_database(DBConnector, output_table_name,
                      str_output, job_filename, jobinfoid,
                      current_time, 'queue', checksum_name)
    return str_output


def run_sql_command(DBConnector, sql_command):
    """Runs the given sql command, and handles for a database disconnect. If
    cannot connect to database, returns false. If connects, executes
    command, and returns values if select, or none if another command
    """

    connection_tries = 0
    delay_time = 5  # reconnection time in seconds
    while (connection_tries < 5):
        try:
            DBConnector.cursor.execute(sql_command)
        except mysql.connector.Error as err:
            # wrong hostname
            if err.errno == errorcode.CR_WRONG_HOST_INFO:
                print(err)
                # break
            # could not make initial server connection
            elif err.errno == errorcode.CR_CONN_HOST_ERROR:
                print("Could not make initial connection. Retrying in 5",
                      "seconds...")
            # errors during the a query
            elif((err.errno == errorcode.CR_SERVER_LOST_EXTENDED) |
                 (err.errno == errorcode.CR_SERVER_LOST) |
                 (err.errno == errorcode.ER_SERVER_SHUTDOWN)):
                print(err)
                print("Database connection broke. Reconnecting...")
                DBConnector.cursor.close()
            # errors in database access informatoin (password, name, etc.)
            elif ((err.errno == errorcode.ER_DBACCESS_DENIED_ERROR) |
                  (err.errno == errorcode.ER_ACCESS_DENIED_ERROR)):
                print(err)
            # unknown or uncaught error
            else:
                raise
            # wait for retry
            connection_tries += 1
            time.sleep(delay_time)

            #  retry connection 
            DBConnector.make_connection()
        # retrieve info from query and close query when there are no
        # connections problems
        else:
            rows = []
            if(DBConnector.cursor.with_rows):
                rows = DBConnector.cursor.fetchall()
            DBConnector.cnx.commit()
            return rows
    # failed to connect after retrying multiple times
    else:
        print("Could not reconnect at all. Exiting program")
        sys.exit()


def write_to_database(DBConnector, tb_name, xml_string, file_name, job_info_id,
                      cur_time, job_status, check_sum):
    """
    Inserts into a database a new entry for the output of the jobbuilder
    """
    add_output = ("INSERT INTO {} "
                  "(output_file, filename, jobinfoid, "
                  "jobfilecreated, jobstatus, checksum)"
                  "VALUES ({!r}, {!r}, {}, "
                  "{}, {!r}, {!r})") .format(tb_name,
                                             xml_string, file_name, job_info_id,
                                             cur_time, job_status, check_sum)
    run_sql_command(DBConnector, add_output)


def check_and_create_jobs(input_wildcards, output_wildcards, template_name,
                          files_db_cnx, files_table_name,
                          jobs_db_cnx, jobs_table_name,
                          job_name, xml_string):
    """
    Creates jobs based on the inputs found in the database in the table given
    """
    query_list = []
    file_number = 0

    s = input_wildcards[0].replace('*', '%')

    query = ("SELECT filename FROM {} "
             "WHERE filename LIKE {!r}") .format(files_table_name, s)
    rows = run_sql_command(files_db_cnx, query)
    # loops through all the first inputs found, and checks them against all
    # the other inputs
    if(rows is not None):
        for f in range(len(rows)):
            index = rows[f][0].find('_CS')
            time_stamp = rows[f][0][:index]
            #  used to check later if the job already exists in the queue
            checksum_name = time_stamp + output_wildcards[0][1:]
            all_matches = True
            no_matches = []  # for marking which files were missing in match

            # searches in the database if the output files exist
            # if they all exist, skips, else moves on to making the job
            for f in range(len(output_wildcards)):
                end_prod_name = time_stamp + output_wildcards[f][1:]
                if not (end_prod_exists(files_db_cnx, files_table_name,
                        end_prod_name)):
                    break
            # only continues if all output files were found
            else:
                continue

            # searches job queue to see if job already exists
            # - skips if found
            if(job_exists(jobs_db_cnx, jobs_table_name, checksum_name)):
                if(verbosity >= 1):
                    print(checksum_name, " is already in the job queue. Moving on")
                continue
            # goes through all other input files, and finds matches with
            # first input wildcard
            for i in range(1, len(input_wildcards)):
                find_string = time_stamp + input_wildcards[i][1:]

                # search for next item to see if exists in database
                new_query = ("SELECT filename FROM {} "
                             "WHERE filename = {!r}") .format(files_table_name,
                                                              find_string)
                new_row = run_sql_command(files_db_cnx, new_query)

                if(not new_row):
                    all_matches = False
                    no_matches.append(find_string)
            if all_matches:
                print("Creating job for", checksum_name)  
                now_time = time.strftime('%Y%m%d.%H%M%S')
                job_filename = (str(now_time) + '.' + str(file_number) + '.'
                                '' + template_name)
                s = create_new_xml_file(jobs_db_cnx, jobs_table_name,
                                        xml_string, time_stamp, job_filename,
                                        job_name, checksum_name)
                file_number += 1
            else:
                for i in range(len(output_wildcards)):
                    out_filename = (path.join('NoCreate')
                                    + '/' + time_stamp
                                    + output_wildcards[i][1:]
                                    + '.txt')
                    out = open(out_filename, 'w')
                    for j in range(len(no_matches)):
                        out.write(no_matches[j])
                        out.write('\n')
                    out.close()


# -------------------------------Main Function------------------------------
def main(files_config_loc, jobs_config_loc, jobname, template_loc,
         new_verbosity):
    global verbosity
    verbosity = new_verbosity
    # retrieve database config information from config files
    with open(files_config_loc, 'r') as file:
        config_files = json.load(file)

    with open(jobs_config_loc, 'r') as file:
        config_jobs = json.load(file)

    # connect to the databases
    files_cnx = DBConnector(config_files)
    jobs_cnx = DBConnector(config_jobs)

    # find the ini files in the template folder
    template_folder = template_loc

    template_files = access_templates(template_folder, '*' + jobname)

    # goes through all the files found in the template folder
    for i in range(len(template_files)):
        # file address of template file
        template_file_loc = template_folder + '/' + template_files[i]

        # parse the given ini file to find the xml string to be read
        ini_parser = configparser.ConfigParser()
        ini_parser.read(template_file_loc)
        xml_string = ini_parser['write_file']['contents']
        xml_string = xml_string.strip()  # remove whitspace and newlines

        # creates parsers to the xml template
        xml_file_tree = EleTree.ElementTree(EleTree.fromstring(xml_string))
        xml_file_elements = xml_file_tree.getroot()

        # retrieves input and output wildcards from template file
        input_wildcards = import_input_wildcards(xml_file_elements)
        output_wildcards = import_output_wildcards(xml_file_elements)

        # checks for wildcard errors - if found, continues onto next file
        if(check_wildcard_errors(input_wildcards, output_wildcards,
                                 template_file_loc)):
            continue

        # finds the job name based on the title of the file
        split_template_name = template_files[i].split('_')
        job_name = split_template_name[2]
        if verbosity >= 1:
            print("Start searching to make jobs for " + jobname)
        # check_and_create_jobs('files', input_wildcards, output_wildcards,
        # job_name, xml_string, files_cnx, jobs_cnx)
        check_and_create_jobs(input_wildcards, output_wildcards, template_files[i],
                              files_cnx, 'files',
                              jobs_cnx, 'jobs',
                              job_name, xml_string)
    # close before finishing
    files_cnx.close_connections()
    jobs_cnx.close_connections()

    if verbosity >= 1:
        print("Finished!")
