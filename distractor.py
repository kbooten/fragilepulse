import enchant
spell = enchant.Dict("en_US")

from nltk.corpus import wordnet as wn
wn.synsets('dog.n.1')
import requests
from nltk import pos_tag,tokenize,ngrams
import distance
import random

from nltk.corpus import stopwords
stops = stopwords.words('english')
stops += ['nothing',"I'm","getting","having","need"] ## custom stops to deal with my sentence templates

import json
with open('words.json','r') as f:
    words = json.load(f)
words = [w for w in words if "_" not in w]
words = [w for w in words if w.istitle()!=w]
words = [w for w in words if spell.check(w)]

with open('amazon_sents.json','r') as f:
    i_need_statements = json.load(f)
i_need_statements = [i for i in i_need_statements if len(i)<100]
i_need_statements = [i for i in i_need_statements if i.count('.')==1]

import gensim
### need to have some word vectors for gensim...the ones I'm using are too big for github. 
model = gensim.models.KeyedVectors.load_word2vec_format("somevectors.bin", binary=True) 

with open('noun2adj.json','r') as f:
    noun2adj = json.load(f)

with open('adj2noun.json','r') as f:
    adj2noun = json.load(f)

with open('noun2verb.json','r') as f:
    noun2verb = json.load(f)


import tweepy
### ADD CREDENTIALS
auth = tweepy.OAuthHandler("???","???")
auth.set_access_token("???","???")
api = tweepy.API(auth)

