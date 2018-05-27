from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
from datetime import date
#!/usr/bin/python
import geocoder
import MySQLdb
from math import radians, cos, sin, asin, sqrt
import datetime

app = Flask(__name__)

@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
  global verified
  # Create a Cursor object to execute queries.
  # Initialize database
  db = init_db()

  # Get the message the user sent our Twilio number
  body = request.values.get('Body', None)
  body = body.lower()
  # Start our TwiML response
  phonenumber = request.values.get('From', None)
  cur = db.cursor()
  cur.execute("SELECT ssn FROM patients.active_customers WHERE phone_number = " + phonenumber) #Get SSN
  SSN = cur.fetchone()[0]
  cur.execute("SELECT usr_id FROM patients.active_customers WHERE phone_number = " + phonenumber) #Get usr_id
  usr_id = cur.fetchone()[0]

  # Get the message the user sent our Twilio number
  body = request.values.get('Body', None)
  body = body.lower()
  resp = MessagingResponse()

  # Determine the right reply for this message
  if body == 'refill prescription':
      cur.execute("SELECT usrname FROM patients.active_customers WHERE phone_number = " + phonenumber) #Get usrname
      usrname = cur.fetchone()[0]
      resp.message("Hello " + str(usrname) + ". Please enter the last 4 digits of your social security "
                      "# and what prescription you need (#### drug_name)")
  elif len(body) > 4 and body != 'refill prescription': #Confirm SSN is correct
          socialnum, prescript = body.split(" ")
          if(str(SSN) == socialnum): #Verifies SSN
              #Search for prescript
              cur.execute("SELECT prescription_name FROM patients.prescription WHERE usr_id = " + str(usr_id)) #Get drug names
              prescript_list = cur.fetchmany()

              matches = (x for x in prescript_list if prescript == str(x))
              if matches is None:
                  resp.message("Not a valid prescription")
                  quit()
              #toBeRefilled = matches[0]

              cur.execute("SELECT prescript_id FROM patients.prescription "
                          "WHERE prescription_name = '" + str(prescript) + "'") #Get unique prescription ID
              prescript_id = cur.fetchone()[0]
              #prescript_id = 1

              cur.execute("SELECT fill_left FROM patients.prescription "
                          "WHERE prescript_id = " + str(prescript_id)) #Get numbers of fills left
              fill_left = cur.fetchone()[0]

              cur.execute("SELECT copay FROM patients.prescription "
                          "WHERE prescript_id = " + str(prescript_id)) #Get copay
              copay = cur.fetchone()[0]

              cur.execute("SELECT last_fill FROM patients.prescription "
                          "WHERE prescript_id = " + str(prescript_id)) #Get last fill date
              #last_fill = cur.fetchone()[0]
              today = datetime.datetime.now()
              #days_apart = (today-last_fill).days

              #Verify that the prescription can be filled
              #if(days_apart < 30):
                  #resp.message("It has not been 30 days since your last refill")
                  #quit()
              if(fill_left < 1):
                  resp.message("No fills remaining")
                  quit()

              cur.execute("SELECT address FROM patients.active_customers "
                          "WHERE usr_id = '" + str(usr_id) + "'") #Get user address
              address = str(cur.fetchone()[0])

              cur.execute("SELECT pharmacy FROM patients.active_customers "
                          "WHERE usr_id = '" + str(usr_id) + "'") #Get pharmacy address
              pharm_address = str(cur.fetchone()[0])
          else:
              resp.message("Not verified")
              quit()

          g = geocoder.google(str(pharm_address))
          userloc2 = g.latlng
          h = geocoder.google(str(address))
          pharm2 = h.latlng
          userloc2[1], userloc2[0], pharm2[1], pharm2[0] = map(radians, [userloc2[1], userloc2[0], pharm2[1], pharm2[0]])

          dlon = pharm2[1] - userloc2[1]
          dlat = pharm2[0] - userloc2[0]
          a = sin(dlat/2)**2 + cos(userloc2[0]) * cos(pharm2[0]) * sin(dlon/2)**2
          c = 2 * asin(sqrt(a))
          k = 6371 #Use 3956 for milesw
          #print(dis)
          dis = c * k
          rated = 1.15
          tme = dis/rated
          time = str(tme)

          resp.message("Thank you! Your refill of " + str(prescript) + " is on the way. "
                                                       "Your copay of $" + str(copay) + " will be charged to your account.")
          resp.message("It will take approximately " + str(round(tme)) + " minutes for your refill to arrive.")

         # cur.execute("UPDATE patients.prescription SET last_fill = " + str(today) + ", "
                                                #"fill_left = " + str(fill_left-1) + " WHERE prescript_id = " + str(prescript_id))


  return str(resp)

def init_db():
    database = MySQLdb.connect(
                     host="localhost",  # your host
                     user="root",       # username
                     passwd="password",     # password
                     db="patients")   # name of the database
    return database;


if __name__ == "__main__":
 app.run(debug=True)