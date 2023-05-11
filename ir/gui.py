from datetime import datetime
import sys  
import os
import numpy as np
import json


from elasticsearch import Elasticsearch
from elasticsearch import helpers
from elasticsearch_dsl import Search, Q, Index, Document, Text, Keyword, UpdateByQuery
from elasticsearch_dsl.query import MoreLikeThis
from math import asin, pi
import news_updater as news_updater
from spelling_correction import Bigrams

from functools import partial

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QTextEdit 
from PyQt5.QtWidgets import QListWidget
from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtWidgets import QStackedLayout
from PyQt5.QtCore import QEventLoop
from PyQt5.QtCore import Qt


tags_elastic_search = {'POLITICS': 0, 'WELLNESS': 1, 'ENTERTAINMENT': 2, 'TRAVEL': 3, 'STYLE & BEAUTY': 4, 'EDUCATION': 5, 'HEALTHY LIVING': 6, 'QUEER VOICES': 7, 'FOOD & DRINK': 8, 'BUSINESS': 9, 'COMEDY': 10, 'SPORTS': 11, 'BLACK VOICES': 12, 'HOME & LIVING': 13, 'PARENTS': 14, 'U.S. NEWS': 15, 'TECH': 16, 'ARTS & CULTURE':17, 'WORLD NEWS':18, 'MEDIA':19, 'TASTE':20, 'WEIRD NEWS':21, 'RELIGION':22, 'CRIME':23, 'WOMEN':24, 'SCIENCE':25 }

def load_artificial_documents(filename):
    """ 
    Used in conjunction with a preference. Returns a doc id corresponding to the preference.
    """
    docs = {}
    with open(filename, 'r') as f:
        data= json.load(f)  
        for key,value in data.items():
            resp = Search(using=Elasticsearch("http://localhost:9200"), index="new_news").query("match_phrase", headline=value).execute()
            if len(resp) != 1 : 
                docs[key] = "ERROR"       
            else : 
                docs[key] = resp[0].meta.id
    return docs
              
          
artificial_docs = load_artificial_documents("artificial_documents.json")
#print(artificial_docs)

class User(Document):
    """
    Class to represent a user in elasticsearch. 
    """
    username = Keyword(index=False, multi = False)
    preferences = Keyword(multi=True) #list equivalent
    history = Keyword(multi=True)

    class Index:
        name = 'users'
        settings = {
          "number_of_shards": 1,
        }

    def save(self, ** kwargs):
        return super(User, self).save(** kwargs)

    def is_published(self):
        return datetime.now() > self.published_from
  
######################### USEFUL FUNCTIONS FOR ELASTIC SEARCH ################################

def reset_index(client, index):
    client.indices.delete(index=index, ignore=[400, 404])


def set_elastic_search(client):
    User.init(using = client)
    index_user = Index("users")
    if not index_user.exists(using=client):
        print("Index 'users' does not exist yet. Creating it ...")
        index_user.create(using=client)
    else:
        print("Index 'users' found")
    #user_0 = User(username="0", preferences = [], history = [])
    #user_0.save(using = client)
    

def list_user_es(client, index):
    """
    Returns list of all users in elasticsearch index 'users'
    """
    res = []
    search = Search(using=client, index=index)
    for elt in search.scan():
        res.append(elt.username)
    print(res)
    

    
def check_user_es(client, index, user):
    resp = Search(using=client, index=index).query("match", username=user).execute()
    if len(resp) == 0 : return False, None, []     
    elif len(resp) > 1 :
        raise Exception("Error multiple users with the same name")
    else :
        user = resp[0]
        #Regenerate missing fields (in the case where pref = [] or history = [], these fields do not exist)
        if "preferences" not in user : user.preferences = []
        if "history" not in user : user.history = []
        return  True, list(user.preferences), list(user.history)
          

def write_user_es(client, index, username, preferences, history = []):  
    User(username=username, preferences = list(preferences) , history = history).save(using = client, index = index)


def update_history(client, index, user, doc_id):
    try:
        #Think of creating the field history if it does not exist
        ubq = UpdateByQuery(using=client, index=index).query("match", username=user).script(source="if (!ctx._source.containsKey(\"history\")) { ctx._source.history = params.history } else ctx._source.history.addAll(params.history)", params= {"history":[doc_id]})
        ubq.execute()
        Index(index).refresh(using = client)
    
    except Exception as e:
        print(e)
        
