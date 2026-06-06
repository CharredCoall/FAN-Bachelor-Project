import numpy as np
import csv
import os
import matplotlib.pyplot as plt

#Global variables
model_keys = ["yfYXmOJTWZj9daLG", "hdRm7wScJqOvmVze", "4vPloGeWwi6swcOq"]
models = ["Qwen", "meta-llama", "deepseek-ai"]
characters = ["Jim", "Brody", "Cecilia", "Jasmine", "Voll"]

#Counting the score of llm on real data
def countDataScore(npdata):
    Score = np.zeros((len(npdata), 3))
    for i, row in enumerate(npdata):
        if row[-1] != '':
            Score[i, int(row[-1][0]) - 1] += 1
    return Score

#Producing all graphs for selection of fullSet and Score 
def graphResults(fullSet, Score, qData):
    outputFolder = "result"
    singleRater = np.sum(Score) == len(Score)

    # Initialize counts and sums
    modelScore = np.zeros(3)
    modelSum = np.zeros(3)
    modelCount = np.zeros(3)

    modelEnjoyment = np.zeros(3)
    modelImperfection = np.zeros(3)

    characterScore = np.zeros(5)
    characterSum = np.zeros(5)
    characterCount = np.zeros(5)

    characterEnjoyment = np.zeros(5)
    characterImperfection = np.zeros(5)

    modelCharacterScore = np.zeros((3,5))
    modelCharacterSum = np.zeros((3,5))

    max_length = 0
    counter = 0
    convos = 0
    for row in fullSet:
        if row[-5] == "":
            convos += 1
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

    ImperfectionScore = np.zeros(2)
    ImperfectionSum = np.zeros(2)

    rowRating = np.zeros(convos)
    Enjoyment = np.zeros(convos)
    InCharacterScore = np.zeros(convos)

    ratingPerEnjoyment = np.zeros(6)
    ratingPerEnjoymentCount = np.zeros(6)
    
    ImperfectionEnjoyment = np.zeros(2)
    ImperfectionEnjoymentSum = np.zeros(2)

    characterConvos = np.zeros(5)

    LengthEnjoymentScore = np.zeros(max_length)

    #Initialize counters for keeping track of sentence length
    temp = []
    counter = 0
    convoIdx = 0
    lastQIdx = 0
    lastCharacterIdx = 0
    lastModelIdx = 0
    lastImperfect = 0

    #Calculating all stats
    for row, scores in zip(fullSet, Score):
        #Get model and character of row
        modelIdx = model_keys.index(row[-3])
        characterIdx = characters.index(row[-2])
        qIdx = [x[1] for x in qData].index(row[0])
        Imperfect = int(qData[qIdx][3] == "Yes" and row[-2] in qData[qIdx][5].split(";"))

    
        #Increment frequency counters
        modelCount[modelIdx] += 1
        characterCount[characterIdx] += 1

        #Sum given scores
        wScores = np.sum(scores * (np.arange(3) + 1))
        modelScore[modelIdx] += wScores
        characterScore[characterIdx] += wScores
        modelCharacterScore[modelIdx, characterIdx] += wScores
        ImperfectionScore[Imperfect] += wScores
        ratingPerEnjoyment[int(qData[qIdx][7+characterIdx])] += wScores
        modelEnjoyment[modelIdx] += int(qData[qIdx][7+characterIdx])
        modelImperfection[modelIdx] += Imperfect
        
        #Sum ratings
        sum = np.sum(scores)
        modelSum[modelIdx] += sum
        characterSum[characterIdx] += sum
        modelCharacterSum[modelIdx, characterIdx] += sum
        ImperfectionSum[Imperfect] += sum
        ratingPerEnjoymentCount[int(qData[qIdx][7+characterIdx])] += sum

        #If row is the first in a message, record stats over length for previous message
        if row[-5] == "":
            if counter > 0: #Ensure there was a previous message
                #Calculating total score and sum of previous message
                score = np.sum(np.array(temp) * (np.arange(3) + 1))
                sum = np.sum(temp)

                #Increment frequency counter
                LengthFreq[counter-1] += 1
                characterConvos[lastCharacterIdx] += 1
                ImperfectionEnjoymentSum[lastImperfect] += 1

                #Add score of previous message
                LengthScore[counter-1] += score
                characterLengthScore[lastCharacterIdx][counter-1] += score
                modelLengthScore[lastModelIdx][counter-1] += score
                LengthEnjoymentScore[counter-1] += int(qData[lastQIdx][7+lastCharacterIdx])
                ImperfectionEnjoyment[lastImperfect] += int(qData[lastQIdx][7+lastCharacterIdx])
                characterEnjoyment[lastCharacterIdx] += int(qData[lastQIdx][7+lastCharacterIdx])
                characterImperfection[lastCharacterIdx] += lastImperfect

                #Add sum of previous message
                LengthSum[counter-1] += sum
                characterLengthSum[lastCharacterIdx][counter-1] += sum
                modelLengthSum[lastModelIdx][counter-1] += sum

                rowRating[convoIdx] = score/sum
                Enjoyment[convoIdx] = qData[lastQIdx][7+lastCharacterIdx]
                InCharacterScore[convoIdx] = qData[lastQIdx][lastCharacterIdx - 7]
                convoIdx += 1

            #Reset lenght counters
            counter = 0
            temp = []
            lastQIdx = qIdx
            lastCharacterIdx = characterIdx
            lastModelIdx = modelIdx
            lastImperfect = Imperfect

        temp.append(scores)
        counter += 1
    
    #Ensure the length of the final message is also calculated
    if counter > 0:
        #Calculating total score and sum of previous message
        score = np.sum(np.array(temp) * (np.arange(3) + 1))
        sum = np.sum(temp)

        #Increment frequency counter
        LengthFreq[counter-1] += 1
        characterConvos[lastCharacterIdx] += 1
        ImperfectionEnjoymentSum[lastImperfect] += 1

        #Add score of previous message
        LengthScore[counter-1] += score
        characterLengthScore[lastCharacterIdx][counter-1] += score
        modelLengthScore[lastModelIdx][counter-1] += score
        LengthEnjoymentScore[counter-1] += int(qData[lastQIdx][7+lastCharacterIdx])
        ImperfectionEnjoyment[lastImperfect] += int(qData[lastQIdx][7+lastCharacterIdx])
        characterEnjoyment[lastCharacterIdx] += int(qData[lastQIdx][7+lastCharacterIdx])
        characterImperfection[lastCharacterIdx] += lastImperfect

        #Add sum of previous message
        LengthSum[counter-1] += sum
        characterLengthSum[lastCharacterIdx][counter-1] += sum
        modelLengthSum[lastModelIdx][counter-1] += sum

        rowRating[convoIdx] = score/sum
        Enjoyment[convoIdx] = qData[lastQIdx][7+lastCharacterIdx]
        InCharacterScore[convoIdx] = qData[lastQIdx][lastCharacterIdx - 7]

    #Calculate averages
    LengthMu = LengthScore/np.max([LengthSum, np.ones(len(LengthSum))], axis=0)
    characterLengthMu = characterLengthScore/np.max([characterLengthSum, np.ones_like(characterLengthSum)], axis=0)
    modelLengthMu = modelLengthScore/np.max([modelLengthSum, np.ones_like(modelLengthSum)], axis=0)
    characterMu = characterScore/characterSum
    modelMu = modelScore/modelSum
    modelCharacterMu = modelCharacterScore/modelCharacterSum
    ImperfectionMu = ImperfectionScore/ImperfectionSum
    ratingPerEnjoymentMu = ratingPerEnjoyment/ratingPerEnjoymentCount
    LengthEnjoymentMu = LengthEnjoymentScore/np.max([LengthFreq, np.ones_like(LengthFreq)], axis=0)
    ImperfectionEnjoymentMu = ImperfectionEnjoyment/ImperfectionEnjoymentSum
    characterEnjoymentMu = characterEnjoyment/characterConvos
    characterImperfectionMu = characterImperfection/characterConvos
    modelEnjoymentMu = modelEnjoyment/modelCount
    modelImperfectionMu = modelImperfection/modelCount

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
    #plt.xticks(np.arange(max_length) + 1)

    freqScaling = np.ceil(np.max(LengthFreq)/8)

    ax2.tick_params(axis='y', labelcolor="red", zorder=1)
    ax2.set_yticks(np.append([1], np.arange(8) * freqScaling + freqScaling ))
    ax1.set_yticks(np.arange(9) * (2/8) + 1)
    ax2.set_ylim((0,8 * freqScaling))
    ax1.set_ylim((1,3))
    ax1.grid()
    ax2.grid()

    #Set labels and legends
    ax2.legend(avglengthplt + frqlengthplt, ["Avg. score per length", "Frq of length"], loc='upper right', framealpha=1.0, edgecolor='black', fancybox=False)
    ax1.set_ylabel("Average score")
    ax2.set_ylabel("Frequency", color="red")
    ax1.set_xlabel("Conversation Length")
    plt.title("Average score over length of conversation")
    
    #Save graph
    plt.savefig(f"{outputFolder}/exp2_Length")
    plt.close()

    if max_length > 20:
        #Create Plot 1!
        #Plotting average score per length along with frequency of length (to show how significant the score of that length is)
        fig, ax1 = plt.subplots(figsize=(8, 6))

        #Uses a dual yaxis plot
        ax2 = ax1.twinx()

        max_length = np.max(np.where(LengthFreq[:20] > 0)) + 1
        LengthFreq = LengthFreq[:max_length]
        LengthMu = LengthMu[:max_length]

        #Plots average and frequency
        avglengthplt = ax1.plot(np.arange(max_length) + 1, LengthMu)
        frqlengthplt = ax2.plot(np.arange(max_length) + 1, LengthFreq, color="red")

        #Set ticks and limits, such that y axes match
        #plt.xticks(np.arange(max_length) + 1)

        freqScaling = np.ceil(np.max(LengthFreq)/8)

        ax2.tick_params(axis='y', labelcolor="red", zorder=1)
        ax2.set_yticks(np.append([1], np.arange(8) * freqScaling + freqScaling ))
        ax1.set_yticks(np.arange(9) * (2/8) + 1)
        ax2.set_ylim((0,8 * freqScaling))
        ax1.set_ylim((1,3))
        ax1.grid()
        ax2.grid()

        #Set labels and legends
        ax2.legend(avglengthplt + frqlengthplt, ["Avg. score per length", "Frq of length"], loc='upper right', framealpha=1.0, edgecolor='black', fancybox=False)
        ax1.set_ylabel("Average score")
        ax2.set_ylabel("Frequency", color="red")
        ax1.set_xlabel("Conversation Length")
        plt.title("Average score over length of conversation")
        
        #Save graph
        plt.savefig(f"{outputFolder}/exp2_Length(%outliers)")
        plt.close()

    #Create Plot 2!
    #Plotting average score per length along with frequency of length (to show how significant the score of that length is)
    fig, ax1 = plt.subplots(figsize=(8, 6))

    #Uses a dual yaxis plot
    ax2 = ax1.twinx()

    #Plots average and frequency
    avglengthplt = ax1.plot(np.arange(max_length-1) + 2, LengthEnjoymentMu[1:])
    frqlengthplt = ax2.plot(np.arange(max_length-1) + 2, LengthFreq[1:], color="red")

    #Set ticks and limits, such that y axes match
    #plt.xticks(np.arange(max_length) + 1)

    freqScaling = np.ceil(np.max(LengthFreq)/10)

    ax2.tick_params(axis='y', labelcolor="red", zorder=1)
    ax2.set_yticks(np.append([1], np.arange(11) * freqScaling  ))
    ax1.set_yticks(np.arange(11) * 0.5)
    ax2.set_ylim((0,10 * freqScaling))
    ax1.set_ylim((0,5))
    ax1.grid()
    ax2.grid()

    #Set labels and legends
    ax2.legend(avglengthplt + frqlengthplt, ["Avg. Enjoyment per length", "Frq of length"], loc='upper right', framealpha=1.0, edgecolor='black', fancybox=False)
    ax1.set_ylabel("Average Enjoyment")
    ax2.set_ylabel("Frequency", color="red")
    ax1.set_xlabel("Conversation Length")
    plt.title("Average Enjoyment over length of conversation")
    
    #Save graph
    plt.savefig(f"{outputFolder}/exp2_LengthEnjoyment")
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
    plt.savefig(f"{outputFolder}/exp2_CharacterLength")
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
    plt.savefig(f"{outputFolder}/exp2_ModelLength")
    plt.close()

    #Create Plot 4!
    #Plotting frequency of each character
    plt.bar(characters, characterCount, label=characters, color=["red", "blue", "green", "purple", "orange"])
    plt.ylabel("Frequency")
    plt.title("Frequency of Characters")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_CharacterFreq.png")
    plt.close()

    #Create Plot 5!
    #Plotting average score of each character
    plt.bar(characters, characterMu, label=characters, color=["red", "blue", "green", "purple", "orange"])
    plt.ylabel("Average Score")
    plt.ylim((2,3))
    plt.title("Score over all Characters")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_Character.png")
    plt.close()

    #Create Plot 5!
    #Plotting average enjoyment of each character
    plt.bar(characters, characterEnjoymentMu, label=characters, color=["red", "blue", "green", "purple", "orange"])
    plt.ylabel("Average Enjoyment")
    plt.ylim((0,5))
    plt.title("Enjoyment over all Characters")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_CharacterEnjoyment.png")
    plt.close()

    #Create Plot 5!
    #Plotting average enjoyment of each character
    plt.bar(characters, characterImperfectionMu, label=characters, color=["red", "blue", "green", "purple", "orange"])
    plt.ylabel("Average Imperfections")
    plt.ylim((0,1))
    plt.title("Imperfection over all Characters")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_CharacterImperfection.png")
    plt.close()

    #Create Plot 6!
    #Plotting frequency of models
    plt.bar(models, modelCount, label=models, color=["red", "blue", "green"])
    plt.ylabel("Frequency")
    plt.title("Frequency of models")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_ModelFreq.png")
    plt.close()

    #Create Plot 7!
    #Plotting Average score of each model
    plt.bar(models, modelMu, label=models, color=["red", "blue", "green"])
    plt.ylabel("Average Score")
    plt.ylim((2,3))
    plt.title("Score over all models")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_Model.png")
    plt.close()

    #Create Plot 7!
    #Plotting Average enjoyment of each model
    plt.bar(models, modelEnjoymentMu, label=models, color=["red", "blue", "green"])
    plt.ylabel("Average Enjoyment")
    plt.ylim((0,5))
    plt.title("Enjoyment over all models")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_ModelEnjoyment.png")
    plt.close()

    #Create Plot 7!
    #Plotting Average Imperfections of each model
    plt.bar(models, modelImperfectionMu * 100, label=models, color=["red", "blue", "green"], zorder=5)
    plt.ylabel("% of responses with Imperfection")
    plt.ylim((0,30))
    plt.yticks(np.arange(7) * 5)
    plt.grid(axis='y')
    plt.title("Imperfection over all models")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_ModelImperfection.png")
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
    plt.savefig(f"{outputFolder}/exp2_ModelCharacter.png")
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
    plt.savefig(f"{outputFolder}/exp2_ModelCharacterSorted.png")
    plt.close()

    #Create plot 10!
    #Plot of the overall score of each row, sorted by score
    plt.plot(Mu)
    if singleRater:
        plt.ylabel("Score")
    else:
        plt.ylabel("Average Score")
    plt.xlabel("# of responses")
    plt.title("Score over all responses (sorted)")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_Score.png")
    plt.close()

    #Create Plot 11!
    #Plotting Average score of whether model experienced imperfections
    plt.bar(["No/Maybe", "Yes"], ImperfectionMu, label=["No/Maybe", "Yes"], color=["green", "red"], zorder=5)
    plt.ylabel("Average Score")
    plt.grid(axis='y')
    plt.ylim((2,3))
    plt.title("Score over Imperfection")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_Imperfection.png")
    plt.close()

    #Create Plot 11!
    #Plotting Average Enjoyment of whether model experienced imperfections
    plt.bar(["No/Maybe", "Yes"], ImperfectionEnjoymentMu, label=["No/Maybe", "Yes"], color=["green", "red"], zorder=5)
    plt.ylabel("Average Enjoyment")
    plt.xlabel("Did you experience any imperfections with this character?")
    plt.grid(axis='y')
    plt.ylim((0,5))
    plt.title("Enjoyment over Imperfection")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_EnjoymentImperfection.png")
    plt.close()

    #Create Plot 12!
    #Scatter plot over rating to enjoyment
    plt.scatter(Enjoyment, rowRating)
    a, b = np.polyfit(Enjoyment, rowRating, 1)
    plt.plot(a * np.arange(6) + b)
    plt.ylabel("Score")
    plt.xlabel("Enjoyment")
    plt.title("Score over Enjoyment")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_RatingToEnjoyment.png")
    plt.close()

    #Create Plot 13!
    #Scatter plot over rating to enjoyment
    plt.scatter(InCharacterScore, rowRating)
    a, b = np.polyfit(InCharacterScore, rowRating, 1)
    plt.plot(a * np.arange(6) + b)
    plt.ylabel("Score")
    plt.xlabel("How well did the model stay in character")
    plt.title("Score over Staying in character")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_InCharacterRating.png")
    plt.close()

    #Create Plot 14!
    #Plotting Average model score per playerEnjoyment
    plt.bar(np.arange(6), ratingPerEnjoymentMu)
    plt.ylabel("Average Score")
    plt.xlabel("Enjoyment")
    plt.ylim((2,3))
    plt.title("Average Score over Enjoyment")

    #Save graph
    plt.savefig(f"{outputFolder}/exp2_EnjoymentAverageScore.png")
    plt.close()


#Plots the graphs 
#Initializes data
realdata = []
qData = []

#Gets real data
with open(f"judge_merged_dataset_full.csv", mode='r', encoding='Latin-1') as path:
        file = csv.reader(path)
        next(file, None)
        realdata = np.fromiter(file, dtype=np.ndarray)

with open("Wasteful Fellas.csv", mode='r', encoding='Latin-1') as path:
    file = csv.reader(path)
    next(file, None)
    qData = np.fromiter(file, dtype=np.ndarray)

qData = np.array([x for x in qData if x[1] != ""])

realdata = np.array([x for x in realdata if x[0] in [y[1] for y in qData]])

#Count scores
realMu = countDataScore(realdata)

#Process and plot real data
realdata = realdata[~np.all(realMu == 0, axis=1)]
realMu = realMu[~np.all(realMu == 0, axis=1)]

graphResults(realdata, realMu, qData)