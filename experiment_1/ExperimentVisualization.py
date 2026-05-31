import numpy as np
import csv
import os
import matplotlib.pyplot as plt

#Global variables
model_keys = ["yfYXmOJTWZj9daLG", "hdRm7wScJqOvmVze", "4vPloGeWwi6swcOq"]
models = ["Qwen", "meta-llama", "deepseek-ai"]
characters = ["Jim", "Brody", "Cecilia", "Jasmine", "Voll"]

#Counting our own scores
def countOurScore(length, cumN):
    Score = np.zeros((length, 3))
    for an in ["asger", "franja", "natali"]:
        for part in range(1,8):
            if os.path.exists(f"{an}/merged_dataset_part{part}_{an}.csv"): #Ignore if file doesn't exist
                with open(f"{an}/merged_dataset_part{part}_{an}.csv", mode='r', encoding='Latin-1') as path:
                    file = csv.reader(path)
                    next(file, None)
                    #For each row, increment the value at the score we made
                    for i, row in enumerate(file):
                        if row[-1] != '': #Ignore if score is not given
                            Score[i + cumN[part - 1],int(row[-1])-1] += 1
    return Score

#Counting the score of llm as a judge
def countModelScore(length, cumN):
    Score = np.zeros((length, 3))
    for part in range(1,8):
        if os.path.exists(f"judge_merged_dataset_part{part}.csv"): #Ignor if file doesn't exist
            with open(f"judge_merged_dataset_part{part}.csv", mode='r', encoding='Latin-1') as path:
                file = csv.reader(path)
                next(file, None)
                #For each row, increment the value at the score the model made
                for i, row in enumerate(file):
                    if row[-1] != '': #Ignore if score is not given
                        Score[i + cumN[part - 1],int(row[-1][0])-1] += 1
    return Score


