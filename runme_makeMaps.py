import pandas as pd
import numpy as np
import webbrowser
import os
from ZealtyCrawler import ZealtyCrawler

#Note: for installing geopandas, had to following SO answer here: https://stackoverflow.com/a/58943939/6292794
#Also had to change final line from "pipwin install geopandas" to "pip install geopandas"
import geopandas as gpd


def getGeoDataframe(geoJsonFilename):
    geoDataFrame = gpd.read_file(geoJsonFilename)
    geoDataFrame = geoDataFrame.drop(columns=['created_at',
                                              'updated_at'])  # Drop columns containing datetimes to avoid issues with serializing datetimes

    # Select only the columns we care about (could combine with dropping datetime columns above. Keeping seperate because those columns must be dropped to avoid a bug, where-as columns here are a choice)
    geoDataFrame = geoDataFrame[['geometry', 'csdname', 'ername', 'csduid']]
    geoDataFrame.csduid = pd.to_numeric(geoDataFrame.csduid, errors='coerce')

    # Correct scraped neighborhood names that don't line up with Zealty neighborhoods

    # TODO: names of neighborhoods don't quite line up perfectly between datasets (compared them in matlab). Some seem
    # #to be due to capitalization or formatting issues (e.g. Fraserview VE vs FraserView VE, Yale vs Yale - Dogwood
    # Valley) while some of the islands seem to be missing in the scraped dataset (e.g. Gabriola island). Figure out
    # which ones can be salvaged, throw out the remaining entries in the scraped dataset that aren't found in the map
    # dataset (e.g. aggregate regions) then combine datasets and plot

    #TODO: In the process of figuring out names that need to be corrected using the spreadhsheet "Comparing Geometry Names to Zealty Names"
    areaNameConversionDictionary = {
        'Gibsons & Area': 'Gibsons',
        'Grandview VE': 'Grandview Woodland',
        'Hastings East': 'Hastings Sunrise',
        'FraserView VE': 'Fraserview VE',
        'Boyd park': 'Boyd Park'
    }#TODO: Geometry data is missing south marine neighborhood in zealty

    geoDataFrame[['csdname']] = geoDataFrame[['csdname']].replace(areaNameConversionDictionary)

    geoDataFrame.rename(columns={'csdname': 'AreaName'}, inplace=True)

    return geoDataFrame

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    #Change this line to determine which property type will be scraped. Possible valid types are :
    #  'All Residential'
    #  'Detached'
    #  'Apartment'
    #  'Townhouse'
    #  'Manufactured on Pad'
    #  'Multi-Family'
    #  'Vacant Lot'
    ###
    propertyType = 'Townhouse'
    ###
    
    #Get geography data
    #Original data from here: https://vadimmarusin.carto.com/tables/bc_condo_prices_by_neighbourhood/public
    #Modified using Google MyMaps here: https://www.google.com/maps/d/u/0/edit?hl=en&mid=1GH5NiZg0KxC7O9gBG40dlvKDGBRuFVE&ll=49.326468086686845%2C-123.09479915231066&z=15
    #(After exporting from Google MyMaps as KML, had to convert to GeoJSON using online tool and then remove accidentally added newlines [i.e. "\n"] manually)
    geoJsonFilename = 'myBoundaries\\bc_condo_prices_by_neighbourhood_modified.geojson'
    geoDataFrame = getGeoDataframe(geoJsonFilename)
    
    

    #Get real-estate data
    zealtyCrawler = ZealtyCrawler()
    scrapedDataFrame = zealtyCrawler.scrapeStatisticsTableData(propertyType)
    zealtyCrawler.teardown_method()

    scrapedDataFrame.to_csv('scrapedDataFrame_' + propertyType + '.csv')
    geoDataFrame.to_csv('geoDataFrame_' + propertyType + '.csv')


    combinedGeoDataFrame = geoDataFrame.set_index('AreaName').join(scrapedDataFrame.set_index('AreaName'), how='inner')
    combinedGeoDataFrame.to_csv('combinedGeoDataFrame_' + propertyType + '.csv')
    combinedGeoDataFrame.to_file('combinedGeoDataFrame_' + propertyType +  '.json', driver="GeoJSON")
    #combinedGeoDataFrame = gpd.read_file('combinedGeoDataFrame_' + propertyType +  '.json')
    
    allPlottingVariables = ["MedianPrice", "MedianPricePerSqFt", "MedianDOM", "NumSold"]
    
    for plottingVariable in allPlottingVariables:
      lowerLimitQuantile = 0.01
      upperLimitQuantile = 0.9
    
      vmin = combinedGeoDataFrame[plottingVariable].quantile(lowerLimitQuantile)
      vmax = combinedGeoDataFrame[plottingVariable].quantile(upperLimitQuantile)

        
      m = combinedGeoDataFrame.explore(plottingVariable, 
                                       categorical=False,
                                       cmap='jet', 
                                       vmin=vmin,
                                       vmax=vmax,
                                       legend_kwds={'colorbar':True, 'max_labels' : 5}, 
                                       tooltip_kwds={'localize': True})


      # write the returned map to disk and then open it a la https://stackoverflow.com/a/70551913/6292794
      outputFilename = 'vanRealEstateMap_' + propertyType + '_' + plottingVariable + '.html'
      m.save(outputFilename)
      webbrowser.open('file://' + os.path.realpath(outputFilename))