from pymongo import MongoClient
url="mongodb://localhost:27017/"
client=MongoClient(url)
db=client.dhi_analytics
#print(client.list_database_names())
def get_academic_year():
    dhi_internal = db.dhi_internal
    academicyear=dhi_internal.aggregate([{"$group":{"_id":"null","academicyear":{"$addToSet":"$academicYear"}}},{"$project":{"academicyear":"$academicyear","_id":0}}])
    for year in academicyear:
        year=year['academicyear']
    return year

def get_term():
  term = db.dhi_term_detail.find_one({"degreeId":"BE"})
  termType=[]
  for sem in term["academicCalendar"]:
        termType.append(sem["termName"])
  termType.sort()
  return termType