def update_preferences(client, index, user, update_pref):
    try:
        #Think of creating the field preferences if it does not exist
        ubq = UpdateByQuery(using=client, index=index).query("match", username=user).script(source="if (!ctx._source.containsKey(\"preferences\")){ ctx._source.preferences = params.preferences } else{ for (int i = 0; i < ctx._source.preferences.length; ++i){ ctx._source.preferences[i] += params.preferences[i]}}", params= {"preferences":update_pref})
        ubq.execute()
        Index(index).refresh(using = client)
    except Exception as e:
        print(e)
        
        
def tags_to_preferences(doc_tags, power = 0.5, tags =tags_elastic_search):
    """
    Returns all the tags corresponding to a given document, formatted to match with the preferences format (one hot encoded)
    """
    L = np.zeros(len(tags))
    for tag in doc_tags :
        idx = tags.get(tag, -1)
        if idx == -1 : continue
        L[idx] = power
    return list(L) 
    


######################### DEPRECATED : uses .json file to store users       

# [{"user":"0", "preferences":[]}] : users.json default

def check_user(filename, username):
    """ 
    Checks if the input username already exists in the user base.
    """
    with open(filename, 'r') as f:
        data = json.load(f)  
        for entry in data:  
            if entry["user"] == username : return True, list(entry["preferences"]), list(entry["history"])
        f.close()
    return False, None, []
    
def write_user(filename, username, preferences):
    """ 
    Writes new user to the user base. With preferences vector (one hot encoded)
    """
    with open("users.json", 'r+') as f:
        f.seek(0, 2)  # seek to end of file; f.seek(0, os.SEEK_END) is legal
        f.seek(f.tell() - 2, 0)
        f.truncate()
        f.write(",")
        entry = {}
        entry["user"] = username
        entry["preferences"] = preferences
        entry["history"] = []
        json.dump(entry, f, separators=(',',': '))
        f.write(']')
        f.close() 

################################################
    

class MainWindow(QWidget):  
    """
    Main window. Login / Create user window.
    """  

    def __init__(self, tags_topics, address, index ):
        super().__init__()
        self.layout = QGridLayout(self) 
        self.set_window()
        self.define_widgets()    
        self.username = "" 
        self.tags_topics = tags_topics
        self.client =  Elasticsearch(address)
        reset_index(self.client, "users") #for debug purposes
        set_elastic_search(self.client)
        #check_user_es(self.client, "users", "tim")
        list_user_es(self.client, "users")
        self.preferences = None
        self.index = index
                
        
    def set_window(self):
        self.setWindowTitle("User")
        self.setGeometry(200, 200, 600, 700)     
        self.setFixedWidth(600)
        self.setFixedHeight(700)  


    def define_widgets(self):          
       
        text = QLabel(text ="Username", parent = self)
        self.layout.addWidget(text, 0 ,0)
       

        self.text_input = QLineEdit(parent = self)
        self.text_input.setPlaceholderText('If username not found, creates new user')
        self.layout.addWidget(self.text_input, 0,1)

        
        button_next = QPushButton("Next", parent = self)
        button_next.clicked.connect(self.forward)
        self.layout.addWidget(button_next, 2,1)
       
        
        button_quit = QPushButton("Quit", parent = self)
        button_quit.clicked.connect(self.close)
        self.layout.addWidget(button_quit, 2,0)
        
        self.setLayout(self.layout)

    
    def forward(self):
        self.username = self.text_input.text()
        if self.username == "":
            QMessageBox.about(self, "Warning", "No name provided.")
            return 
        
        status, self.preferences, self.history  = check_user_es(self.client, "users", self.username)
        if not status :  
            self.hide()
            self.ld_window = PreferencesWindow(self, self.tags_topics)
            self.ld_window.show()
            loop = QEventLoop()
            self.ld_window.setAttribute(Qt.WA_DeleteOnClose)
            self.ld_window.destroyed.connect(loop.quit)
            loop.exec() 
        
        else :
            self.search_window = SearchWindow(self, self.tags_topics, self.preferences, self.history)
            self.search_window.show()
            self.hide()
            loop = QEventLoop()
            self.search_window.destroyed.connect(loop.quit)
            loop.exec() 


      
############################################################################

