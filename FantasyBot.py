#importing modules
import time
import praw
import urllib2
import json
import csv
from bs4 import BeautifulSoup
from pprint import pprint





#declare global variables
bot_username = "FantasyBot"
bot_password = "Fanta5y99"
is_PPR_scoring = False




#define classes
class Athlete(object):
    name = ""
    position = ""
    team = ""
    small = ""

    def __init__(self, info):
        self.name = info[0 : info.find("(") - 1]
        self.position = info[info.find("(") + 1 : info.find("-") - 1]
        self.team = info[info.find("-") + 2 : info.find(")")]
        self.small = self.name.replace(' ', '-').replace('.', '').lower()











# ----
# ----
# ----
# Define functions
# ----
# ----
# ----


#must only be one player and/or team on each side of the OR/VS
#formats accepted:
# 1  [WDIS] ________ or ________
# 2  [WDIS] ________ vs ________
# 3  [WDIS] ________ vs. ________
# 4  [WDIS] ________ vs ___ or ________ vs ___
# 5  [WDIS] ________ vs. ___ or ________ vs. ___



def loopThroughWDISPosts():
	submissions = r.get_subreddit('fantasyfootball').search("title:WDIS", sort='new', limit=25)

	#loop through all submissions
	for post in submissions:

		#print available posts
		#pprint(vars(post))
		print "----------------------------------------------------------------"
		print post
		print "----------------------------------------------------------------"

		#loop through
		if isValidTitle(post):
			if shouldCommentBePosted(post):
			
				#get final ranking URL
				finalRankingInfo = gatherTitleInfo(post)

				print "Ranking Info: %s" % finalRankingInfo
				print "\n"

					
				#test if error and complete bot function
				if finalRankingInfo != "error":
					
					#create comment message
					final_comment = constructComment(finalRankingInfo)
					#post.add_comment(final_comment)


				#end of post
				print "----------------------------------------------------------------"
				print "\n"
				print "\n"

			else:
				break







def loopThroughOfficialWDISThreads():
	submissions = r.get_subreddit('fantasyfootball').search("title:OFFICIAL WDIS THREAD", sort='new', limit=5)

	#loop through all submissions
	for post in submissions:

		#print available posts
		#pprint(vars(post))
		print "----------------------------------------------------------------"
		print post
		print "----------------------------------------------------------------"






def isValidTitle(post):
	title_text = post.title.lower()
	title_split = title_text.split()


	#get first six chars and test
	firstSixChars = title_text[0:6]
	wdis_terms = ['[wdis]', 'wdis: ', '(wdis)', 'wdis--', 'wdis -']
	has_wdis_term = any(string in title_text for string in wdis_terms)


	#test for compare terms
	compare_terms = ['vs', 'or', 'vs.']
	has_compare_term = any(string in title_split for string in compare_terms)


	#is it valid?
	if has_wdis_term and has_compare_term:
		return True
	else:
		return False
	







