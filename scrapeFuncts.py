from bs4 import BeautifulSoup
from selenium import webdriver
import urlList
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pickle
import time

#Gathers URLs for fertilizer trends and then extracts information from table within those pages

# will need to replace chromedriver.exe for appropriate per operating system

# returns href after specified string
def hrefSearch(searchStr, source):
	soupStr = str(source)
	results = []
	index = 0
	while index != -1:
		index = soupStr.find(searchStr,index)
		index = soupStr.find("href=",index) + 6
		#because i added 6 up here, check for 5 (-1 is not found -1 + 6 = 5)
		if index is 5:
			return results
		endIndex = soupStr.find('"', index)
		results.append("https://www.dtnpf.com" + soupStr[index: endIndex])
		index = endIndex + 1

#returns data from table on requested URL
def tableReturn(source):
	data = []
	# finds "DRY" <- table title , and then pulls parent to get info into list of lists
	table = source.find(text="DRY").find_parent("table")
	table_body = table.find('tbody')
	rows = table_body.find_all('tr')
	for row in rows:
	    cols = row.find_all('td')
	    cols = [ele.text.strip() for ele in cols]
	    data.append([ele for ele in cols if ele]) # Get rid of empty values
	return data

def gspreadAuth():
	scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
	credentials = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
	gc = gspread.authorize(credentials)
	wks = gc.open_by_url("https://docs.google.com/spreadsheets/d/1iEwsC2vCy8QuRvTtZyRzSdkpeTcpgCRtHgFsObaMlHA/edit#gid=0")
	ws = wks.get_worksheet(0)
	return ws



#finds next empty row
def next_available_row(sheet):
	str_list = list(filter(None, sheet.col_values(1)))  # fastest
	return len(str_list)

#table json break list in half liquid and dry so can upload to drive across
if __name__ == "__main__":
	#declare webdriver get base webpage
	driver = webdriver.Chrome()
	url  = "https://www.dtnpf.com/agriculture/web/ag/news/crops/more"
	driver.get(url)
	html = driver.page_source
	soup = BeautifulSoup(html,"html.parser")
	ws = gspreadAuth()
	totals = 0;
	links = hrefSearch("DTN Retail Fertilizer Trends", soup) #find links
	for link in links: #iterate through links check if any have already been used
		count = 0;
		if link not in urlList.urlList:
			urlList.urlList.append(link) #add link to list
			driver.get(link)
			html = driver.page_source
			soup = BeautifulSoup(html,"html.parser")
			data = tableReturn(soup) # get data from link
			if ['LIQUID'] in data:
				split = data.index(['LIQUID'])
			elif ['Liquid'] in data:
				split = data.index(['Liquid'])
			dryData = data[:split] 
			liquidData = data[split:]
			dateCol = ws.col_values(3)
			for x,y in zip(dryData, liquidData):
				if len(x[0])>11 and x[0] not in dateCol:
					count = count+1;
					ws.append_row([x[0].split()[-1], x[0].split()[0], x[0],x[1],x[2],x[3],x[4],y[1],y[2],y[3],y[4]])
		else:
			print(link , "in URL list, skipping")
		print("Added" ,str(count) ,"values from " , link)
		totals = totals + count
		time.sleep(5) #rate limit
 
	#writeback url list
	with open('urlList.py', 'w') as file:
		file.write('urlList = ')
		file.write(str(urlList.urlList))
	print("Program complete added", totals,"values")