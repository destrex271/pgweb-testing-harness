import os
import re

print("Executing")
print(os.listdir())

report_content = ''

with open('../../final_report.log', 'r') as report:
    report_content = report.read()
    report.close()

fail_logs = None

print("Length is ", len(report_content))

# Remove migration logs
report_content.replace('Running.*', '\r')
report_content.replace(r'App[A-z, ,0-9].*', '\r')

# Remove Webdriver Logs
# report_content.replace(r"\[WDM\].*", '')
report_content = re.sub(r"\[WDM\].*", '', report_content)

# Extract Failure Logs
indices = re.search(r'FAIL:.*', report_content)
ind1, ind2 = -1, -1
if indices:
    ind1 = indices.start()
indices = re.search('FAILED', report_content)
if indices:
    ind2 = indices.start()

if ind1 != -1 and ind2 != -1:
    fail_logs = report_content[ind1:ind2]

# Removing new lines
report_content.replace(r'System.*', '+++++++++++++++++++Running Tests++++++++++++++++++++')


# Write Failure logs
with open('../../failed_tests.log', 'w+') as fail_rep:
    commit_id = None
    try:
        with open('../../../commit_id.txt', 'r') as commit:
            commit_id = commit.read()
    except FileNotFoundError:
        pass
    if not fail_logs:
        fail_rep.write('No Tests Failed. The build {commit_id} is working fine!')
    else:
        fail_rep.write(r"The build {commit_id} failed the following tests:\n\n\n"+fail_logs)

with open('../../final_report.log', 'w') as report:
    report.write(report_content)
