import gspread,time
from selenium import webdriver
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials

# access to google spreadsheet

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)
sheet = client.open("GSheet-name-goes-here").sheet1   #your G sheet name

#get newly entered profile links. storing entries for later use

linknames,entries=[],[]
for i in range(len(sheet.col_values(1))-1):
    if sheet.cell(i+2,2).value.strip()=='':
        if 'linkedin.com' in sheet.cell(i+2,1).value:
            linknames.append(sheet.cell(i+2,1).value)
        else:
            linknames.append('https://www.linkedin.com/in/'+sheet.cell(i+2,1).value)
        entries.append(sheet.cell(i+2,1).value.strip())
print(linknames)

#open linkedin in browser

browser=webdriver.Chrome('chromedriver.exe')
browser.get('https://www.linkedin.com/uas/login')
config=open('config.txt')
lines=config.readlines()
username=lines[0]
password=lines[1]
config.close()
elementID=browser.find_element_by_id('username')
elementID.send_keys(username)
elementID=browser.find_element_by_id('password')
elementID.send_keys(password)
elementID.submit()

# scrap

k=0
for link in linknames:
    browser.get(link)

    # scroll down and load whole page
    for i in range(0,4000,200):
        browser.execute_script(f"window.scrollBy(0,{i})", "")
        time.sleep(2)

    # scroll to expand skills
    try:
        skillz=browser.find_element_by_class_name('pv-skills-section__chevron-icon')
        browser.execute_script("arguments[0].scrollIntoView(true);", skillz)
        browser.execute_script("window.scrollBy(0,-300)", "")
        skillz.click()
    except:
        skillz=0
    src=browser.page_source
    soup=BeautifulSoup(src,'lxml')
# about
    name=soup.find('li', class_='inline t-24 t-black t-normal break-words').text.strip()
    pic='=image("'+soup.find('img',title=name)['src']+'")'
    des=soup.find('div',class_='flex-1 mr5').h2.text.strip()
    address=soup.find('li',class_='t-16 t-black t-normal inline-block').text.strip()
    try:
        temp_conn=soup.find('span',class_='t-16 t-black t-normal').text.strip()
        connections=temp_conn[:temp_conn.find(' ')]
    except:
        connections=0
#exp
    try:
        exp=soup.find('section',id='experience-section')
        workedas=exp.find_all('h3')
        recentlyWorkedAs,companies,periods,durations,allskills=[],[],[],[],[]
        for i in workedas:
            recentlyWorkedAs.append(i.text.strip())
        company=exp.find_all('p',class_="pv-entity__secondary-title t-14 t-black t-normal")
        for i in company:
            if '\n' in i:
                i=i.text.replace('\n','')
                companies.append(' '.join(i.split()))
            else:
                companies.append(' '.join(i.text.split()))
        period = exp.find_all('h4',class_="pv-entity__date-range t-14 t-black--light t-normal")
        for i in period:
            periods.append(i.text.replace('Dates Employed\n',''))
        duration=exp.find_all('h4',class_="t-14 t-black--light t-normal")
        for i in duration:
            durations.append(i.text.replace('Employment Duration\n',''))
    except:
        companies=recentlyWorkedAs=periods=durations=['no exp']
# a temporary hardcode for people with no exp
    if len(companies)<2:
        for i in range(2):
            companies.append('nil')
            recentlyWorkedAs.append('nil')
            periods.append('nil')
            durations.append('nil')
#edu
    college=soup.find('h3',class_='pv-entity__school-name t-16 t-black t-bold').text.strip()
    degree=soup.find('span',class_='pv-entity__comma-item').text.strip()
#skills
    if skillz!=0:
        skills = soup.find_all('div', class_='display-flex align-items-center flex-grow-1 full-width')
        allskills, finskills = [], []
        for skill in skills:
            allskills.append(skill.text.strip())
        for i in allskills:
            if '\n' in i:
                temp = i.split('\n')
                finskills.append((temp[0], temp[-1]))
            else:
                finskills.append((i, 'nil'))
        stringskills = '\n'.join([str(i) for i in finskills])
    else:
        pass

#write in sheet
    data=[name,pic,des,address,connections,companies[0],recentlyWorkedAs[0],periods[0],durations[0],
          companies[1],recentlyWorkedAs[1],periods[1],durations[1],degree+' in '+college,stringskills]
    row=int(str(sheet.find(entries[k]))[7])
    cell_list = sheet.range(f'B{row}:P{row}')
    for cell,values in zip(cell_list,data):
        cell.value=values
    sheet.update_cells(cell_list,value_input_option='USER_ENTERED')
    k+=1
browser.close()



