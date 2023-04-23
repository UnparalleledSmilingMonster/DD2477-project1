import sys  
import os
import numpy as np
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
from PyQt5.QtCore import QEventLoop
from PyQt5.QtCore import Qt



class MainWindow(QWidget):    

    def __init__(self, tags_topics):
        super().__init__()
        self.layout = QGridLayout(self) 
        self.set_window()
        self.define_widgets()    
        self.username = "" 
        self.tags_topics = tags_topics
                
        
    def set_window(self):
        self.setWindowTitle("New user")
        self.setGeometry(200, 200, 600, 700)     
        self.setFixedWidth(600)
        self.setFixedHeight(700)  


    def define_widgets(self):
    
        button_next = QPushButton("Next", parent = self)
        button_next.clicked.connect(self.forward)
        self.layout.addWidget(button_next, 1,1)
       
        
        button_quit = QPushButton("Quit", parent = self)
        button_quit.clicked.connect(self.close)
        self.layout.addWidget(button_quit, 4,2)   
        
        text = QLabel(text ="Pick a username", parent = self)
        self.layout.addWidget(text, 0 ,0)

        self.text_input = QLineEdit(parent = self)
        self.layout.addWidget(self.text_input, 0 ,1, 1,-1)
    
        
        self.setLayout(self.layout)

    
    def forward(self):
        self.username = self.text_input.text()
        if self.username == "":
            QMessageBox.about(self, "Warning", "No name provided.")
        else :   
            self.ld_window = PreferencesWindow(self, self.tags_topics)
            self.ld_window.show()
            self.ld_window.preferences_list()
            loop = QEventLoop()
            self.ld_window.setAttribute(Qt.WA_DeleteOnClose)
            self.ld_window.destroyed.connect(loop.quit)
            loop.exec()         
    
        
############################################################################


class PreferencesWindow(QWidget):
    def __init__(self, parent, tags_topics):
        super().__init__()
        self.parent = parent
        self.layout = QGridLayout(self) 
        self.set_window()
        self.tags_topics = tags_topics
        self.preferences = np.zeros(len(tags_topics))
       
    def set_window(self):
        self.setWindowTitle("User preferences")
        self.setGeometry(350, 550, 500, 300)
        self.setFixedWidth(500)
        self.setFixedHeight(300)         


    def preferences_list(self):
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
        self.close()
        return self.parent.username, self.preferences
        
    def cancel(self):
        self.close()
        self.parent.cancel = True


        



app = QApplication(sys.argv)

gui_new_user = MainWindow(["politics", "wellness", "entertainment", "travel", "style & beauty", "parenting", "healthy living", "queer voices", "food & drink", "business", "comedy", "sports", "black voices", "home & living", "parents"])
gui_new_user.show()
  
# Run application's main loop
sys.exit(app.exec_())