class Distractor:
    
    def __init__(self):
        self.current_focus = None
        self.distractions = [
                            self.make_what_if_based_on_noun,
                            self.get_similar_orthography_word,
                            self.make_depressed_sentence_based_on_adj,
                            self.make_depressed_sentence_based_on_noun,
                            self.get_similar_word2vec_word, 
                            self.get_tweet, 
                            self.get_consumerist_statement,
                            ]
        self.used = []

    def _test_chunk(self,p):
        if p[0][1].startswith("NN"):
            return False
        if p[0][1].isalpha()==False:
            return False
        if p[-1][1].isalpha()==False:
            return False
        if p[0][0].isalpha()==False:
            return False
        if p[-1][1].startswith("NN")==False:
            return False
        if "." in [t for to,t in p]:
            return False
        if ":" in [t for to,t in p]:
            return False
        return True
        
        
    def _simple_chunking(self,astring,minimum=3,maximum=10):
        tagged = pos_tag(tokenize.casual_tokenize(astring))
        allpossible = []
        for n in range(minimum,maximum):#len(tagged)-maxminus):
            allpossible+=list(ngrams(tagged,n))

        ok = [c for c in allpossible if self._test_chunk(c)]
        return ok
    
    
    def  _get_ok_words(self,astring,justnouns=False):
        if justnouns:
            oktags = ["NN","NNS"]
        else:
            oktags = ['NN',"VB","JJ","AD","NNS"]
        okwords = [token for token,tag in pos_tag(tokenize.casual_tokenize(astring)) if tag[:2] in oktags]
        okwords = [token for token in okwords if token not in stops]
        okwordsstrict = [token for token in okwords if spell.check(token)]
        if okwordsstrict!=[]:
            return okwordsstrict
        else:
            return okwords


    def _get_word_closest_to_words(self,listofwords,words=["terrible","pain"]):
        word_score_tuples = []
        for w in words:
            for t in listofwords:
                try:
                    word_score_tuples.append((t,model.similarity(w,t)))
                except:
                    pass
        word_score_tuples.sort(key=lambda x: x[1], reverse=True)
        return word_score_tuples[0][0]
    
    
    def return_focus(self):
        return self.current_focus
        
        
    def focus_on_word_from_string(self,astring):
        try:
            okwords = self._get_ok_words(astring)
            print(okwords)
            self.current_focus= random.choice([w for w in okwords if w not in self.used])
            self.used.append(self.current_focus)
        except:
            print("randomword")
            self.current_focus = random.choice(words)
            self.used.append(self.current_focus)


    def _get_n_closest_levenshtein(self,target,n=15):
        wordsample = random.sample(words,10000)
        sample_with_scores_tuple = [(w,distance.levenshtein(target,w)) for w in wordsample]
        sample_with_scores_tuple.sort(key=lambda x: x[1])
        return [w for w,tup in sample_with_scores_tuple][:n]

    
    def get_similar_orthography_word(self):            
        orthosims = self._get_n_closest_levenshtein(self.current_focus)
        orthosims = [w for w in orthosims if w.istitle()==False]
        orthosims = [w for w in orthosims if "_" not in w]
        closest_word_by_semantic_dist = self._get_word_closest_to_words(orthosims)
        return closest_word_by_semantic_dist
    
    
    def _narrow_focus(self):
        self.focus_on_word_from_string(self.current_focus)
               

    def convert_to_string(self,nonstring):
        try:
            return " ".join([token for token,tag in nonstring])
        except:
            postagged,author = nonstring
            astring = " ".join([token for token,tag in postagged])
        return astring
            
    


    def get_focus(self):
        focus = self.current_focus
        if type(focus) in [str]:
            return focus
        else:
            return self.convert_to_string(focus)



    def get_similar_word2vec_word(self):
        similar_words = [w for w,t in model.most_similar(self.current_focus,topn=10)]
        similar_words = [w for w in similar_words if w.istitle()==False]
        similar_words = [w for w in similar_words if "_" not in w]
        return self._get_word_closest_to_words(similar_words)


    def make_depressed_sentence_based_on_noun(self):
        noun=self.current_focus
        adj = random.choice(noun2adj[noun])
        sentence = "I'm nothing but a %s %s" % (adj,noun)
        return sentence

    def make_depressed_sentence_based_on_adj(self):
        adj=self.current_focus
        noun = random.choice(adj2noun[adj])
        sentence = "I'm nothing but a %s %s" % (adj,noun)
        return sentence


    def make_what_if_based_on_noun(self):
        noun=self.current_focus
        verb = random.choice(noun2verb[noun])
        sentence = "What if a %s %ss me?" % (noun,verb)
        return sentence


    def get_tweet(self):
        
        def test_tweet(atweetstring):
            loweredstring = atweetstring.lower()
            if "http" in loweredstring:
                return False
            if 'twitter' in loweredstring:
                return False
            if '@' in loweredstring:
                return False
            # if any(bw in loweredstring for bw in bannedwords):
            #     return False
            return True    

        stub = random.choice(['😥','😫','😔','😰'])
        tweets = api.search('"%s"+"%s"  -filter:retweets -filter:safe'%(stub,self.current_focus),lang='en',count=100)
        tweets = [t for t in tweets if " "+self.current_focus+" " in t.text]
        tweets = [t.text for t in tweets if (t.truncated==False)]
        tweets = [t for t in tweets if test_tweet(t)]
        tweets = [t for t in tweets if len(t)<100]
        tweets.sort(key=len)
        return random.choice(tweets[:3])



    def get_consumerist_statement(self):
        return random.choice([s for s in i_need_statements if self.current_focus in s])

    

    def become_distracted(self,tofocuson=None):
        needstochange = self.current_focus
        if tofocuson!=None:
            self.current_focus = tofocuson
            self._narrow_focus
        if (type(self.current_focus) in [str,] and len(tokenize.casual_tokenize(self.current_focus))==1):
            random.shuffle(self.distractions)
            for d in self.distractions:
                try:
                    print (d)
                    new_focus = d()
                    self.current_focus = new_focus
                    break
                except:
                    pass
        else:
            self._narrow_focus()
        if needstochange==self.current_focus:
            self.current_focus = random.choice(words)



def main():
    mydistraction = Distractor()
    mydistraction.become_distracted("I'm nothing but a weak excuse.")
    for i in range(6):
        focus = mydistraction.get_focus()
        print(focus)
        mydistraction.become_distracted()
        print()


if __name__ == '__main__':
    main()
                    