class PreferencesWindow(QWidget):
    """
    Window to select preferences. (Cold start problem : select at least 3 positive)
    """
    def __init__(self, parent, tags_topics):
        super().__init__()
        self.parent = parent
        self.layout = QGridLayout(self) 
        self.tags_topics = tags_topics
        self.preferences = np.zeros(len(tags_topics))
        self.set_window()
        self.define_widgets()
       
    def set_window(self):
        self.setWindowTitle("New User : Preferences")
        self.setGeometry(350, 550, 500, 300)
        self.setFixedWidth(600)
        self.setFixedHeight(400)         


    def define_widgets(self):
        
        ok = QPushButton("Confirm", parent = self)
        ok.clicked.connect(self.forward)

        self.buttons = []         
        max_abs = 4       
        fct = []
        for i in range(len(self.tags_topics)):
            fct.append(partial(self.preference, i))
        
        for key, i in self.tags_topics.items():
            self.buttons.append(QPushButton(key.lower(), parent = self))
            u = i // max_abs
            v = i % max_abs
            self.buttons[i].clicked.connect(fct[i])
            self.layout.addWidget(self.buttons[i], u, v)
            
        self.layout.addWidget(ok, len(self.tags_topics) // max_abs + 2, 3)
        self.setLayout(self.layout)
    
    
    def preference(self, k):  
        idx = self.tags_topics.get(self.buttons[k].text().upper())
        if self.preferences[idx] == 0 :
            self.preferences[idx] = 3
            self.buttons[k].setStyleSheet('QPushButton {background-color: green;}')
        elif self.preferences[idx] == 3 :
            self.preferences[idx] = -1   
            self.buttons[k].setStyleSheet('QPushButton {background-color: red;}')     
        else : # -1
            self.preferences[idx] = 0
            self.buttons[k].setStyleSheet('QPushButton {background-color: white;}') 
        
            
    def forward(self):
        if len(self.preferences[self.preferences == 3]) < 3 :
            QMessageBox.about(self, "Cold start !", "Select at least 3 positive preferences.")
            return
            
        write_user_es(self.parent.client, "users", self.parent.username, self.preferences, [])
        self.parent.search_window = SearchWindow(self.parent, self.tags_topics, self.preferences, self.parent.history)
        self.parent.search_window.show()
        self.hide() 
        loop = QEventLoop()
        self.parent.search_window.destroyed.connect(loop.quit)  
        loop.exec()    
        self.close()    

############################################################################


class SearchWindow(QWidget):
    """
    Window for the user to input search queries.
    """
    
    def __init__(self, parent, tags_topics, preferences, history):
        super().__init__()
        self.parent = parent
        self.layout = QGridLayout(self) 
        self.tags_topics = tags_topics
        self.idx_to_tags = {}
        
        for key,val in self.tags_topics.items():
            self.idx_to_tags[val] = key
            
        self.preferences = preferences
        self.history = history
        self.set_window()
        self.define_widgets()
        self.nb_elements = 30 #max number of hits per query
        self.last_read = None #last doc read id

        self.spelling_corrector = Bigrams(new=False)
       
    def set_window(self):
        self.setWindowTitle("Search Window")
        self.setGeometry(300, 300, 600, 700)     
        self.setFixedWidth(600)
        self.setFixedHeight(700)        


    def define_widgets(self):
        self.layout.setColumnStretch(0,1)
        self.layout.setColumnStretch(1,2)
        self.layout.setColumnStretch(2,1)
        self.layout.setRowStretch(2,3)
        
        
        text = QLabel(text ="Query Search", parent = self)
        self.layout.addWidget(text, 0 ,0, alignment =Qt.AlignCenter)       
        
        self.text_input = QLineEdit(parent = self)
        self.text_input.setPlaceholderText('Use keywords')
        self.layout.addWidget(self.text_input, 0,1)
        
        self.search = QPushButton("Search", parent = self)
        self.search.clicked.connect(self.query_search)
        self.layout.addWidget(self.search, 0, 2)
        
        self.reco = QPushButton("News Recommendations", parent = self)
        self.reco.clicked.connect(self.recommendations)
        self.layout.addWidget(self.reco, 1, 1)
        
                
        self.stack = QStackedLayout()
        self.layout.addLayout(self.stack, 2,0,1,3)      
        
        self.list_search = QListWidget(parent = self)
        self.stack.addWidget(self.list_search)
        
        self.text_field = QTextEdit(self)
        self.text_field.setReadOnly(True)
        self.stack.addWidget(self.text_field)
        
        self.stack_prev = QStackedLayout()
        self.layout.addLayout(self.stack_prev, 1,0)    
        
        self.more_res = QPushButton("More results", parent = self)
        self.more_res.clicked.connect(self.more_results)
        self.stack_prev.addWidget(self.more_res)        
        self.more_res.hide()
        
        self.previous = QPushButton("Back", parent = self)
        self.previous.clicked.connect(self.text_to_list)
        self.stack_prev.addWidget(self.previous)
        
        self.update = QPushButton("Update", parent = self)
        self.update.clicked.connect(self.update_news)
        self.layout.addWidget(self.update, 1,2)
       
        self.like = QPushButton("Like", parent = self)
        self.like.clicked.connect(self.like_news)
        self.layout.addWidget(self.like, 3,2)
        self.like.hide()
        
        self.dislike = QPushButton("Dislike", parent = self)
        self.dislike.clicked.connect(self.dislike_news)
        self.layout.addWidget(self.dislike, 3,0)
        self.dislike.hide()
        
        
        quit = QPushButton("Quit", parent = self)
        quit.clicked.connect(self.menu)
        self.layout.addWidget(quit, 4,1)
        
       
        self.setLayout(self.layout)
        
    def menu(self):   
        self.parent.show()
        self.close() 
    
    def update_news(self):
        new_articles = news_updater.read_new_articles('ir/formated_dataset.json')
        # add the new articles to the database
        helpers.bulk(self.parent.client, new_articles, index="new_news")
        message = "Added " + str(len(new_articles)) + " new articles to the database"
        QMessageBox.about(self, "Update", message)
        
        return 0
       
    def like_news(self):
        self.liked = 1
        self.like.setStyleSheet('QPushButton {background-color: green;}')
        self.dislike.setStyleSheet('QPushButton {background-color: white;}')
        
    def dislike_news(self):
        self.liked = -1
        self.dislike.setStyleSheet('QPushButton {background-color: red;}')
        self.like.setStyleSheet('QPushButton {background-color: white;}')
        
    def reset_like(self):
        self.like.setStyleSheet('QPushButton {background-color: white;}')
        self.dislike.setStyleSheet('QPushButton {background-color: white;}')
        self.liked = 0
        
        
    def list_to_text(self):
        self.read = True  #to know when the user is done reading 
        self.stack_prev.setCurrentIndex(1)
        self.stack.setCurrentIndex(1)
        self.list_search.itemClicked.disconnect()
        self.more_res.hide()
        self.like.show()
        self.dislike.show()
        self.reset_like()
         
    def text_to_list(self):
        if self.last_read != None and self.read:
                self.add_history(self.last_read, self.liked)
        self.last_read = None           
        self.read = False
        self.stack_prev.setCurrentIndex(0)
        self.stack.setCurrentIndex(0)       
        self.list_search.itemClicked.connect(self.read_article)
        self.like.hide()
        self.dislike.hide()
        self.more_res.show()
        self.reset_like()    
        
    def more_results(self):
        self.text_field.clear()
        self.list_search.clear()
        for index, hit in enumerate(self.search.scan()):
            self.mem[index] = hit.meta.id
            QListWidgetItem(str(index) + " " + hit.headline , self.list_search)
        self.list_search.itemClicked.connect(self.read_article)
        
    def translate_preferences(self):
        pref_cat = {}
        for i in range(len(self.preferences)):
            if np.abs(self.preferences[i]) > 0 :
                pref_cat[self.idx_to_tags.get(i)] = self.preferences[i]
        return pref_cat
    
        
    def query_search(self):  
        self.text_to_list()
        self.text_field.clear()
        self.list_search.clear()
        search_query = self.text_input.text()
        if search_query == "":
            QMessageBox.about(self, "Warning", "No query input.")
            pass
        should_list = []
        preferences_categories = self.translate_preferences()  
        print("pref", preferences_categories)         
        for key, value in preferences_categories.items():
            if value > 2:
                should_list.append(Q("match", tags=key))
        
        list_search = search_query.split(" ")

        # only search for suggestions if the one word does not return results
        if len(list_search) == 1:
            query = Q('bool', must=[Q('match', headline=search_query)], should=should_list, minimum_should_match=0)
            query |= Q('bool', must=[Q('match', text=search_query)], should=should_list, minimum_should_match=0)
            self.search = Search(using=self.parent.client, index=self.parent.index).query(query)
            self.response = self.search[:self.nb_elements].execute() #restrict to nb_elements elements returned
            self.list_search.clear()
            # check if self.response is empty
            if len(self.response) == 0:
                suggestion = self.spelling_corrector.get_spelling_suggestions(tokens=list_search) # find suggested words, will only give alternatives if words are not present in the dataset
                suggestion = " ".join(suggestion)

                if suggestion != "" and suggestion != search_query:
                    QMessageBox.about(self, "Info", "Did you mean : " + suggestion + " ?")
                    search_query = suggestion
            else:
                search_query = list_search[0]
            
        else:
            suggestion = self.spelling_corrector.get_spelling_suggestions(tokens=list_search) # find suggested words, will only give alternatives if words are not present in the dataset
            suggestion = " ".join(suggestion)

            if suggestion != "" and suggestion != search_query:
                QMessageBox.about(self, "Info", "Did you mean : " + suggestion + " ?")
                search_query = suggestion

        print("should", should_list)
        query = Q('bool', must=[Q('match', headline=search_query)], should=should_list, minimum_should_match=0)
        query |= Q('bool', must=[Q('match', text=search_query)], should=should_list, minimum_should_match=0)
        self.search = Search(using=self.parent.client, index=self.parent.index).query(query)

        self.response = self.search[:self.nb_elements].execute() #restrict to nb_elements elements returned
        self.list_search.clear()
        self.mem = {} #stores articles ids
            
        for index, hit in enumerate(self.response):
            self.mem[index] = hit.meta.id
            QListWidgetItem(str(index) + " " + hit.headline + " | " + format(hit.meta.score, '.3f') , self.list_search)
            print(index, hit.tags)
        self.list_search.itemClicked.connect(self.read_article)
       
            
    def read_article(self, item):
        self.list_to_text()
        index = int(item.text().split(" ")[0])
        self.text_field.clear()
        self.text_field.insertPlainText(self.response[index].text)
        self.last_read = self.mem[index]
        print(self.mem[index])
        
    def add_history(self, news_id, liked):
        doc_tags = Document.get(news_id, using = self.parent.client, index=self.parent.index).tags
        doc_pref = tags_to_preferences(doc_tags)
        if liked ==1 or liked == 0 : 
            update_history(self.parent.client, "users", self.parent.username, news_id)
            doc_pref = [x *(liked +1) for x in doc_pref]
            self.history.append(news_id)   
        else : doc_pref = [-x for x in doc_pref]        
        update_preferences(self.parent.client, "users", self.parent.username, doc_pref)
        self.preferences =[ a + b for a,b in zip(self.preferences,doc_pref)]

   
    def recommendations(self):
        self.text_to_list()
        dislike = []
        artificial_read = []
        preferences_categories = self.translate_preferences()  
        for key, value in preferences_categories.items():
            if value < 0:
                dislike.append(Q("match", tags=key))
            elif value >=3:
                artificial_read.append(artificial_docs[key])                

        print("Dislike:",dislike)
        full_hist = artificial_read+self.history
        print(full_hist)
        
        q = Q()  
        for i, id in enumerate(reversed(full_hist)):
            if i == 0:
                q = Q(MoreLikeThis(like={"_index": self.parent.index, "_id": id.strip()}, fields=[
                  "tags", "authors", "headline","text"], min_term_freq=1, min_doc_freq=1, boost=pi/2-asin(i/len(full_hist))))  
            else:
                q |= Q(MoreLikeThis(like={"_index": self.parent.index, "_id": id.strip()}, fields=[
                   "tags", "authors", "headline", "text"], min_term_freq=1, min_doc_freq=1, boost=pi/2-asin(i/len(full_hist))))
        # https://stackoverflow.com/questions/66498900/filter-data-by-day-range-in-elasticsearch-using-python-dsl
        
        
        num_of_days = 365*2
        date_limit = Q("range",date={"gte": "now-%dd" % num_of_days,"lt": "now" })
        

        if len(dislike)>0 :self.search = Search(using=self.parent.client, index=self.parent.index).query(date_limit)\
        .query(q).query(Q('bool', must_not=dislike))
        else : self.search = Search(using=self.parent.client, index=self.parent.index).query(date_limit).query(q)

        
        self.response = self.search[:self.nb_elements].execute()
        self.list_search.clear()
        self.mem = {} #stores articles ids
        with open("evaluation/eval_"+self.parent.username, 'w') as f:
            for index, hit in enumerate(self.response[:10]):
                self.mem[index] = hit.meta.id
                QListWidgetItem(str(index) + " " + hit.headline + " (" + hit.date + ") | " + format(hit.meta.score, '.3f') , self.list_search)
                f.write(str(index) + " " + hit.headline+ " - " + str(hit.tags) +"-\n")
                print(index, hit.tags)
        
        
        self.list_search.itemClicked.connect(self.read_article)
       
      
############################################################################


app = QApplication(sys.argv)

gui_new_user = MainWindow(tags_elastic_search,"http://localhost:9200", "new_news" )
gui_new_user.show()
  
# Run application's main loop
sys.exit(app.exec_())

