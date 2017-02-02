"""generate stats to summarize public repo growth across all Microsoft orgs

TO DO:
- automate the creation of the data file (import gitdata, etc.)
- automate the creation of the XLSX
"""
import collections

#-------------------------------------------------------------------------------
def get_totals(filename):
    """Read the specified data file and create a dictionary of the total public
    repos created for each month. Dictionary has two types of keys: year+month
    (e.g., '201702') or year+month+org (e.g., '201702microsoft'). The value is
    the number of public repos created in that year/month.

    Note that the data file was created with the following command:
    c:> gitdata repos -o* -amsftgits -sa -nmicrosoft-repos.csv
            -fowner.login/name/created_at/private -d -v
    """
    ymtotals = collections.defaultdict()

    for line in open(filename, 'r').readlines():
        values = line.strip().split(',') # create list of values

        if values[0] == 'owner_login' or values[3] != 'public':
            continue # these rows ignored

        orgname = values[0].lower()
        year = values[2][:4]
        month = values[2][5:7]
        for key in [year + month, year + month + orgname]:
            if key in ymtotals.keys():
                ymtotals[key] += 1
            else:
                ymtotals[key] = 1

    return ymtotals

#-------------------------------------------------------------------------------
def write_csv(ymtotals, filename):
    """Write a CSV file summarizing cumulative totals for Azure, Microsoft, and
    other orgs.
    """

    yearmonths = sorted([key for key in ymtotals])
    currentyear = yearmonths[0][:4] # first year
    currentmonth = yearmonths[0][4:6] # first month
    lastyear = yearmonths[-1][:4]
    lastmonth = yearmonths[-1][4:6]

    cumm_tot = 0
    cumm_az = 0
    cumm_ms = 0

    with open(filename, 'w') as fhandle:
        fhandle.write('year,month,microsoft,azure,other\n')

    while True:
        yearmonth = currentyear + currentmonth

        cumm_tot += ymtotals.get(yearmonth, 0)
        cumm_az += ymtotals.get(yearmonth + 'azure', 0)
        cumm_ms += ymtotals.get(yearmonth + 'microsoft', 0)
        print(currentyear, currentmonth, cumm_tot, cumm_az, cumm_ms)
        with open(filename, 'a') as fhandle:
            fhandle.write(currentyear + ',' + currentmonth + ',' + \
                str(cumm_ms) + ',' + str(cumm_az) + ',' + \
                str(cumm_tot - cumm_ms - cumm_az) + '\n')
        if currentmonth == '12':
            currentyear = str(int(currentyear) + 1).zfill(4)
            currentmonth = '01'
        else:
            currentmonth = str(int(currentmonth) + 1).zfill(2)
        if currentyear > lastyear or (currentyear == lastyear and currentmonth > lastmonth):
            break


#-------------------------------------------------------------------------------
if __name__ == '__main__':

    TOTALS = get_totals('microsoft-repos.csv')
    write_csv(TOTALS, 'publicrepototals.csv')
