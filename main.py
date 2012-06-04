import webapp2
import os
import hashlib
import hmac
import jinja2
import sys
import logging
import classifier
import numpy as np
sys.path.append('utils')
import utils.encodeReviews as encodeReviews
SECRET = 'TooSecret'
import time

from xml.dom.minidom import Document
from BeautifulSoup import BeautifulStoneSoup
from google.appengine.ext import db
from google.appengine.api import memcache

# For hashing the cookie functionality
def hash_str(text):
  return hmac.new(SECRET,text).hexdigest()

def make_secure_val(text):
  return '%s|%s' % (text,hash_str(text))

def check_secure_val(h):
  value = h.split('|')[0]
  if h == make_secure_val(value):
    return value

jinja_environment = jinja2.Environment(autoescape=True,
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')))

class Review(db.Model):
  review = db.StringProperty(required = True)
  label = db.StringProperty(required = True)
  created = db.DateTimeProperty(auto_now_add = True)

class MainPage(webapp2.RequestHandler):
  def get(self):
    visits = 0
    visit_cookie_val = self.request.cookies.get('visits')
    if visit_cookie_val:
      cookie_val = check_secure_val(visit_cookie_val)
      if cookie_val:
        visits = int(cookie_val)

    visits += 1
    new_cookie_val = make_secure_val(str(visits))
    self.response.headers.add_header('Set-Cookie','visits=%s' % new_cookie_val)
    template_values = {'visits':check_secure_val(new_cookie_val)}
    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render(template_values))

def read_reviews(update = False):
  key = 'all_reviews'
  temp_reviews = memcache.get(key)
  if temp_reviews is None or update:
    logging.error("database Query")
    temp_reviews = db.GqlQuery("Select * from Review Order By created Desc")
    memcache.set(key,temp_reviews)
  temp_reviews = list(temp_reviews)
  return temp_reviews

class AllReviews(webapp2.RequestHandler):
  def get(self):
    update = self.request.get('update')
    if update == "true":
      reviews = read_reviews(True)
    else:
      reviews = read_reviews()
    values = {'reviews':reviews}
    template = jinja_environment.get_template('allreviews.html')
    self.response.out.write(template.render(values))

  def post(self):
    review = self.request.get('reviewContent').strip()
    if review:
      r = Review(review = review)
      r.put()
      self.redirect("/allreviews")
    else:
      error = "Please enter your review"
      template = jinja_environment.get_template('addreview.html')
      self.response.out.write(template.render({'error':error}))  

def form_xml(reviews):
  doc = Document()
  reviews_xml = doc.createElement("reviews")
  doc.appendChild(reviews_xml)

  for eachReview in reviews:
    review = doc.createElement("review")
    if (eachReview.label == 'Positive'):
        review.setAttribute("label", "1")
    else:
        review.setAttribute("label", "2")
    temp = eachReview.review.strip()
    rtext = doc.createTextNode(temp)
    review.appendChild(rtext)
    reviews_xml.appendChild(review)

  return doc


class ApiAllReviews(webapp2.RequestHandler):
  def get(self):
    reviews = read_reviews()
    reviews = list(reviews)
    xml_doc = form_xml(reviews)
    self.response.headers['Content-Type'] = 'text'
    self.response.out.write(xml_doc.toprettyxml(indent=""))

  def post(self):
    review = self.request.get('reviewContent').strip()
    if review:
      r = Review(review = review)
      r.put()
      self.redirect("/allreviews")
    else:
      error = "Please enter your review"
      template = jinja_environment.get_template('addreview.html')
      self.response.out.write(template.render({'error':error}))  

def read_words_raw():
  key = 'all_words'
  words = memcache.get(key)
  if words is None:
    words = db.GqlQuery("Select * from words_raw")
    memcache.set(key,words)
  return words

def read_words_labels():
  key = 'all_words_labels'
  words_labels = memcache.get(key)
  if words_labels is None:
    words_labels = db.GqlQuery("Select * from words_and_labels")
    memcache.set(key,words_labels)
  return words_labels


class AddReview(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template('addreview.html')
    self.response.out.write(template.render())

  def post(self):
    # Preparing labels
    train_labels = ['Positive','Negative']
    review = self.request.get('reviewContent').strip()

    words_values = read_words_raw()
    words = [each.vocab for each in words_values]

    # Function for getting the index of word
    def get_word_index(word):
      return int(words.index(word))

    # Preparing the test data from review
    #stopfile = os.getcwd()+'/utils/data/stopwords.txt';
    test_voc = []
    test_voc.append(review)
    test_voc = " ".join(test_voc)
    test_voc = test_voc.split()
    test_voc = encodeReviews.lowercase(test_voc)
    #test_voc_set = encodeReviews.remove_stop_words(test_voc,stopfile)
    test_voc_set = set(test_voc)


    st_time = time.time()
    test_data = np.array([[0,0,0]])
    init_flag = True
    for test_word in test_voc_set:
      if test_word in words:
        word_index = words.index(test_word)
        word_count = test_voc.count(test_word)
        if init_flag:
          test_data[0,0] =  1
          test_data[0,1] =  word_index
          test_data[0,2] =  word_count
          init_flag = False
        else:
          test_data = np.vstack([test_data,[1,word_index,word_count]])
    end_time = time.time()
    #print 'time took 1',(end_time - st_time)
    # Retrieving the classifier values from database
    classifier_values = read_words_labels()
    words_labels = np.zeros((1,3))
    flag = 0
    counter = 0

    st_time = time.time() 
    for each in classifier_values:
      if flag == 0:
        words_labels[0,0] = get_word_index(classifier_values[0].word)
        words_labels[0,1] = classifier_values[0].poslab
        words_labels[0,2] = classifier_values[0].neglab
        flag = 1
      else:
        words_labels = np.vstack([words_labels,[get_word_index(classifier_values[counter].word),classifier_values[counter].poslab,classifier_values[counter].neglab]])
      counter = counter + 1
    end_time = time.time()
    #print 'time took 2',(end_time - st_time)

    # Setting Laplacian constant
    laplacian = 1.0

    # Classifying a new Review i.e posteriors
    posteriors_combined = np.zeros([1,2])
    st_time = time.time() 
    # calculating probabilities
    word_ids = test_data[:,1]
    for j in range(2):
      posteriors_combined[0,j] = (np.log((words_labels[word_ids,j+1] + laplacian)/((words_labels[:,j+1]).sum() + (laplacian * len(words))) + (1/2))).sum()
    end_time = time.time()
    #print 'time took 3',(end_time - st_time)
    predicted = posteriors_combined.argmax(axis = 1)[0] + 1
    #print posteriors_combined
    r = Review(review = review,label = train_labels[predicted-1])
    r.put()
    #print train_labels[predicted-1]
    self.redirect('/allreviews?update=true');



class Delete(webapp2.RequestHandler):
  def get(self):
    q = db.GqlQuery("SELECT * FROM words_raw")
    results = q.fetch(10)
    db.delete(results)

class Signup(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template('signup.html')
    self.response.out.write(template.render())


app = webapp2.WSGIApplication([('/', MainPage),('/addreview',AddReview),('/allreviews',AllReviews),('/api/allreviews.xml',ApiAllReviews),('/delete',Delete),('/signup',Signup)],
                              debug=True)
