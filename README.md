**Vancouver Real Estate Plotting**
Scrapes real-estate sold data in the lower-mainland (greater Vancouver area) and creates an interactive visualization of neighborhood-by-neighborhood data viewable in a web browser. 



Data can be scraped for different property types, including: detached, townhomes, apartments, and all residential. Data can be colorized by: median price, median price per square foot, median days on market, and total number sold. Regardless of how map is colorized, all metrics are visible when cursored over. At the time of writing (Jan 2023), scraped data corresponds to all sales in 2022.

Demo gif/image shows median sale price for detached homes sold in 2022.


**Setup**

Install Anaconda or miniconda. (See Note 1)

Navigate to the desired directory and, in the anaconda prompt, call: 

	conda env create -f environment.yml
	
	conda activate vancouverRealEstatePlotting
	
	conda install -c conda-forge geopandas
	

Download geckodriver.exe from the link below and place in root directory. For 64 bit windows, look for "...-win64.zip".

https://github.com/mozilla/geckodriver/releases

Create a (free) account on [Zealty.ca](https://www.zealty.ca/). Make sure the password you use is NOT being re-used with other accounts.(See Note 2)

In the root directory, create a file called "ZealtyLogin.txt" that contains the email for your Zealty account on the first line, and the password for your Zealty account on the 2nd line. (See Note 2)

Call "python runme_makeMaps.py" to scrape, save, and open maps for all property statistics (median price, median price per SqFt, num sold, median days on market) for the selected property type (e.g. "Detached"). This property type can be changed by editing the main function of runme_makeMaps.py


Note 1: Installing depencies using pip (atleast on windows) has significant headaches related to installing the C based dependencies of geopandas as described here: https://geopandas.org/en/stable/getting_started/install.html
(Trust me, I tried. Use conda.)

Note 2: The login strategy used is **NOT** secure. Plain-text passwords are, in general, a huge security no-no. This is why you should ensure the password you use is not re-used elsewhere. In this case, a security breach with a Zealty account is very low stakes, especially if the account you make is only used for this script.
