import sys  
import os
import numpy as np
import json


from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.query import MoreLikeThis
from math import asin, pi
from search import query, recommendation

import json


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


# [{"user":"0", "preferences":[]}] : users.json default

def check_user(filename, username):
    """ 
    Checks if the input username already exists in the user base.
    """
    with open(filename, 'r') as f:
        data = json.load(f)  
        for entry in data:  
            if entry["user"] == username : return True, entry["preferences"]
        f.close()
    return False, None
    
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
        json.dump(entry, f, separators=(',',': '))
        f.write(']')
        f.close() 
    
    

class MainWindow(QWidget):  
    """
    Main window. Login / Create user window.
    """  

    def __init__(self, tags_topics, address, user_fl, index ):
        super().__init__()
        self.layout = QGridLayout(self) 
        self.set_window()
        self.define_widgets()    
        self.username = "" 
        self.tags_topics = tags_topics
        self.client =  Elasticsearch(address)
        self.filename = user_fl 
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
            pass
        
        status, self.preferences  = check_user(self.filename, self.username)
        if not status :  
            self.hide()
            self.ld_window = PreferencesWindow(self, self.tags_topics)
            self.ld_window.show()
            loop = QEventLoop()
            self.ld_window.setAttribute(Qt.WA_DeleteOnClose)
            self.ld_window.destroyed.connect(loop.quit)
            loop.exec() 
        
        else :
            self.search_window = SearchWindow(self, self.tags_topics, self.preferences)
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
        self.setFixedWidth(500)
        self.setFixedHeight(300)         


    def define_widgets(self):
        
        ok = QPushButton("Confirm", parent = self)
        ok.clicked.connect(self.forward)

        self.buttons = []         
        max_abs = 4       
        fct = []
        for i in range(len(self.tags_topics)):
            fct.append(partial(self.preference, i))
            
        for i in range(len(self.tags_topics)):
            self.buttons.append(QPushButton(self.tags_topics[i], parent = self))
            u = i // max_abs
            v = i % max_abs
            self.buttons[i].clicked.connect(fct[i])
            self.layout.addWidget(self.buttons[i], u, v)
            
        self.layout.addWidget(ok, len(self.tags_topics) // max_abs + 2, 3)
        self.setLayout(self.layout)
    
    
    def preference(self, k):  
        idx = self.tags_topics.index(self.buttons[k].text())
        if self.preferences[idx] == 0 :
            self.preferences[idx] = 1
            self.buttons[k].setStyleSheet('QPushButton {background-color: green;}')
        elif self.preferences[idx] == 1 :
            self.preferences[idx] = -1   
            self.buttons[k].setStyleSheet('QPushButton {background-color: red;}')     
        else : # -1
            self.preferences[idx] = 0
            self.buttons[k].setStyleSheet('QPushButton {background-color: white;}') 
        
            
    def forward(self):
        if np.linalg.norm(self.preferences) < 3 :
            QMessageBox.about(self, "Cold start !", "Select at least 3 positive preferences.")
            pass
            
        write_user(self.parent.filename, self.parent.username, list(self.preferences))
        self.parent.search_window = SearchWindow(self.parent, self.tags_topics, self.preferences)
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
    TODO : implement recommendation without query
    TODO : add read articles to history (should add it to json user)
    """
    def __init__(self, parent, tags_topics, preferences):
        super().__init__()
        self.parent = parent
        self.layout = QGridLayout(self) 
        self.tags_topics = tags_topics
        self.preferences = preferences
        self.set_window()
        self.define_widgets()

       
    def set_window(self):
        self.setWindowTitle("Search Window")
        self.setGeometry(300, 300, 600, 700)     
        self.setFixedWidth(600)
        self.setFixedHeight(700)        


    def define_widgets(self):
        text = QLabel(text ="Query Search", parent = self)
        self.layout.addWidget(text, 0 ,0)
       
        
        self.text_input = QLineEdit(parent = self)
        self.text_input.setPlaceholderText('Use keywords')
        self.layout.addWidget(self.text_input, 0,1)
        
        self.search = QPushButton("Search", parent = self)
        self.search.clicked.connect(self.query_search)
        self.layout.addWidget(self.search, 0, 2)
                
        self.stack = QStackedLayout()
        self.layout.addLayout(self.stack, 1,1)      

        self.text_field = QTextEdit(self)
        self.text_field.setReadOnly(True)
        self.stack.addWidget(self.text_field)
        
        self.list_search = QListWidget(parent = self)
        self.stack.addWidget(self.list_search)
        
        self.previous = QPushButton("Previous", parent = self)
        self.previous.clicked.connect(self.prev_list)
        self.layout.addWidget(self.previous, 1, 2)
        self.previous.hide()
        
        
        quit = QPushButton("Quit", parent = self)
        quit.clicked.connect(self.menu)
        self.layout.addWidget(quit, 4,0)
        
       
        self.setLayout(self.layout)
        
    def menu(self):   
        self.parent.show()
        self.close() 
        
    def prev_list(self):
        self.previous.hide()
        self.stack.setCurrentIndex(1)
        self.list_search.itemClicked.connect(self.read_article)
         
      
    
    def translate_preferences(self):
        pref_cat = {}
        for i in range(len(self.preferences)):
            if self.preferences[i] > 0 :
                pref_cat[self.tags_topics[i]] = self.preferences[i]
        return pref_cat
    
        
    def query_search(self):  
        self.previous.hide()
        self.stack.setCurrentIndex(1)

        self.text_field.clear()
        search_query = self.text_input.text()
        if search_query == "":
            QMessageBox.about(self, "Warning", "No query input.")
            pass
        should_list = []
        preferences_categories = self.translate_preferences()           
        for key, value in preferences_categories.items():
            if value > 2:
                should_list.append(Q("match", tags=key))

        self.searches = Search(using=self.parent.client, index=self.parent.index).query(Q('bool', must=[Q('match', headline=search_query)], should=should_list, minimum_should_match=0)).execute()
        self.list_search.clear()
        self.mem = {}
        fcts = []
        for i in range(len(self.searches)):
            fcts.append(partial(self.read_article, i))
            
        for index, hit in enumerate(self.searches):
            self.mem[index-1] = hit.meta.id
            QListWidgetItem(str(index) + " " + hit.headline , self.list_search)
        
        self.list_search.itemClicked.connect(self.read_article)
       
            
    def read_article(self, item):
        self.previous.show()
        self.stack.setCurrentIndex(0)
        index = int(item.text().split(" ")[0])
        self.list_search.itemClicked.disconnect()
        self.text_field.clear()
        self.text_field.insertPlainText(self.searches[index-1].text)

       
        
        
        
        
    
############################################################################


app = QApplication(sys.argv)
tags = ["politics", "wellness", "entertainment", "travel", "style & beauty", "parenting", "healthy living", "queer voices", "food & drink", "business", "comedy", "sports", "black voices", "home & living", "parents"]
gui_new_user = MainWindow(tags,"http://localhost:9200", "users.json", "new_news" )
gui_new_user.show()
  
# Run application's main loop
sys.exit(app.exec_())

