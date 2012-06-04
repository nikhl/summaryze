from BeautifulSoup import BeautifulStoneSoup
import sys
import os
import numpy as np
import re
sys.path.append('data')

from google.appengine.ext import db

def make_pretty(text):
	review_text = re.sub(r"[-./@?#!+\\=^`_$&%;:><\\\",\\(\\)\\*]"," ",text)
	review_text = re.sub(r"[-'~]","",review_text)
	review_text = re.sub(r'[\d]',"",review_text)
	review_text = re.sub(r'[\\\[\\\]\\\{\\\}]',"",review_text)
	review_text = ' '.join(review_text.split())
	return review_text

def lowercase(l):
	temp = [each.lower() for each in l]
	return temp

def remove_stop_words(vocab,stopfile):
	# handling the stop words
	stop_handler = open(stopfile,'r').read()
	stop_handler = stop_handler.split()
	stop_handler = " ".join(stop_handler)
	stop_handler = stop_handler.split()
	stop_handler = lowercase(stop_handler)
	vocab = sorted(set(vocab) - set(stop_handler))
	return vocab



def encode():

	# training data file in the form on XML
	file = open(os.getcwd()+'/utils/data/reviews.xml','r');
	stopfile = os.getcwd()+'/utils/data/stopwords.txt';
	soup = BeautifulStoneSoup(file.read())
	
	# Find all the reviews extracted from XML
	allreviewsTags = soup.findAll('review')
	reviews = [review.contents[0] for review in allreviewsTags]

	# Extract all the distinct words from the reviews to train NaiveBayes classifier
	vocabulary = []
	train_labels = [int(review['class']) for review in allreviewsTags]
	train_data_docIds = [review['doc_id'] for review in allreviewsTags]

	# Going through each review extract distinct words and add them to vocabulary
	for eachReview in reviews:
		words = []
		words.append(make_pretty(eachReview))
		words = words[0].split()
		vocabulary.extend(words)
	vocabulary = lowercase(vocabulary)
	vocabulary = remove_stop_words(vocabulary,stopfile)
	
	train_data = np.zeros((1,3))
	flag = True
	i = 0
	for each in reviews:
		doc_id = train_data_docIds[i]
		doc_words = reviews[int(doc_id)-1]
		doc_words = doc_words.split()
		doc_words = lowercase(doc_words)
		words = []
		words.append(make_pretty(each))
		words = " ".join(words)
		words = words.split()
		words = lowercase(words)
		words = remove_stop_words(words,stopfile)
		for word in words:
			row = str(i+1)+" "
			word_index = vocabulary.index(word)
			row = row+str(word_index+1)+" "
			word_count = doc_words.count(word)
			row = row+str(word_count)
			if flag:
				train_data[0,0] =  i
				train_data[0,1] =  word_index
				train_data[0,2] =  word_count
				flag = False
			else:
				train_data = np.vstack([train_data,[i,word_index,word_count]])
		i = i+1
    

	return vocabulary,train_labels,train_data

