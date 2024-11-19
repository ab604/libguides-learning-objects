import pandas as pd
import requests
import re
import os
from datetime import datetime, timedelta

# Set up 
date = datetime.now().strftime('%Y-%m-%d')
report_date = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
old_date = (datetime.now() - timedelta(days=8)).strftime('%Y-%m-%d')
#links_file = os.environ.get('LINKS_FILE')
#if not links_file:
#    links_file = f"reports/get-links-{old_date}.csv"
#os.makedirs('reports', exist_ok=True)


# Download the CSV file from GitHub
url = f"https://raw.githubusercontent.com/ab604/link-crawler/main/reports/check-links-report-{report_date}.csv" 
#response = requests.get(url)
#csv_data = response.text

# Parse the CSV data
df = pd.read_csv(url)

# Print the dataframes
print(df.head())
#print(panopto_df.head())

# Filter for four types of LO
dfm = df[
    df['URL'].str.contains('[Aa]rticulate|[Tt]hinglink|[Ww]ordpress|[Pp]anopto|[Pp]owtoon', case=False)
]

# Create a new column 'lo' based on the 'url' column
dfm['lo'] = dfm['URL'].apply(lambda x: 
    'Panopto' if re.search('[Pp]anopto', x) else
    'ThingLink' if re.search('[Tt]hinglink', x) else
    'Articulate' if re.search('[Ar]ticulate', x) else
    'Wordpress' if re.search('[Ww]ordpress', x) else
    'Powtoon' if re.search('[Pp]owtoon', x) else
    'Other'
)
# 
print(dfm.head())

print(dfm.groupby('lo').size().reset_index(name='count'))