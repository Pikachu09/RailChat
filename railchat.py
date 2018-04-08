import os
import time
import json
import unicodedata
import requests
import re
from slackclient import SlackClient

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "current status of train <train number>"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
PAGE_ACCESS_TOKEN = "nmcd43yqf0"

def parse_bot_commands(slack_events):
	for event in slack_events:
		if event["type"] == "message" and not "subtype" in event:
			#print "anything"
			user_id, message = parse_direct_mention(event["text"])
			if user_id == starterbot_id:
				return message, event["channel"]
	return None, None

def parse_direct_mention(message_text):
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)




def train_det(c, channel):
	response = None
	nex=0
	for word in c:
		
		if word=='train':
			nex=1
			continue
		if nex==1:
			train=word
			break
	return train
def live_status(c, channel, train):
	try:
		url = "https://api.railwayapi.com/v2/live/train/"+train+"/date/"+c+"/apikey/"+PAGE_ACCESS_TOKEN+"/"
		rep = requests.get(url)	
		#r = rep.json()
		#r = unicodedata.normalize('NFKD', r).encode('ascii','ignore')	
		
		r = json.loads(rep.text)
		
	except Exception as ex:
		response = "Train number is ivalid."
		return response

	stns= len(r["route"])
	
	for i in range(stns):
		if r["route"][i]["has_arrived"]== True:
			if r["route"][i]["has_departed"]== False:
				#print r["route"][i]
				r["route"][i]={k:r["route"][i][k] for k in r["route"][i] if (k!="no" and k!= "has_arrived" and k!= "has_departed")}
				r["route"][i]["station"]= str(r["route"][i]["station"]["name"]+" ("+r["route"][i]["station"]["code"]+")")
				lab=r["route"][i].keys()
				#print lab
				stat=r["route"][i].values()
				#print stat            
				if i==stns-1:
					response="Train has reached destination."                
				else:
					response="Train is at the platform."
				for j in range(1,len(lab)):
					response=response+"\n"+str(lab[j])+"\t:\t"+str(stat[j])
				break
		elif r["route"][i]["has_departed"]== False:
			if i==0:
				response="Train has not started yet."                
			else:
				#print r["route"][i-1]
				response="*Train is running.*\n *Departed from:* "            
				r["route"][i-1]={k:r["route"][i-1][k] for k in r["route"][i-1] if (k!="no" and k!= "has_arrived" and k!= "has_departed")}
				r["route"][i-1]["station"]= str(r["route"][i-1]["station"]["name"]+" ("+r["route"][i-1]["station"]["code"]+")")
				lab=r["route"][i-1].keys()
				stat=r["route"][i-1].values()
				break
        
        if lab:
	
		for j in range(1,len(lab)):
			response=response+"\n*"+str(lab[j])+"*\t:\t"+str(stat[j])    
    
        return response    
    

   # Sends the response back to the channel


def seat_avail(c, channel):
	response=None
	nex=0
	for word in c:
		
		if word=='train':
			nex=1
			continue
		elif word == 'from':
			nex=2
			continue
		elif word == 'to':
			nex=3
			continue
		elif word == 'on':
			nex=4
			continue

		if nex==1:
			train=word
			nex=0
			continue
		if nex==2:
			src=word
			nex=0
			continue
		if nex==3:
			dest=word
			nex=0
			continue
		if nex==4:
			date=word
			nex=0
			continue
	#print train, src, dest, date
	slack_client.api_call("chat.postMessage",channel=channel,text="What would you prefer?\n First AC (1C)\n Second AC (2A)\n , Third AC (3A)\n Sleeper Class (SL) \n First Class (FC)\n Air Conditioned Chair Car (CC) \n Second Seating (2S) \n\n Tell me the class code given in brackets  ")
	return train, src,dest, date

def seat2(c, channel, pref, train, src, dest, date):
	
		
	try:
		url = "https://api.railwayapi.com/v2/check-seat/train/"+str(train)+"/source/"+str(src)+"/dest/"+str(dest)+"/date/"+str(date)+"/pref/"+str(pref)+"/quota/"+str(c)+"/apikey/"+PAGE_ACCESS_TOKEN+"/"
		
		rep = requests.get(url)	
		#r = rep.json()
		#r = unicodedata.normalize('NFKD', r).encode('ascii','ignore')	
		
		r = json.loads(rep.text)
		#print r
	except Exception as ex:
		response = "Sorry, Invalid query. Check train number and respective codes again."
		return response
	

	r["train"]= str(r["train"]["name"])+" ("+str(r["train"]["number"])+")"
	r["from"]= str(r["from_station"]["name"])+" ("+str(r["from_station"]["code"])+ ")"
	r["to"]= str(r["to_station"]["name"])+" ("+str(r["to_station"]["code"])+ ")"
	r["journey_class"]= str(r["journey_class"]["name"])+" ("+str(r["journey_class"]["code"])+")"
	r["quota"]= str(r["quota"]["name"])+" ("+str(r["quota"]["code"])+")"
	l=r["availability"]
	response=str("*Train:* "+r["train"]+"\n*From:* "+r["from"]+"\n*To:* "+r["to"]+"\n*Journey Class:* "+r["journey_class"]+"\n*Quota:* "+r["quota"]+"\n\n*Availability:* \n*Date:* \t\t\t\t *Status:* ")
	for i in range(len(l)):
		response=response+"\n"+l[i]["date"]+" \t\t "+l[i]["status"]
	return response

