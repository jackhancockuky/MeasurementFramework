from gettext import install
import os
import json

import elk_utilities as eu
import custom_dashboards

import logging 



def copy_files(src_dir, dst_dir):
    os.system(f"cp -r {src_dir}/* {dst_dir}")

def copy_file(src_file, dst_file):
    os.system(f"cp -r {src_file} {dst_file}")


def get_file_basenames(files):
    basenames = []
    for f in files:
        basenames.append(os.path.basename(f))
    return basenames


def main():

    logFilePath = os.path.join(eu.log_dir, "update.log")
    logging.basicConfig(filename=logFilePath, format='%(asctime)s %(name)-8s %(levelname)-8s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level="INFO")
    logging.info("-----Start Update Script.-----")


    ret_val = { "success":True, "msg":"" }
    data = eu.get_data()

#############
# testing dashboard single loading

    command_found = False
    if "commands" in data:
        # Ensure certain commands are run in the needed order


        for cmd in data["commands"]:
            if "cmd" in cmd and cmd["cmd"] == "upload_dashboards":
                ret_val['uploaded_dashboards'] = {}
                command_found = True
                logging.info("---upload_dashboards command found---")
                # move files from files dir to dashboards dir
                if "dashboard_filenames" in cmd:
                    logging.info("found dashboard_filenames")
                    for dashboard_filename in get_file_basenames( cmd["dashboard_filenames"] ):
                        logging.info(f"  Dashboard {dashboard_filename}")
                        src_dashboard_filename = os.path.join(eu.files_dir, dashboard_filename )
                        dst_dashboard_filename = os.path.join(eu.dashboards_dir, dashboard_filename )
                        logging.info(f"    Copy {src_dashboard_filename} to {dst_dashboard_filename}")
                        copy_file(src_dashboard_filename, dst_dashboard_filename)
                        
                        ret_val['uploaded_dashboards'][dashboard_filename] = {} 
                        ret_val['uploaded_dashboards'][dashboard_filename]['success'] = True

        for cmd in data["commands"]:
            if "cmd" in cmd and cmd["cmd"] == "add_dashboards":
                command_found = True
                logging.info("---add_dashboard command found---")
                ret_val["added_dashboards"] = {}

                # Check if user wants to force reinstall
                if "force" in cmd:
                    do_force = cmd["force"]
                    logging.info(f"add_dashboards force set to {do_force}")
                else:
                    do_force = False

                # Get list of installed dashboards to prevent double installing.
                installed_dashboards = eu.read_installed_dashboards()
                
                # import the dashboard into kibana
                if "dashboard_filenames" in cmd:
                    logging.info("found dashboard_filenames")
                    for dashboard_filename in get_file_basenames(  cmd["dashboard_filenames"] ):
                        logging.info(f"  Dashboard {dashboard_filename}" )

                        # Only install the dashboard if it has not been installed or if user wants to force reinstall
                        if do_force or dashboard_filename not in installed_dashboards:
                            logging.info( f"  Importing {os.path.join(eu.dashboards_dir, dashboard_filename )} to kibana" )
                            result = custom_dashboards.import_dashboard(dashboard_filename)
                            logging.info(result)
                            #ret_val["msg"] += f'Added dashboard {dashboard_filename}\n'
                            ret_val["added_dashboards"][dashboard_filename] = {}
                            ret_val["added_dashboards"][dashboard_filename]["success"] = result["success"]
                            ret_val["added_dashboards"][dashboard_filename]["msg"] = result["msg"]

                            if dashboard_filename in installed_dashboards:
                                logging.info("Forced reinstall of kibana dashboard.")
                            if result["success"] and dashboard_filename not in installed_dashboards:
                                installed_dashboards.append(dashboard_filename)
                                eu.write_installed_dashboards(installed_dashboards)
                        else:
                            ret_val["added_dashboards"][dashboard_filename] = {}
                            ret_val["added_dashboards"][dashboard_filename]["success"] = False
                            ret_val["added_dashboards"][dashboard_filename]["msg"] = "Already installed."

                        #else: Do nothing dashboard alread exists

                        # Version without force
                        # if dashboard_filename in installed_dashboards:
                        #     logging.info(f"{dashboard_filename} has already been installed so it will not be installed again." )
                        # else:
                        #     logging.info(os.path.join(eu.dashboards_dir, dashboard_filename ))
                        #     result = custom_dashboards.import_dashboard(dashboard_filename)
                        #     logging.info(result)
                        #     ret_val["msg"] += f'Added dashboard {dashboard_filename}\n'
                        #     ret_val[dashboard_filename] = {}
                        #     ret_val[dashboard_filename]["success"] = result["success"]
                        #     ret_val[dashboard_filename]["msg"] = result["msg"]
                        #     if (result["success"]):
                        #         installed_dashboards.append(dashboard_filename)
                        #         eu.write_installed_dashboards(installed_dashboards)
                            

                        #result["data"]  is not dependable json serializable
                        

    # if not command_found:
    #     # Command not recognized
    #     ret_val['msg'] += f"No recognized command found."    




####################






    if "cmd" in data:
        if "upload_custom_dashboards" in data["cmd"]:
            # get list of filenames
            if "dashboard_filenames" in data:
                # Dashboards should have been uploaded to the files directory.
                 #os.chdir(ansible_dir)
                for dfilename in data["dashboard_filenames"]:
                    src_dashboard_filename = os.path.join(eu.files_dir, dfilename)
                    dst_dashboard_filename = os.path.join(eu.dashboards_dir, dfilename)

                    copy_file(src_dashboard_filename, dst_dashboard_filename)
                    ret_val['msg'] += f'Have dashboard "{dfilename}.\n'
                    # do something with dashboard file
                    # maybe move them to the Dashboards dir
        if "add_custom_dashboards" in data["cmd"]:
             ret_val['msg'] += custom_dashboards.import_dashboards()

    print(eu.get_json_string(ret_val))
    #print(json.dumps(ret_val))

if __name__ == "__main__":
    main()