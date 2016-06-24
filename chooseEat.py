from Tkinter import *
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from rdflib.namespace import DC, FOAF
chooseeat = Namespace("http://chooseeat.org/vocabulary#")
import time
import re
from SPARQLWrapper import SPARQLWrapper, JSON
g = Graph()
time = time.time()
time = str(time)
# Create an identifier to use as the subject for the user.
user = URIRef('https://chooseeat.org/user/'+time)

#Global variables for the user information
top = Tk()
firstName = StringVar()
lastName = StringVar()
age = StringVar()
drug = StringVar()
Eemail = StringVar()

#Userinterface
def userInterface():

	top.configure(background='white')
	top.wm_title("ChooseEAT")

	#Introduction
	Lintro1 = Label(top, text="Hello!", fg='white', bg='#FF5252').pack(fill=X)
	Lintro2 = Label(top, text=" If you fill in the following information about yourself,", 
		fg='white', bg='#FF5252').pack(fill=X)
	Lintro3 = Label(top, text=" this application will help you to find", 
		fg='white', bg='#FF5252').pack(fill=X)
	Lintro4 = Label(top, text=" your best matching dish from a restaurant according to your personal condition. ", 
		fg='white', bg='#FF5252').pack(fill=X)

	#First name entry
	L1 = Label(top, text=" First name", fg='#4B4747', bg='white').pack(fill=X)
	E1 = Entry(top, bd =6, textvariable=firstName, fg='#4B4747').pack(ipadx=75)

	#second name entry
	Lln = Label(top, text="Last name", fg='#4B4747', bg='white').pack(fill=X)
	Eln = Entry(top, bd=6, textvariable=lastName, fg='#4B4747').pack(ipadx=75)

	#email entry
	Lemail = Label(top, text="email adress", fg='#4B4747', bg='white').pack(fill=X)
	Email = Entry(top, bd=6, textvariable=Eemail, fg='#4B4747').pack(ipadx=75)

	"""
	#Gender listbox
	L2 = Label(top, text="What is your gender?")
	L2.pack()
			  
	Lb1 = Listbox(top, selectmode= SINGLE, height = 2, exportselection=0)
	Lb1.insert(1, "male")
	Lb1.insert(2, "female")
	Lb1.pack()
	"""

	#age entry
	L3 = Label(top, text="What is your age?", fg='#4B4747', bg='white').pack(fill=X)
	E2 = Entry(top, bd =6, textvariable=age, fg='#4B4747').pack(ipadx=75)

	#The drugs the user is using
	Ldrugs = Label(top, text="Type in which drug you use; ", 
		fg='white', bg='#FF5252').pack(fill=X)
	Lexamples = Label(top, text="For example: Paracetamol, Hydrocodone, Simvastatin", 
		fg='white', bg='#FF5252').pack(fill=X)
	Lexamples2 = Label(top, text=" Lisinopril, or any other drug.", 
		fg='white', bg='#FF5252').pack(fill=X)
	LNo = Label(top, text=" If you don't use any drugs, type: No", 
		fg='white', bg='#FF5252').pack(fill=X)
	Edrugs = Entry(top, bd=6, textvariable=drug, 
		fg='#4B4747').pack(ipadx=75)

	#Ok button
	B = Button(top, text = "Ok", command=storeInformation, fg='white', bg='#FF5252').pack()

	top.mainloop()

#stores the user information in an RDF Graph
def storeInformation():	
	firstname = firstName.get()
	lastname = lastName.get()
	#genderr = gender.get(gender.curselection())
	agee = age.get()
	agee = float(agee)
	email = Eemail.get()
	drugs = drug.get()
	drugURI = getDrugURI(drugs)
	top.destroy()
	# Add triples using store's add method.
	g.add( (user, RDF.type, FOAF.Person) )
	g.add( (user, FOAF.givenName, Literal(firstname)) )
	g.add( (user, FOAF.familyName, Literal(lastname)) )
	#g.add( (user, FOAF.gender, Literal(gender)) )
	g.add( (user, FOAF.age, Literal(agee)) )
	g.add( (user, FOAF.mbox, URIRef("mailto:"+email)) )
	if drugURI != "invalidDrug":
		g.add( (user, chooseeat.takeDrug, URIRef(drugURI)) )

	# For each foaf:Person in the store print out its mbox property.
	print("--- printing mboxes ---")
	for person in g.subjects(RDF.type, FOAF.Person):
	    for mbox in g.objects(person, FOAF.mbox):
	        print(mbox)
	print( g.serialize(format='n3') )

	# Bind a few prefix, namespace pairs for more readable output
	g.bind("dc", DC)
	g.bind("foaf", FOAF)