def pnr(c,channel):
	nex=0
	for word in c:
		
		if word=='pnr' or word=='PNR':
			nex=1
			continue
		if nex==1:
			pnr=word
			break
		
	try:
		url = "https://api.railwayapi.com/v2/pnr-status/pnr/"+pnr+"/apikey/"+PAGE_ACCESS_TOKEN+"/"
		rep = requests.get(url)	
		#r = rep.json()
		#r = unicodedata.normalize('NFKD', r).encode('ascii','ignore')	
		
		r = json.loads(rep.text)
		
	except Exception as ex:
		response = "Invalid pnr."
		return response
	r["from_station"]=str(r["from_station"]["name"])+" ("+str(r["from_station"]["code"])+")"
	r["to_station"]=str(r["to_station"]["name"])+" ("+str(r["to_station"]["code"])+")"
	r["boarding_point"]=str(r["boarding_point"]["name"])+" ("+str(r["boarding_point"]["code"])+")"
	r["train"]=str(r["train"]["name"])+" ("+str(r["train"]["number"])+")"
	r["journey_class"]=str(r["journey_class"]["name"])+" ("+str(r["journey_class"]["code"])+")"

	response=" *pnr:* "+str(r["pnr"])+"\n*date of journey:* "+str(r["doj"])+"\n*total passengers:* "+str(r["total_passengers"])+"\n*chart prepared:* "+str(r["chart_prepared"])+"\n*From:* "+r["from_station"]+"\n*To:* "+r["to_station"]+"\n*Boarding Point:* "+r["boarding_point"]+"\n*Train:* "+r["train"]+"\n*Journey Class:* "+r["journey_class"]+"\n*Ticket Details:* \nNo.\t\t*Current_stat*\t\t\t\t*Booking_stat*"
	l=r["passengers"]
	for i in range(len(l)):
		response=response+"\n"+str(l[i]["no"])+"\t\t"+str(l[i]["current_status"])+"\t\t\t\t"+str(l[i]["booking_status"])
	return response

if __name__ == "__main__":
	if slack_client.rtm_connect(with_team_state=False):
		print("Starter Bot connected and running!")
       # Read bot's user ID by calling Web API method `auth.test`
		starterbot_id = slack_client.api_call("auth.test")["user_id"]
		se=0
		cu=0
		response=None
		while True:
			command, channel = parse_bot_commands(slack_client.rtm_read())
			if command:
				default_response = "Not sure what you mean. Try format *{}*.".format(EXAMPLE_COMMAND)  				
				c=map(str,command.split())
			#print c
				if "current" in c:
					cu=1
					se=0
					train= train_det(c, channel)
					slack_client.api_call("chat.postMessage",channel=channel,text="Which date did the train start? (dd-mm-yyyy)")
				elif cu==1:
					cu=0
					c=''.join(c)
					response = live_status(c, channel, train)
					slack_client.api_call("chat.postMessage",channel=channel,text=response or default_response)
				elif "pnr" in c:
					se=0
					cu=0
					response=pnr(c,channel)
					slack_client.api_call("chat.postMessage",channel=channel,text=response or default_response)
				elif "seat" in c:
					se=1
					cu=0
					train, src, dest, date =seat_avail(c, channel)

				elif se==1:
					se=2
					slack_client.api_call("chat.postMessage",channel=channel,text="Which quota? Tell me the quota code  ")
					pref=''.join(c)
				elif se==2:
					se=0
					c=''.join(c)
					response = seat2(c, channel, pref, train, src, dest, date)
					slack_client.api_call("chat.postMessage",channel=channel,text=response or default_response)
				else:
					se=0
					slack_client.api_call("chat.postMessage",channel=channel,text=response or default_response)
				time.sleep(RTM_READ_DELAY)
		
	else:
		print("Connection failed. Exception traceback printed above.")