def gatherTitleInfo(post):
	print "\nEntering: gatherTitleInfo() function"


	title_text = post.title.lower()
	title_split = title_text.split()

	
	#declare vars
	replace_terms = ['.', ',', '@', '(', ')', '?', '!']
	compare_terms = ['vs', 'or']
	compare_term_count = 0
	compare_term_count_indexes = []
	athlete1List = []
	athlete2List = []
	athlete1 = ""
	athlete2 = ""
	rankingInfo = ""
	

	#remove wdis term
	del title_split[0]


	#HACK: return error if more than 3 commas
	if title_text.count(',') >= 2:
		return "error"


	#remove common words and characters
	for term in replace_terms:
		title_split = [word.replace(term,'') for word in title_split]


	#test for ppr or standard terms
	global is_PPR_scoring
	is_PPR_scoring = isPPRScoring(title_split)


	#loop through terms
	for term in compare_terms:
		compare_term_count += title_split.count(term) #count up term count

		if term in title_split:	#get term indices
			compare_term_count_indexes.append(title_split.index(term))
	

	#slice out whats before and after the compare term
	if compare_term_count == 1:
		athlete1List = title_split[0:compare_term_count_indexes[0]]
		athlete2List = title_split[compare_term_count_indexes[0] + 1:]

		athlete1_string = " ".join(map(str, athlete1List))
		athlete2_string = " ".join(map(str, athlete2List))

		#print athlete1_string
		#print athlete2_string

		athlete1_info = getAthleteInfo(athlete1_string, 'left')
		athlete2_info = getAthleteInfo(athlete2_string, 'right')

		print "Athlete 1 Info: %s" % athlete1_info
		print "Athlete 2 Info: %s" % athlete2_info

		if athlete1_info is not None and athlete2_info is not None:
			rankingInfo = getRankingURL(athlete1_info, athlete2_info)
		else:
			rankingInfo = "error"

	elif compare_term_count == 3:
		athlete1List = title_split[0:compare_term_count_indexes[1]]
		athlete2List = title_split[compare_term_count_indexes[1] + 1:]

		athlete1_string = " ".join(map(str, athlete1List))
		athlete2_string = " ".join(map(str, athlete2List))

		print athlete1_string
		print athlete2_string

		rankingInfo = "error"
	
	else:
		rankingInfo = "error"
	

	#return final values
	return rankingInfo






def isPPRScoring(list):
	print "\nEntering isPPRScoring(%s) function" % list

	ppr_terms = ['PPR', 'ppr']
	non_ppr_terms = ['Non-PPR', 'non-ppr', 'no ppr', 'non ppr']
	
	has_ppr_term = any(string in list for string in ppr_terms)
	has_non_ppr_term = any(string in list for string in non_ppr_terms)

	#test values
	print "has_ppr_term: %s" % has_ppr_term
	print "has_non_ppr_term: %s" % has_non_ppr_term

	if has_ppr_term and not has_non_ppr_term:
		return True
	else:
		return False






def getAthleteInfo(string, position):
	#start outside, and go in
	print "\nEntering: getAthleteInfo(%s, %s) function" % (string, position)


	#declare values
	final_name = ""
	searchURL = "http://www.fantasypros.com/ajax/search-nfl.php?term="
	data_length = 0
	loop_int = 0
	data = []
	results = []


	#split name into list
	name_list = string.split()


	#check initial response and length
	while data_length == 0:
		
		#remove items if second or more loop
		if loop_int != 0 and len(name_list) > 1:
			if position == "left":
				del name_list[0]
			elif position == "right":
				print "Name List Length: %s" % len(name_list)
				del name_list[len(name_list) - 1]

		elif loop_int != 0 and len(name_list) == 1:
			return


		#turn list into string
		name_string = " ".join(map(str, name_list)).lower()


		#check if string includes nickname
		print "Nickname Loop"
		with open('assets/nicknames.csv', mode='r') as f:
			reader = csv.reader(f)
			for index, row in enumerate(reader):
				nickname = row[0].lower()
				has_nickname = nickname in name_string

				if has_nickname:
					name_string = row[1].lower()

					print "nickname: %s" % nickname
					print "name_string: %s" % name_string
					print "has_nickname: %s" % has_nickname
					print index, row

					break


		#put together request
		reqURL = searchURL + name_string.replace(' ', '+')
		print "Request URL: %s" % (reqURL)
		req = urllib2.Request(reqURL)


		#attempt request and read results
		resp = urllib2.urlopen(req)
		data = resp.read()

		if data:
			results = json.loads(data)
			data_length = len(results)
		

		#increment loop int
		loop_int += 1


		#if loop_int gets too big cancel everything
		if loop_int > 10:
			return

		#print data
		print "Loop int: %s" % loop_int
		print "Name string: %s" % name_string
		print "Results: %s" % results
		print "Results length: %s" % data_length
		

	#test length
	if data_length == 1:
		final_name = results[0]['label']

	elif data_length > 1:
		final_name = getHighestRankingAthlete(results)

	#print final name
	print "Final Name: %s" % final_name
	print "\n"

	#turn response into Athlete Class
	return Athlete(final_name)










