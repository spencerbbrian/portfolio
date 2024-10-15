import json
import random

with open("C:/Users/brian/Desktop/portfolio/portfolio/python/intermediate/Quiz/questions.json") as f:
    questions = json.load(f)

play =  input("Do you want to play a geography quiz?")


def play_quiz():
    number_of_questions = 5
    score = 0
    easy_questions = questions['easy']
    medium_questions = questions['medium']
    hard_questions = questions['hard']
    level =  input("What level of difficulty do you want to play at? (easy, medium, hard): ")
    if  level == "easy":
        random.shuffle(questions["easy"])
        for i, eq in enumerate(questions["easy"][:number_of_questions]):
            print(f"Question {i + 1}: {eq['question']}")
            for j, option in enumerate(eq["options"]):
                print(f"Option {j + 1}: {option}")
            try:
                answer = int(input("Answer: (1 to 4): "))
                if 1 <= answer <= 4:
                    if eq["options"][answer - 1] == eq["answer"]:
                        print("correct")
                        score += 1
                    else:
                        print("Wrong! Next question")
                else: 
                    print("Please enter a valid option between from 1 to 4")
            except ValueError:
                 print("Please enter a valid option between from 1 to 4")
        
    print(f"Your score is {score}/{number_of_questions}.")

if play == "yes" or "Y":
        print("Welcome to the geography quiz!")
        play_quiz()
else:
        print("Goodbye!")