#Producing all graphs for selection of fullSet and Score 
def graphResults(fullSet, Score, outputFolder):
    singleRater = np.sum(Score) == len(Score)

    # Initialize counts and sums
    modelScore = np.zeros(3)
    modelSum = np.zeros(3)
    modelCount = np.zeros(3)

    characterScore = np.zeros(5)
    characterSum = np.zeros(5)
    characterCount = np.zeros(5)

    modelCharacterScore = np.zeros((3,5))
    modelCharacterSum = np.zeros((3,5))

    max_length = 0
    counter = 0
    for row in fullSet:
        if row[1] == "":
            max_length = np.max([max_length, counter])
            counter = 0
        counter += 1

    LengthScore = np.zeros(max_length)
    LengthSum = np.zeros(max_length)
    LengthFreq = np.zeros(max_length)

    characterLengthScore = np.zeros((5, max_length))
    characterLengthSum = np.zeros((5, max_length))

    modelLengthScore = np.zeros((3, max_length))
    modelLengthSum = np.zeros((3, max_length))

    #Initialize counters for keeping track of sentence length
    temp = []
    counter = 0

    #Calculating all stats
    for row, scores in zip(fullSet, Score):
        #Get model and character of row
        modelIdx = model_keys.index(row[-3])
        characterIdx = characters.index(row[-2])
        
        #Increment frequency counters
        modelCount[modelIdx] += 1
        characterCount[characterIdx] += 1

        #Sum given scores
        modelScore[modelIdx] += np.sum(scores * (np.arange(3) + 1))
        characterScore[characterIdx] += np.sum(scores * (np.arange(3) + 1))
        modelCharacterScore[modelIdx, characterIdx] += np.sum(scores * (np.arange(3) + 1))
        
        #Sum ratings
        modelSum[modelIdx] += np.sum(scores)
        characterSum[characterIdx] += np.sum(scores)
        modelCharacterSum[modelIdx, characterIdx] += np.sum(scores)

        #If row is the first in a message, record stats over length for previous message
        if row[1] == "":
            if counter > 0: #Ensure there was a previous message
                #Calculating total score and sum of previous message
                score = np.sum(np.array(temp) * (np.arange(3) + 1))
                sum = np.sum(temp)

                #Increment frequency counter
                LengthFreq[counter-1] += 1

                #Add score of previous message
                LengthScore[counter-1] += score
                characterLengthScore[characterIdx][counter-1] += score
                modelLengthScore[modelIdx][counter-1] += score

                #Add sum of previous message
                LengthSum[counter-1] += sum
                characterLengthSum[characterIdx][counter-1] += sum
                modelLengthSum[modelIdx][counter-1] += sum

            #Reset lenght counters
            counter = 0
            temp = []

        temp.append(scores)
        counter += 1
    
    #Ensure the length of the final message is also calculated
    if counter > 0:
        #Calculating total score and sum of previous message
        score = np.sum(np.array(temp) * (np.arange(3) + 1))
        sum = np.sum(temp)

        #Increment frequency counter
        LengthFreq[counter-1] += 1

        #Add score of previous message
        LengthScore[counter-1] += score
        characterLengthScore[characterIdx][counter-1] += score
        modelLengthScore[modelIdx][counter-1] += score

        #Add sum of previous message
        LengthSum[counter-1] += sum
        characterLengthSum[characterIdx][counter-1] += sum
        modelLengthSum[modelIdx][counter-1] += sum

    #Calculate averages
    LengthMu = LengthScore/np.max([LengthSum, np.ones(len(LengthSum))], axis=0)
    characterLengthMu = characterLengthScore/np.max([characterLengthSum, np.ones_like(characterLengthSum)], axis=0)
    modelLengthMu = modelLengthScore/np.max([modelLengthSum, np.ones_like(modelLengthSum)], axis=0)
    characterMu = characterScore/characterSum
    modelMu = modelScore/modelSum
    modelCharacterMu = modelCharacterScore/modelCharacterSum

    #Only calculates overall score when score is only given by one rater
    if singleRater:
        Mu = np.sum(Score * (np.arange(3) + 1), axis=1)
    else:
        Mu = np.sum(Score * (np.arange(3) + 1), axis=1) / np.sum(Score, axis=1)

    #Sort Overall scores
    Mu = np.sort(Mu)

    #Create Plot 1!
    #Plotting average score per length along with frequency of length (to show how significant the score of that length is)
    fig, ax1 = plt.subplots(figsize=(8, 6))

    #Uses a dual yaxis plot
    ax2 = ax1.twinx()

    #Plots average and frequency
    avglengthplt = ax1.plot(np.arange(max_length) + 1, LengthMu)
    frqlengthplt = ax2.plot(np.arange(max_length) + 1, LengthFreq, color="red")

    #Set ticks and limits, such that y axes match
    plt.xticks(np.arange(max_length) + 1)
    ax2.tick_params(axis='y', labelcolor="red", zorder=1)
    ax2.set_yticks(np.append([1], np.arange(8) * 6 + 6 ))
    ax1.set_yticks(np.arange(9) * (2/8) + 1)
    ax2.set_ylim((0,48))
    ax1.set_ylim((1,3))
    ax1.grid()
    ax2.grid()

    #Set labels and legends
    ax2.legend(avglengthplt + frqlengthplt, ["Avg. score per length", "Frq of length"], loc='upper right', framealpha=1.0, edgecolor='black', fancybox=False)
    ax1.set_ylabel("Average score")
    ax2.set_ylabel("Frequency", color="red")
    plt.xlabel("Conversation Length")
    plt.title("Average score over length of conversation")
    
    #Save graph
    plt.savefig(f"{outputFolder}/Length")
    plt.close()

    #Create Plot 2!
    #Plotting Average score for each character over length of conversation (of lengths in [1,6])
    #Plot for each character
    for i in np.arange(5):
        plt.bar(np.arange(6) * 8 + 1 + i, characterLengthMu[i][:6], label=characters[i])
    
    #Set tick, labels and legends
    plt.xticks(np.arange(6) * 8 + 3, np.arange(6) + 1)
    plt.legend(loc="lower left")
    plt.ylabel("Average score")
    plt.title("Average score over length of conversation")
    plt.xlabel("Conversation Length")

    #Save graph
    plt.savefig(f"{outputFolder}/CharacterLength")
    plt.close()

    #Create Plot 3!
    #Plotting Average score for each model over length of conversation (of lengths in [1,6])
    #Plot for each model
    for i in np.arange(3):
        plt.bar(np.arange(6) * 8 + 1 + i, modelLengthMu[i][:6], label=models[i])

    #Set tick, labels and legends
    plt.xticks(np.arange(6) * 8 + 2, labels=np.arange(6) + 1)
    plt.legend()
    plt.ylim((2,3))
    plt.ylabel("Average score")
    plt.title("Average score over length of conversation")
    plt.xlabel("Conversation Length")

    #Save graph
    plt.savefig(f"{outputFolder}/ModelLength")
    plt.close()

    #Create Plot 4!
    #Plotting frequency of each character
    plt.bar(characters, characterCount, label=characters, color=["red", "blue", "green", "yellow", "orange"])
    plt.ylabel("Frequency")
    plt.title("Frequency of Characters")

    #Save graph
    plt.savefig(f"{outputFolder}/CharacterFreq.png")
    plt.close()

    #Create Plot 5!
    #Plotting average score of each character
    plt.bar(characters, characterMu, label=characters, color=["red", "blue", "green", "yellow", "orange"])
    plt.ylabel("Average Score")
    plt.ylim((2,3))
    plt.title("Score over all Characters")

    #Save graph
    plt.savefig(f"{outputFolder}/Character.png")
    plt.close()

    #Create Plot 6!
    #Plotting frequency of models
    plt.bar(models, modelCount, label=models, color=["red", "blue", "green"])
    plt.ylabel("Frequency")
    plt.title("Frequency of models")

    #Save graph
    plt.savefig(f"{outputFolder}/ModelFreq.png")
    plt.close()

    #Create Plot 7!
    #Plotting Average score of each model
    plt.bar(models, modelMu, label=models, color=["red", "blue", "green"])
    plt.ylabel("Average Score")
    plt.ylim((2,3))
    plt.title("Score over all models")

    #Save graph
    plt.savefig(f"{outputFolder}/Model.png")
    plt.close()

    #Create Plot 8!
    #Plotting score over cross of models and characters
    #Plot for each model over characters, creates bars grouped by character and coloured by model
    for i in np.arange(3):
        plt.bar( np.arange(5) * 8 + 1 + i, modelCharacterMu[i], label=models[i])
    
    #Set ticks to character names
    plt.xticks(np.arange(5) * 8 + 2, labels=characters)
    plt.yticks(np.arange(10) * 0.1 + 2)
    plt.ylim((2,3))
    plt.legend(loc='upper left')
    plt.ylabel("Average Score")
    plt.title("Score over cross of models and Characters")

    #Save graph
    plt.savefig(f"{outputFolder}/ModelCharacter.png")
    plt.close()

    #Create plot 9!
    #Plotting cross of models and characters sorted by score

    #Creates matrix with information about the order of each model per character
    sortedModelCharacterMu = modelCharacterMu[:,characterMu.argsort()]
    sortedCharacters = np.array(characters)[characterMu.argsort()]
    placementMatrix = sortedModelCharacterMu.argsort(axis=0)

    #Plot for each model over characters, creates bars grouped by sorted characters and model
    for i in np.arange(3):
        imatrix = np.where(placementMatrix == i)
        plt.bar( np.arange(5) * 8 + 1 + imatrix[0][imatrix[1].argsort()], sortedModelCharacterMu[i], label=models[i])
    
    #Set ticks to character names
    plt.xticks(np.arange(5) * 8 + 2, labels=sortedCharacters)
    plt.yticks(np.arange(10) * 0.1 + 2)
    plt.ylim((2,3))
    plt.legend(loc='upper left')
    plt.ylabel("Average Score")
    plt.title("Score over cross of models and Characters (Sorted)")

    #Save graph
    plt.savefig(f"{outputFolder}/ModelCharacterSorted.png")
    plt.close()

    #Create plot 10!
    #Plot of the overall score of each row, sorted by score
    plt.plot(Mu)
    if singleRater:
        plt.ylabel("Score")
    else:
        plt.ylabel("Average Score")
    plt.title("Score over all responses (sorted)")

    #Save graph
    plt.savefig(f"{outputFolder}/Score.png")
    plt.close()