def getHighestRankingAthlete(data):
	print "Entering: getHighestRankingAthlete(%s) function" % data


	#define vars
	athlete_list = data
	highestRank = 300
	bestPlayer = ""


	#create list of athletes
	for index, item in enumerate(athlete_list):
		#print "Index: %s" % index
		#print "Item: %s" % item

		label = item['label']
		name = label[0 : label.find("(") - 1]
		pos = label[label.find("(") + 1 : label.find("-") - 1]
		rank = scrapeAthleteRank(name, pos)
		athlete_list[index]['rank'] = rank

		#print "Athlete Rank: %s" % rank

	print "Athlete Results: %s" % athlete_list


	#get highest rank and return as result
	for player in athlete_list:
		print "Name: %s, Rank: %s" % (player['label'], player['rank'])
		if player['rank'] != 'N/A':
			if int(player['rank']) < highestRank:
				highestRank = int(player['rank'])
				bestPlayer = player['label']


	#make sure bestPlayer exists
	if not bestPlayer:
		bestPlayer = athlete_list[0]['label']
		print "No players had a ranking. Going with the default."


	#return final athlete
	return bestPlayer










def scrapeAthleteRank(name, pos):
	print "Entering: scrapeAthleteRank(%s, %s) function" % (name, pos)
	
	#declare vars
	playerRank = "N/A"
	pos = pos.lower()
	site_body = ""


	#put together requests
	url = 'http://www.fantasypros.com/nfl/rankings/%s.php' % pos
	req = urllib2.Request(url)


	#attempt request and handle exceptions
	try:
	    resp = urllib2.urlopen(req)
	except urllib2.URLError, e:
		if e.code == 404:
			print "404 ERROR"
		else:
			print "DIFF ERROR"
	else:
		print "SUCCESS!"
		site_body = resp.read()


	#create soup
	soup = BeautifulSoup(site_body)

	#navigate DOM
	playerText = soup.find(text=name)
	print "Player Text Found: %s" % playerText

	#check if player is on page, if so get rank
	if playerText:
		playerRow = playerText.findParents('tr')[0]
		#print "Player Row <tr>: %s" % playerRow

		playerRank = playerRow.find('td').string
		#print "player Rank #: %s" % playerRank
	

	#return rank
	return playerRank











def getRankingURL(player1, player2):
	print "Entering: getRankingURL() function"

	#declare vars
	URLBase = "http://www.fantasypros.com/nfl/start/"
	passThru = 0
	statusURL = "empty1"
	pageURL = "empty2"

	#construct function
	while statusURL != pageURL:
		if passThru == 0:
			pageURL = URLBase + player1.small + "-" + player2.small + ".php"
		elif passThru == 1:
			pageURL = URLBase + player1.small + "-" + player1.team.lower() + "-" + player2.small + ".php"
		elif passThru == 2:
			pageURL = URLBase + player1.small + "-" + player2.small + "-" + player2.team.lower() + ".php"
		elif passThru == 3:
			pageURL = URLBase + player1.small + "-" + player1.team.lower() + "-" + player2.small + "-" + player2.team.lower() + ".php"
		else:
			pageURL = "error"
			#print "URL cannot be found"
			break

		# // url status
		#print "Testing again... "
		status = urllib2.urlopen(pageURL)
		statusURL = status.url
		#pprint(vars(status))

		print "URL Being attempted: %s" % pageURL
		print "URL Being returned: %s" % statusURL
		print "On attempt #: %s" % passThru

		# // increment pass thru
		passThru += 1
	

	#add ppr filter if not qb
	print "Is PPR scoring? %s" % is_PPR_scoring
	print "Player 1 pos: %s" % player1.position.lower()
	if is_PPR_scoring and player1.position.lower() != 'qb':
		pageURL += "?scoring=PPR"

	#scrape rankings from page
	chosenPlayerInfo = getPickPercentage(player1, player2, pageURL)

	#add url to rankings
	chosenPlayerInfo['url'] = pageURL

	#clean up
	passThru = 0

	#complete
	return chosenPlayerInfo