#takes a drug name as parameter and returns its drugURI
def getDrugURI(drug):
	drug = '"%s"'%drug
	sparql = SPARQLWrapper("http://wifo5-03.informatik.uni-mannheim.de/drugbank/sparql")
	sparql.setQuery("""
	    PREFIX drugbank: <http://wifo5-04.informatik.uni-mannheim.de/drugbank/resource/drugbank/>
	    PREFIX drug: <http://wifo5-04.informatik.uni-mannheim.de/drugbank/resource/drugs/>
		SELECT distinct ?drug 
		WHERE { 
		       OPTIONAL {?drug drugbank:genericName """+drug+"""}
		       OPTIONAL {?drug drugbank:synonym """+drug+""" }
		       OPTIONAL {?drug drugbank:label """+drug+"""}
 		}
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()   
	for result in results["results"]["bindings"]:
		if result == {}:
			return "invalidDrug"
		else:
			drugUri = result["drug"]["value"]
			return drugUri 

#takes the URI of the user as parameter, returns 
def makeDiet():
	addDietPersonalInformation()
	addDietDrugIntake()

# adds diet restrictions to the users diet from the personal information database
def addDietPersonalInformation():
	for s, p, o in g:
		if not (s, p, o) in g:
			raise Exception("Iterator / Container Protocols are Broken!!")
	for s,p,o in g.triples( (user, FOAF.age, None) ):
		ageCategory = calculateAgeCategory(o)
		less, more, forbidden = dietRecomendation(ageCategory)
	for nutrient in less:
		g.add( (user, chooseeat.less, Literal(nutrient)) )
	for nutrient in more:
		g.add( (user, chooseeat.more, Literal(nutrient)) )
	for ingredient in forbidden:
		g.add( (user, chooseeat.forbidden, Literal(ingredient)) )

# adds diet restrictions to the users diet related to the drugs it uses
def addDietDrugIntake():
	interactions = []
	for s,p,o in g.triples( (user, chooseeat.takeDrug, None) ):
		interactions = foodInteractions(o)
		for element in interactions:
			if "alcohol" in element:
				g.add( (user, chooseeat.forbidden, Literal("alcohol")) )

		# For each foaf:Person in the store print out its mbox property.
	print("--- printing mboxes ---")
	for person in g.subjects(RDF.type, FOAF.Person):
	    for mbox in g.objects(person, FOAF.mbox):
	        print(mbox)
	print( g.serialize(format='n3') )

	# Bind a few prefix, namespace pairs for more readable output
	g.bind("dc", DC)
	g.bind("foaf", FOAF)

# chooses a restaurant
def chooseRestaurant():
	restaurant = "<https://chooseeat.org/restaurant/1>"
	return restaurant

#Takes a list with recipe URI's as parameter, returns a list 
# with their recipe names.
def findDishNames(orderedDishes):
	dishNameList = []
	sparql = SPARQLWrapper("http://localhost:5820/restaurants/query")
	for dish in orderedDishes:
		sparql.setQuery("""
			PREFIX chooseeat:<http://chooseeat.org/vocabulary/>
			PREFIX schema:<http://schema.org/>
			select distinct ?dishName
			where { 
					<"""+dish+"""> chooseeat:recipeName ?dishName .
				}
		""")
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		for result in results["results"]["bindings"]:
			dishName = result["dishName"]["value"]
			dishNameList.append(dishName)
	return dishNameList


#takes ageCategory as parameter, returns diet lists less, more and forbidden
def dietRecomendation(ageCategory):
	needLessNutrition = []
	needMoreNutrition = []
	forbiddenIngredients = []
	ageCategory = '"%s"'%ageCategory
	sparql = SPARQLWrapper("http://localhost:5820/chooseEatData/query")
	sparql.setQuery("""
		PREFIX chooseeat:<http://chooseeat.org/vocabulary/>
		select distinct ?s ?moreNutrition ?lessNutrition ?forbiddenIngredient
		where { 
			?s chooseeat:targetAge """ +ageCategory+ """ ; 
			OPTIONAL {?s chooseeat:needMoreOfNutrition ?moreNutrition }
			OPTIONAL {?s chooseeat:needLessOfNutrition ?lessNutrition }
			OPTIONAL {?s chooseeat:forbiddenIngredient ?forbiddenIngredient }
		}
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	for result in results["results"]["bindings"]:
		if result.has_key("lessNutrition"):
			less = result["lessNutrition"]["value"]
			needLessNutrition.append(less)
		if result.has_key("moreNutrition"):
			more = result["moreNutrition"]["value"]
			needMoreNutrition.append(more)
		if result.has_key("forbiddenIngredient"):
			forbidden = result["forbiddenIngredient"]["value"]
			forbiddenIngredients.append(forbidden)

	return needLessNutrition, needMoreNutrition, forbiddenIngredients

#takes a drugURI as input and returns a list with the drug foodinteractions.
def foodInteractions(drugURI):
	foodInteractions = []
	sparql = SPARQLWrapper("http://wifo5-03.informatik.uni-mannheim.de/drugbank/sparql")
	sparql.setQuery("""
	    PREFIX drugbank: <http://wifo5-04.informatik.uni-mannheim.de/drugbank/resource/drugbank/>
		PREFIX drug: <http://wifo5-04.informatik.uni-mannheim.de/drugbank/resource/drugs/>
		SELECT distinct ?foodInteraction 
		WHERE { <"""+drugURI+"""> drugbank:foodInteraction ?foodInteraction }
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()

	for result in results["results"]["bindings"]:
	    foodInteractions.append(result["foodInteraction"]["value"])
	return foodInteractions

# returns a list with all recipes from the chosen restaurant and
# returns another list with recipes that contain forbidden ingredients.
def selectRecipes():
	restaurant = chooseRestaurant()
	recipes = getRecipes(restaurant)
	forbiddenIngredient = "nothing"
	forbiddenRecipes = []
	for recipe in recipes:
		ingredientList = []
		sparql = SPARQLWrapper("http://localhost:5820/restaurants/query")
		sparql.setQuery("""
			PREFIX chooseeat:<http://chooseeat.org/vocabulary/>
			PREFIX schema:<http://schema.org/>
			select distinct ?ingredient
			where { 
					<"""+recipe+"""> schema:recipeIngredient ?ingredient .
				}
		""")
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		for result in results["results"]["bindings"]:
			ingredient = result["ingredient"]["value"]
			ingredientList.append(ingredient)
		for element in ingredientList:
			if "wine" in element or "alcohol" in element or "beer" in element:
				for s,p,o in g.triples( (user, chooseeat.forbidden, None) ):
					forbiddenIngredient = o
					if recipe in recipes:
						forbiddenRecipes.append(recipe)
						recipes.remove(recipe)
	return recipes, forbiddenRecipes

#returns all the recipe URI's from the given restaurant URI
def getRecipes(restaurant):
	recList = []
	sparql = SPARQLWrapper("http://localhost:5820/restaurants/query")	
	sparql.setQuery("""
		PREFIX chooseeat:<http://chooseeat.org/vocabulary/>
		PREFIX schema:<http://schema.org/>
		select distinct ?recipe 
		where { 
			"""+restaurant+""" chooseeat:hasRecipe ?recipe .
		}
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	elementList = []
	for result in results["results"]["bindings"]:
		recipe = result["recipe"]["value"]
		recList.append(recipe)
	return recList 

#Takes a list of recipes as parameter, returns a list with lists from 
#every nutrient from the "more" list of the user, where each "nutrient 
#list" is ordered in ascending order of the nutrient values.
#to specify which nutrient value belongs to which recipe, they 
#are related by the use of tuples as followed: ("Nutrient", "recipe", "nutrientValue") 
def addMore(recList):
	totalList = []
	more = []	
	for s,p,o in g.triples( (user, chooseeat.more, None) ):
		more.append(o)
	sparql = SPARQLWrapper("http://localhost:5820/restaurants/query")
	for element in more:
		sparql.setQuery("""
			PREFIX chooseeat:<http://chooseeat.org/vocabulary/>
			PREFIX schema:<http://schema.org/>
			select distinct ?s ?content 
			where { 
				?s a schema:Recipe;
				   schema:"""+element+"""Content ?content 
				}
		""")
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		elementList = []
		for result in results["results"]["bindings"]:
			value = result["content"]["value"]
			recipe = result["s"]["value"]
			value = float(value)
			if recipe in recList:
				elementList.append((element, recipe, value))
		elementList = sorted(elementList, key=lambda tup:tup[2])
		totalList.append(elementList)
	return totalList

#Takes a list of recipes as parameter, returns a list with lists from every nutrient from the "less"
#list of the user, where each "nutrient list" is ordered in descending order of the nutrient values.
#to specify which nutrient value belongs to which recipe, they are related by the use of tuples as 
#followed: ("Nutrient", "recipe", "nutrientValue") 
def addLess(recList):
	totalList = []
	less = []
	for s,p,o in g.triples( (user, chooseeat.less, None) ):
		less.append(o)
	sparql = SPARQLWrapper("http://localhost:5820/restaurants/query")
	for element in less:
		sparql.setQuery("""
			PREFIX chooseeat:<http://chooseeat.org/vocabulary/>
			PREFIX schema:<http://schema.org/>
			select distinct ?s ?content 
			where { 
				?s a schema:Recipe;
				   schema:"""+element+"""Content ?content 
			}
		""")
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()
		elementList = []
		for result in results["results"]["bindings"]:
			value = result["content"]["value"]
			recipe = result["s"]["value"]
			value = float(value)
			if recipe in recList:
				elementList.append((element, recipe, value))
		elementList = sorted(elementList, key=lambda tup:tup[2])
		sortedList = []
		for elements in reversed(elementList):
			sortedList.append(elements)
		totalList.append(sortedList)
	return totalList

#Takes a list of recipes as parameter, and returns a list of recipes,
# in the appropriate order for the users peronal condition
def rankDishes(recList):
	moreList = addMore(recList)
	lessList = addLess(recList)
	orderedRecipes = moreList + lessList
	scoreList = []
	output = []
	for element in recList:
		scoreList.append((element, 0))
	for recipeOrderList in orderedRecipes:
		for recipe in recList:
			matchingTuple = [item for item in recipeOrderList if item[1] == recipe]
			matchingTuple = matchingTuple[0]
			score = recipeOrderList.index(matchingTuple)
			oldScoreTuple = [item for item in scoreList if item[0] == recipe]
			oldScoreTuple = oldScoreTuple[0]
			newScore = oldScoreTuple[1] + score
			scoreList.remove(oldScoreTuple)
			scoreList.append((recipe, newScore))
	orderedScoreList = sorted(scoreList, key=lambda tup:tup[1])
	for scores in reversed(orderedScoreList):
		output.append(scores[0])
	output = removeDuplicates(output)
	return output

#Shows a window with the output
def createOutput(orderedList, forbiddenRecipes):
	output = Tk()
	output.configure(background='white')
	output.wm_title("ChooseEAT")
	more = []
	less = []
	forbidden = []
	interactions = []
	forbiddenRecipes = findDishNames(forbiddenRecipes)
	orderedList = findDishNames(orderedList)

	#Intro
	for s,p,o in g.triples( (user, FOAF.givenName, None) ):
		firstName = o
	for s,p,o in g.triples( (user, FOAF.familyName, None) ):
		lastName = o
	Lname = Label(output, text="Hi "+firstName+" "+lastName+ ",", 
		fg='white', bg='#FF5252').pack(fill=X)

	#age information
	for s,p,o in g.triples( (user, FOAF.age, None) ):
		ageCategory = calculateAgeCategory(o)
	Lage = Label(output, text="You are a(n) "+ageCategory+",", 
		fg='white', bg='#FF5252').pack(fill=X)

	#Nutrient recommendations
	for s,p,o in g.triples( (user, chooseeat.more, None) ):
		more.append(o)
	if len(more) > 0:
		Lmore = Label(output, text= "It is important that your dish contains "+
			"enough of the following nutrient(s):",
			 fg='white', bg='#FF5252').pack(fill=X)
		for i in range(len(more)):
			nutrient = more[i]
			Lnutrients = Label(output, text=nutrient, 
				fg='white', bg='#FF5252').pack(fill=X)
	for s,p,o in g.triples( (user, chooseeat.less, None) ):
		less.append(o)
	if len(less) > 0:
		Lless = Label(output, text= "And is it important that your dish does "+ 
			"not contain too much of the following nutrient(s):", 
			fg='white', bg='#FF5252').pack(fill=X)
		for i in range(len(less)):
			nutrient = less[i]
			Lnutrients = Label(output, text=nutrient, 
				fg='white', bg='#FF5252').pack(fill=X)
	Lgap = Label(output, text=" ", bg='white').pack(fill=X, ipady=0.1)
	#Possible drug interactions
	for s,p,o in g.triples( (user, chooseeat.takeDrug, None) ):
		interactions = foodInteractions(o)
	if len(interactions) > 0:
		Linteractions = Label(output, text=drug.get()+
			" has the following food recommendations :",
			 fg='#4B4747', bg='white').pack(fill=X)
		for i in range(len(interactions)):
			interaction = interactions[i]
			Linteractions = Label(output, text=interaction, 
				fg='#4B4747', bg='white').pack(ipadx=40, ipady=0.05)
	Lgap = Label(output, text=" ", bg='white').pack(fill=X, ipady=0.1)

	#Forbidden ingredients
	for s,p,o in g.triples( (user, chooseeat.forbidden, None) ):
		forbidden.append(o)
	if len(forbidden) > 0:
		Lforbidden = Label(output, text="You are not allowed to have the"+
			" following ingredient(s):", 
			fg='white', bg='#888787').pack(fill=X)
		for i in range(len(forbidden)):
			forbiddenIngredient = forbidden[i]
			LforbiddenIngredients = Label(output, text=forbiddenIngredient, 
				fg='white', bg='#888787').pack(fill=X)
		LforbiddenRecipeText = Label(output, text="The following dish(es)"+ 
			" contain one or more of these ingredients:",
		 fg='white', bg='#888787').pack(fill=X)
		for i in range(len(forbiddenRecipes)):
			forbiddenRecipe = forbiddenRecipes[i]
			LforbiddenRecipes = Label(output, text=forbiddenRecipe, 
				fg='white', bg='#888787').pack(fill=X)
		Ltherefore = Label(output, text="Therefore this dish is removed from the list of your matches.", 
			fg='white', bg='#888787').pack(fill=X)
	Lgap = Label(output, text=" ", bg='white').pack()

	#Ranking dishes
	Lconclusion = Label(output, text="The best matching dish from the restaurant is:",
		fg='white', bg='#888787').pack(fill=X)
	Lgap = Label(output, text=" ", bg='white').pack()
	Lbest = Label(output, text=orderedList[0]+"!", 
		fg='white', bg='#FF5252').pack(ipadx=40, ipady=20)
	Lgap = Label(output, text=" ", bg='white').pack()
	Lafter = Label(output, text="The rest of the dishes are ranked as followed:", 
		fg='white', bg='#FF5252').pack(fill=X)
	for i in range(len(orderedList)-1):
		i = i+1
		dish = orderedList[i]
		LafterDishes = Label(output, text=dish, fg='white', bg='#FF5252').pack(fill=X)

	output.mainloop()

#removes duplicates from a list.
def removeDuplicates(seq): 
	# order preserving
	checked = []
	for e in seq:
	   if e not in checked:
	       checked.append(e)
	return checked

#Takes as parameter age, returns the age category
def calculateAgeCategory(o):
	age = float(o)
	if age < 18:
		ageCategory = "child"
	elif age > 64:
		ageCategory = "senior"
	else:
		ageCategory = "adult"
	return ageCategory

def main():
	userInterface()
	makeDiet()
	recList, forbiddenRecipes = selectRecipes()
	rankedDishes = rankDishes(recList)	
	createOutput(rankedDishes, forbiddenRecipes)

main()