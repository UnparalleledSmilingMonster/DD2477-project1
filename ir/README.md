## Packages
This engine is coded with Python 3.
The following Python packages are necessary (the versions provided are the ones we use, we cannot ensure the engine will run properly on different versions) :
- elasticsearch, elasticsearch-dsl : `pip install elasticsearch==7.17.9 elasticsearch-dsl==7.4.1`
- numpy : `pip install numpy==1.21.2`
- pyQt : `pip install pyqt5==5.15.7`
- nltk : `pip install nltk==3.7`
- pyenchant : Necessary only if you want to rebuild the bigrams. In that case, uncomment line 28 in **spelling_correction.py**  `pip install pyenchant` 
- beautifulsoup : `pip install beautifulsoup4`
- pandas : `pip install pandas`
- requests : `pip install requests`
- newscatcher : Do not install it with pip as there is a version issue. `pip install feedparser --upgrade` `python newsPack/setup.py install`. You may have to move the **newscatcher** directory to get it found by Python. 


## Installs
The user should have a version of elasticsearch up to date (>= 8). You can either download it from [here](https://www.elastic.co/downloads/elasticsearch) or build it using from the sources. The dataset is available on the GitHub [repository](https://github.com/UnparalleledSmilingMonster/DD2477-project1/tree/7.14/ir) under the name **formatted_dataset.json**. It should be manually uploaded to elasticsearch using Kibana, name the index **"new_news"**. Note that an instance of elasticsearch must be online before one runs the news recommendation engine. You must run elasticsearch on your computer WITHOUT security. It can be done by adding `xpack.security.enabled: false` to config/elasticsearch.yaml


## Running the recommender engine
Execute `python gui.py` in the **ir** directory of the repository. The first window is for the login, type in a username. If the username already exists, it will load the corresponding profile. Otherwise, a new window opens for the creation of the new user profile. One has to indicate what he likes (1 click) and what he dislikes (2 clicks). At least 3 likes are necessary to fine tune the profile. After this step, the search window opens, the buttons are self-explanatory. 

## Evaluation 
You can find the articles rated in the directory **evaluation** for the recommendation relevance part.

## Issues you may run through
- Depending from where you run the program, you can have errors with files not found for the spelling correction. Go inside **spelling_correction.py** and fix the paths to the bigrams and unigrams **.json* files.
- The *update* functions works well but has the same issue with paths. Modify accordingly **news_updater.py**
- The dataset used for the articles is now quite old. We originally compelled the recommendations to be no more than 2 years old. This causes no articles to be recommended. I fixed it to 3 years, you can fix the limit by yourself by modifying the variable *number_of_days* at line 627 in `python gui.py`.

## Disclaimer
When we started the project we forked elasticsearch because we thought we would have to directly modify the repository. That is why our commits are only done in branch 7.14 on the forked repo. (There was a bit of a mixup)