def getPickPercentage(player1, player2, rankURL):
	print "Entering: getPickPercentage(%s, %s, %s) function" % (player1, player2, rankURL)
	
	#declare vars
	site_body = ""
	final_vals = [{
		'player': player1.name,
		'perct': 0
	},{
		'player': player2.name,
		'perct': 0
	}]


	#put together request
	req = urllib2.Request(rankURL)


	#attempt request and handle exceptions
	try:
	    resp = urllib2.urlopen(req)
	except urllib2.URLError, e:
		if e.code == 404:
			print "404 ERROR"
		else:
			print "DIFF ERROR"
	else:
		print "SUCCESS!"
		site_body = resp.read()


	#create soup
	soup = BeautifulSoup(site_body)


	#navigate DOM ---- #picks -> .wsis-summary -> .right-col[0] & .right-col[1]
	rankings = soup.select('#picks .wsis-summary .label-rank')
	print "Picks DIV: %s" % rankings


	#look through both picks
	for index, pick in enumerate(rankings):
		perct = int(pick.get_text().strip('%'))
		final_vals[index]['perct'] = perct

	print "Final Vals: %s" % final_vals


	#grab the higest ranked and return
	if final_vals[0]['perct'] > final_vals[1]['perct']:
		return final_vals[0]
	else:
		return final_vals[1]





def shouldCommentBePosted(post):
	print "Entering: shouldCommentBePosted() function"

	#declare vars
	should_post_comment = True

	#get flattened comments
	post_comments = praw.helpers.flatten_tree(post.comments)

	#loop through comments and confirm FantasyBot hasn't already posted
	for comment in post_comments:
		#pprint(vars(comment))
		print "Comment Author Name: " + comment.author.name
		if comment.author.name == bot_username:
			should_post_comment = False
			break

	#test results
	# TODO: If this returns true, we should break the loop
	print "Should comment been posted? %s" % should_post_comment
	
	#return result
	return should_post_comment









def constructComment(info):
	#check league type
	leagueType = "Standard"
	if is_PPR_scoring:
		leagueType = "PPR"

	#put together message
	message = "Based on FantasyPros data, **%d%%** of experts pick **%s** in a %s format. [View more details here](%s). \n *** \n I am a bot that posts FantasyPros matchups on [WDIS] threads. Please PM me if you have comments/suggestions/feedback." % (info['perct'], info['player'], leagueType, info['url'])
	
	#print message
	print "Comment will say: " + message
	
	#return to add to reddit
	return message








# ----
# ----
# ----
# Connect to reddit
# ----
# ----
# ----

user_agent = ("FantasyBot 0.1 provides fantasypros.com comparisons for those asking WDIS in /r/fantasyfootball. Bot by /u/atomstore")
r = praw.Reddit(user_agent=user_agent)
r.login(bot_username, bot_password)











# ----
# ----
# ----
# Loop through and do everything
# ----
# ----
# ----
while True:

	#loop through WDIS posts
	loopThroughWDISPosts()


	#loop through OFFICIAL WDIS threads
	#loopThroughOfficialWDISThreads()


	#post finish time and wrap up
	print "\n\n"
	print "Finished at: %s" % time.ctime()
	print "----------------------------------------------------------------"
	print "----------------------------------------------------------------"
	print "----------------------------------------------------------------"
	print "----------------------------------------------------------------"
	print "\n\n\n\n"


	#wait some time and go again
	time.sleep(300)






