import webapp2
import os
import jinja2
import numpy as np
import sys
sys.path.append('utils')
import utils.encodeReviews as encodeReviews

from google.appengine.ext import db

jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

class words_raw(db.Model):
    vocab = db.StringProperty(required = True)
    word_index = db.IntegerProperty(required = True)

class words_and_labels(db.Model):
    word = db.StringProperty(required = True)
    poslab = db.IntegerProperty(required = True)
    neglab = db.IntegerProperty(required = True)

class BuildClassifier(webapp2.RequestHandler):
  def get(self):
  	# Loading training data and setting number of words and labels
    [words_voc, train_labels, train_data] = encodeReviews.encode();
    no_of_words = len(words_voc)
    no_of_docs = len(train_labels)
    train_labels = np.array(train_labels)
    no_of_labels = np.unique(np.array(train_labels)).size
    
    # Setting laplacian constant
    laplacian = 1.0

    # Building words vs Labels matrix
    words_labels = np.zeros((no_of_words,no_of_labels))
    for i in range(no_of_labels):
    	words = np.zeros((no_of_words,1))
    	doc_ids = np.where(train_labels == i+1)[0]
        for j in range(doc_ids.size):
            index = doc_ids[j]
            indices = list(np.where(train_data[:,0] == index)[0])
            words[list(train_data[indices,1]),0] = [(x+y) for x,y in zip(words[list(train_data[indices,1])].reshape(-1).tolist(),list(train_data[indices,2]))]
    	words_labels[:,i] = words.reshape(-1,).tolist()
    
    # Storing the values of words_labels into the database
    for i in range(words_labels.shape[0]):
        w = words_and_labels(word = words_voc[i],poslab = int(words_labels[i,0]),neglab = int(words_labels[i,1]))
        w.put()

    # Storing the words into the database
    for each in words_voc:
        v = words_raw(vocab = each,word_index = words_voc.index(each))
        v.put()


    values = {'words':words,'train_labels':train_labels,'train_data':train_data,'word_labels':words_labels}
    template = jinja_environment.get_template('words.html')
    self.response.out.write(template.render(values))


class Classifier(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template('classifier.html')
    self.response.out.write(template.render())


app = webapp2.WSGIApplication([('/classifier', Classifier),('/classifier/build',BuildClassifier)],
                              debug=True)
