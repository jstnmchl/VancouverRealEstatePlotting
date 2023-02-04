#import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from bs4 import BeautifulSoup
import time
import pandas as pd
import os

def getValsFromParsedRow(parsedRow):
  namesOfRows = ['AreaName', 'NumSold', 'MedianPrice', 'MedianPricePerSqFt', 'MedianDOM'];
  if not parsedRow:
    #Use empty list to return names of rows being parsed
    return namesOfRows

  AreaName = parsedRow[0]

  N = len(parsedRow)
  if N == 17:
    # Expecting 17 entries when data is present
    NumSold = float(parsedRow[2].replace(',', ''))
    MedianPrice = float(parsedRow[7].replace(',', '').replace('$', ''))
    MedianPricePerSqFt = float(parsedRow[9].replace(',', '').replace('$', ''))
    MedianDOM = float(parsedRow[15])
  elif N == 16:
    #16 entries indicates data is missing, therefore return AreaName and populate the rest with nans/zeros
    NumSold = 0.0
    MedianPrice = float("NaN")
    MedianPricePerSqFt = float("NaN")
    MedianDOM = float("NaN")
  else:
    errorMsg = 'Expected row in table parsed from Zealty to have 16 or 17 entres but instead ' + \
               str(N) + \
               ' were observed. parsedRow printed to screen immediately before this error message'
    print('ParsedRow on error:')
    print(parsedRow)
    raise ValueError(errorMsg)

  return [AreaName, NumSold, MedianPrice, MedianPricePerSqFt, MedianDOM]

class ZealtyCrawler:
  def __init__(self):
    binary = FirefoxBinary('C:\\Program Files\\Mozilla Firefox\\firefox.exe')

    directoryName = os.path.dirname(__file__)
    executablePath = os.path.join(directoryName, 'geckodriver.exe')
    
    with open('ZealtyLogin.txt') as file:
        lines = [line.rstrip() for line in file]

    self._email = lines[0]
    self._password = lines[1]

    self.driver = webdriver.Firefox(firefox_binary=binary,
                                    executable_path=executablePath)
    self.isLoggedIn = False
    return
  
  def teardown_method(self):
    self.driver.quit()

  def login(self):
    self.driver.get("https://www.zealty.ca/")
    self.driver.set_window_size(1208, 824)
    self.driver.find_element(By.CSS_SELECTOR, ".fixed-width-button:nth-child(5)").click()
    self.driver.find_element(By.ID, "logButton").click()
    self.driver.find_element(By.NAME, "email").send_keys(self._email)
    self.driver.find_element(By.NAME, "password").send_keys(self._password)
    self.driver.find_element(By.CSS_SELECTOR, "div:nth-child(13) > .tall:nth-child(2)").click()

    # TODO: This method assumes that the login worked and sets the object state accordingly. Add logic to actually check
    #  that it worked
    self.isLoggedIn = True
    return

  def parseZealtyStatsTable(self):
    #Parse zealty table and return as pandas dataframe
    time.sleep(1.5)
    html = self.driver.page_source
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", {"class": "stripedTable"})
    table_rows = table.find_all('tr')

    parsedTableAsListOfLists = []
    for tr in table_rows:
      td = tr.find_all('td')
      #Get the text from each row, adding commas between different segments of text so they are separable afterwards (e.g. '5,25%' instead of '525%')
      row = [tr.getText(separator=u';') for tr in td]

      #Seperate out each entry, regardless of which tag it was in
      parsedRow = []
      for element in row:
        parsedRow.extend(element.split(';'))
      #Parse out values of interest from row

      if not parsedRow:
        #Empty row indicates header row in table. Don't add to parsed data
        continue
      parsedRowVals = getValsFromParsedRow(parsedRow)

      if parsedRowVals[0] == 'All Areas':
        #Indicates aggregate row which isn't of interest, therefore skip
        continue
      parsedTableAsListOfLists.append(parsedRowVals)

    columnNames = getValsFromParsedRow([])

    parsedTableAsDataFrame = pd.DataFrame(parsedTableAsListOfLists, columns=columnNames)

    #print(parsedTableAsDataFrame)

    return parsedTableAsDataFrame

  def scrapeStatisticsTableData(self, propertyType):
    VALID_PROPERTY_TYPES = ['All Residential', 
                            'Detached',
                            'Apartment', 
                            'Townhouse',
                            'Manufactured on Pad',
                            'Multi-Family',
                            'Vacant Lot']
    assert propertyType in VALID_PROPERTY_TYPES, "Invalid property type"

    if not self.isLoggedIn:
      self.login()

    #### Select dates
    # Number (17) appears to be counting in the drop-down list, starting at 1, downwards including the blank spaces that act as section breaks
    # Leaving this as 17 rather than "dropdown.find_element(By.XPATH, "//option[. = '2022 JAN-AUG - Summary']")" ensures
    # that even at a later date (e.g. into October) the same summary will be selected even though the option will then
    # likely read JAN-SEP instead of JAN-AUG
    #TODO: Remove magic number and make this more robust
    self.driver.find_element(By.CSS_SELECTOR, "#dateSelect > option:nth-child(19)").click()

    #### Select property type
    dropdown = self.driver.find_element(By.ID, "typeSelect")
    
    #TODO: Add property type as input
    propertyTypeSearchString = "//option[. = '" + propertyType + "']"
    dropdown.find_element(By.XPATH, propertyTypeSearchString).click()
    #dropdown.find_element(By.XPATH, "//option[. = 'Detached']").click()

    #### Select each region

    parsedTables = []
    listOfIndices = range(1, 39) #Hope and Area is 38
    #listOfIndices = range(1, 5)  # Hope and Area is 38
    for index in listOfIndices:
      cssSelectorString = '#regionSelect > option:nth-child(' + str(index) + ')'
      self.driver.find_element(By.CSS_SELECTOR, cssSelectorString).click()
      parsedTables.append(self.parseZealtyStatsTable())

    allTablesCombined = pd.concat(parsedTables, ignore_index=True)
    allTablesCombined[['AreaName']] = allTablesCombined[['AreaName']].replace({'GlenBrooke North': 'Glenbrooke North'})



    allTablesCombined.to_csv('allTablesCombined.csv', index=False)

    allTablesCombined = allTablesCombined.drop_duplicates()
    allTablesCombined.sort_values(by='AreaName', inplace=True, ignore_index=True)



    #TODO: names of neighborhoods don't quite line up perfectly between datasets (compared them in matlab). Some seem
    # #to be due to capitalization or formatting issues (e.g. Fraserview VE vs FraserView VE, Yale vs Yale - Dogwood
    # Valley) while some of the islands seem to be missing in the scraped dataset (e.g. Gabriola island). Figure out
    # which ones can be salvaged, throw out the remaining entries in the scraped dataset that aren't found in the map
    # dataset (e.g. aggregate regions) then combine datasets and plot

    return allTablesCombined
  
if __name__ == '__main__':
  obj = ZealtyCrawler()
  scrapedDataFrame = obj.scrapeStatisticsTableData()
  obj.teardown_method()

  print(scrapedDataFrame)
  print(len(scrapedDataFrame.index))
  print('Done!')