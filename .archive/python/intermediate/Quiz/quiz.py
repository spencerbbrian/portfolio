import json
import random

with open("C:/Users/brian/Desktop/portfolio/portfolio/python/intermediate/Quiz/questions.json") as f:
    questions = json.load(f)

play =  input("Do you want to play a geography quiz?")

def ask_questions(level_questions, number_of_questions):
    score = 0
    random.shuffle(level_questions)
    for i, q in enumerate(level_questions[:number_of_questions]):
        print(f"Question {i + 1}: {q['question']}")
        for j, option in enumerate(q["options"]):
            print(f"Option {j + 1}: {option}")
        try:
            answer = int(input("Answer: (1 to 4): "))
            if 1 <= answer <= 4:
                if q["options"][answer - 1] == q["answer"]:
                    print("correct")
                    score += 1
                else:
                    print("Wrong! Next question")
            else:
                print("Please enter a valid option between from 1 to 4")
        except ValueError:
            print("Please enter a valid option between from 1 to 4")
    return score

def play_quiz():
    number_of_questions = 5
    level = input("What level of difficulty do you want to play at? (easy, medium, hard): ")
    if level in questions:
        score = ask_questions(questions[level], number_of_questions)
        print(f"Your score is {score}/{number_of_questions}.")
    else:
        print("Invalid difficulty level. Please choose from easy, medium, or hard.")

if play == "yes" or play == "Y":
        print("Welcome to the geography quiz!")
        play_quiz()
else:
        print("Goodbye!")