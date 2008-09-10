#!/broad/tools/apps/Python-2.5.2/bin/python
#
# View a batch from the database, with some options to re-execute it
#
import cgitb
cgitb.enable()
import RunBatch
import StyleSheet
import cgi
import os
import os.path

print "Content-Type: text/html"
print

form = cgi.FieldStorage()
batch_id = int(form["batch_id"].value)
my_batch = RunBatch.LoadBatch(batch_id)
if form.has_key("submit_run"):
    for run in my_batch["runs"]:
        if run["run_id"] == int(form["submit_run"].value):
            result = RunBatch.RunOne(my_batch,run)
            print "<html><head><title>Batch # %d resubmitted</title>"%(batch_id)
            StyleSheet.PrintStyleSheet()
            print "</head>"
            print "<body>"
            print "Your batch # %d has been resubmitted."%(batch_id)
            print "<table class='run-table'>"
            for key in result:
                print "<tr><td><b>%s:</b></td><td style='white-space:nowrap'>%s</td></tr>"%(key,result[key])
            print "</table>"
            print "</body></html>"
else:
    print "<html>"
    print "<head>"
    print "<title>View batch # %d</title>"%(batch_id)
    StyleSheet.PrintStyleSheet()
    print "</head>"
    print "<body>"
    print "<div>"
    print "<h1>View batch # %d</h1>"%(batch_id)
    print "<table class='run_table'>"
    print "<thead><tr>"
    print "<th>Start</th><th>End</th><th>Job #</th><th>Status</th><th>Text output file</th><th>Results file</th>"
    print "<th><div>"
    print "<div style='position:relative; float=top'>Delete files</div>"
    print """<div style='position:relative; float=top'>
    <form action='DeleteFile.py' method='POST'>
    <input type='hidden' name='batch_id' value='%(batch_id)d'/>
    <input type='submit' 
                         name='delete_action' 
                         value='Text'   
                         title='Delete all text files' 
                         onclick='return confirm("Do you really want to delete all text files for this batch?")'/>
    <input type='submit' 
                         name='delete_action' 
                         value='Output'   
                         title='Delete output files' 
                         onclick='return confirm("Do you really want to delete all output files for this batch?")'/>
    <input type='submit' 
                         name='delete_action' 
                         value='Done'   
                         title='Delete done files' 
                         onclick='return confirm("Do you really want to delete all done files for this batch?")'/>
    <input type='submit' 
                         name='delete_action' 
                         value='All'   
                         title='Delete all files for this batch' 
                         onclick='return confirm("Do you really want to delete all files for this batch?")'/>
    </form>
    </div>"""%(my_batch)
    print "</div></th>"
    print "</tr></thead>"
    print "<tbody>"
    jobs_by_state = {}
    for run in my_batch["runs"]:
        x = my_batch.copy()
        x.update(run)
        x["text_file"] = RunBatch.RunTextFile(run)
        x["text_path"] = RunBatch.RunTextFilePath(my_batch,run)
        x["done_file"] = RunBatch.RunDoneFile(run)
        x["done_path"]=  RunBatch.RunDoneFilePath(my_batch,run)
        x["out_file"] =  RunBatch.RunOutFile(run)
        x["out_path"] =  RunBatch.RunOutFilePath(my_batch,run)
        print "<tr>"
        print "<td>%(start)d</td><td>%(end)d</td><td>%(job_id)s</td>"%(x)
        if os.path.isfile(x["done_path"]):
            cpu = RunBatch.GetCPUTime(my_batch,run)
            print "<td style='color:green'>"
            if cpu:
                print "Complete (%.2f sec)"%(cpu)
            else:
                print "Complete"
            stat = "Complete"
        else:
            job_status = RunBatch.GetJobStatus(run["job_id"])
            stat = "Unknown"
            if job_status and job_status.has_key("STAT"):
                stat=job_status["STAT"]
            print """
<td style='color:red'>%s<br/>
    <form action='ViewBatch.py' method='POST' target='ResubmitWindow'>
    <input type='hidden' name='batch_id' value='%d' />
    <input type='hidden' name='submit_run' value='%d' />
    <input type='submit' value='Resubmit' />
    </form>
</td>"""%(stat,batch_id,run["run_id"])
        if jobs_by_state.has_key(stat):
            jobs_by_state[stat].append(run)
        else :
            jobs_by_state[stat] = [ run ]
        print "<td><a href='ViewTextFile.py?run_id=%(run_id)d' title=%(text_path)s>%(text_file)s</a></td>"%(x)
        print "<td title='%(out_path)s'>%(out_file)s</td>"%(x)
        #
        # This cell contains the form that deletes things
        #
        print "<td><form action='DeleteFile.py' method='POST'>"
        print "<input type='hidden' name='run_id' value='%(run_id)d' />"%(x)
        print """<input type='submit' 
                         name='delete_action' 
                         value='Text'   
                         title='Delete file %(text_path)s' 
                         onclick='return confirm("Do you really want to delete %(text_file)s?")'/>"""%(x)
        print """<input type='submit' 
                         name='delete_action' 
                         value='Output'   
                         title='Delete file %(out_path)s' 
                         onclick='return confirm("Do you really want to delete %(out_file)s?")'/>"""%(x)
        print """<input type='submit' 
                         name='delete_action' 
                         value='Done'   
                         title='Delete file %(done_path)s' 
                         onclick='return confirm("Do you really want to delete %(done_file)s?")'/>"""%(x)
        print """<input type='submit' 
                         name='delete_action' 
                         value='All'   
                         title='Delete all files for this run' 
                         onclick='return confirm("Do you really want to delete %(text_file)s, %(out_file)s and %(done_file)s?")'/>"""%(x)
        print "</form></td>"
        print "</tr>"
    print "</tbody>"
    print "</table>"
    print "</div>"
    print "<div style='padding:5px'>"
    #
    # The summary table
    #
    print "<div style='position:relative;float:left'>"
    print "<table class='run_table'>"
    print "<thead>"
    print "<tr><th style='align:center' colspan='2'>Job Summary</th></tr>"
    print "<tr><th>Status</th><th>Count</th></tr>"
    print "</thead>"
    print "<tbody>"
    for state in jobs_by_state:
        print "<tr><th>%s</th><td>%d</td></tr>"%(state,len(jobs_by_state[state]))
    print "</tbody>"
    print "</table>"
    print "</div>"
    #
    # Kill button
    print "<div style='position:relative; float:left; padding:10px'>"
    print "<div style='position:relative; float:top'>"
    print "<form action='KillJobs.py'>"
    print "<input type='hidden' name='batch_id' value='%(batch_id)d'/>"%(my_batch)
    print """<input type='submit' 
                     value='Kill all incomplete jobs' 
                     onclick='return confirm("Do you really want to kill all jobs?")' />"""
    print "</form>"
    print "</div>"
    #
    # Upload to database button
    #
    sql_files = []
    for filename in os.listdir(my_batch["data_dir"]):
        if filename.upper().endswith(".SQL"):
            sql_files.append(filename)
    if len(sql_files):
        for filename in sql_files:
            print "<div style='position:relative; float:top'>"
            print "<form action='UploadToDatabase.py' method='POST'>"
            print "<input type='hidden' name='sql_script' value='%s' />"%(filename)
            print "<input type='hidden' name='batch_id' value='%(batch_id)d'/>"%(my_batch)
            print """<input type='submit'
                             value='Run database script %(filename)s?'
                             onclick='confirm("Are you sure you want to upload to the database using %(filename)s?"' />"""%(globals())
            print "</form>"
            print "</div>"
    print "</div>"
    print "</div>"
    print "</body>"