#Plots the graphs for combinations of our own scores and the models scores    
#Initializes data
fullSet = []
N = []

#Creates full dataset 
for i in range(7):
    #Gets the nonscored dataset.
    dataset = csv.reader(open(f"merged_dataset_part{i+1}.csv", mode='r', encoding='Latin-1'))
    next(dataset, None) #Skip header
    
    dataset = np.fromiter(dataset, dtype=np.ndarray) #Converts to numpy array
    
    #Store Length
    N.append(len(dataset))

    #Append data to full set
    fullSet = np.append(fullSet, dataset)

#Create cummulative sum for creating Score matrix
cumN = np.cumsum(np.append([0], N[:-1]))

#Gets the full length of the dataset
length = np.sum(N)

#Count scores
oMu = countOurScore(length, cumN) 
mMu = countModelScore(length, cumN)
cMu = oMu + mMu

#Process and plot combined graphs
cfullSet = fullSet[~np.all(cMu == 0, axis=1)]
cMu = cMu[~np.all(cMu == 0, axis=1)]

graphResults(cfullSet, cMu, "combined_scores")

#Process and plot our graphs
ofullSet = fullSet[~np.all(oMu == 0, axis=1)]
oMu = oMu[~np.all(oMu == 0, axis=1)]

graphResults(ofullSet, oMu, "our_scores")

#Process and plot models graphs
mfullSet = fullSet[~np.all(mMu == 0, axis=1)]
mMu = mMu[~np.all(mMu == 0, axis=1)]

graphResults(mfullSet, mMu, "model_scores")