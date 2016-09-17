# reposbymonth.py
# Convert temp.csv to temp2.csv (monthly totals)
# temp.csv was created with this gitdata command:
# gitdata repos -o* -amsftgits -sa -nmsrepos20160901.csv -fowner.login/name/private -v
import csv

with open('temp.csv', newline='') as csvfile1, open('temp2.csv', 'w', newline='') as csvfile2:
    reporeader = csv.reader(csvfile1, delimiter=' ', quotechar='|')
    repowriter = csv.writer(csvfile2, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    for row in reporeader:
        values = row[0].split(',')
        values[3] = values[3][:7]
        print(values)
        repowriter.writerow([','.join(values)])
