from BeautifulSoup import BeautifulStoneSoup
import sys
import os
sys.path.append('data')

from google.appengine.ext import db

class Review(db.Model):
	review = db.StringProperty(required=True)
	label = db.StringProperty(required=True)

class words(db.Model):
	probPos = db.FloatProperty()
	probNeg = db.FloatProperty()

def encode():
	file = open(os.getcwd()+'/utils/data/reviews.xml','r');
	soup = BeautifulStoneSoup(file.read())
	
	# Find all the reviews extracted from XML
	allreviewsTags = soup.findAll('review')
	reviews = [review.contents for review in allreviewsTags]

	# Extract all the distinct words from the reviews to train NaiveBayes classifier
	vocabulary = []
	train_labels = [review['class'] for review in allreviewsTags]
	train_data_docIds = [review['doc_id'] for review in allreviewsTags]

	# Going through each review extract distinct words and add them to vocabulary
	for eachReview in reviews:
		words = []
		words.append(eachReview[0])
		words = " ".join(words)
		words = words.split()
		vocabulary.extend(words)
	vocabulary = sorted(set(vocabulary))

	train_data = []
	i = 0
	for each in reviews:
		doc_id = train_data_docIds[i]
		doc_words = reviews[int(doc_id)-1][0]
		doc_words = doc_words.split()
		words = []
		words.append(each[0])
		words = " ".join(words)
		words = words.split()
		words = set(words)
		for word in words:
			row = str(i+1)+" "
			word_index = vocabulary.index(word)
			row = row+str(word_index+1)+" "
			word_count = doc_words.count(word)
			row = row+str(word_count)
			train_data.append(row)
		i = i+1
    

	return vocabulary,train_labels,train_data

