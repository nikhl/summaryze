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

class Review(db.Model):
  review = db.StringProperty(required = True)
  created = db.DateTimeProperty(auto_now_add = True)

class MainPage(webapp2.RequestHandler):
  def get(self):
    template_values = {'name':'Nikhil','verb':'love'}
    template = jinja_environment.get_template('index.html')
    self.response.out.write(template.render(template_values))

class AllReviews(webapp2.RequestHandler):
  def get(self):
    reviews = db.GqlQuery("Select * from Review Order By created Desc")
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

class AddReview(webapp2.RequestHandler):
  def get(self):
    template = jinja_environment.get_template('addreview.html')
    self.response.out.write(template.render())

class Delete(webapp2.RequestHandler):
  def get(self):
    q = db.GqlQuery("SELECT * FROM Review")
    results = q.fetch(10)
    db.delete(results)

class EncodeReviews(webapp2.RequestHandler):
  def get(self):
    [words, train_labels, train_data] = encodeReviews.encode();
    values = {'words':words,'train_labels':train_labels,'train_data':train_data}
    template = jinja_environment.get_template('words.html')
    self.response.out.write(template.render(values))


app = webapp2.WSGIApplication([('/', MainPage),('/addreview',AddReview),('/encodeReviews',EncodeReviews),('/allreviews',AllReviews),('/delete',Delete)],
                              debug=True)
