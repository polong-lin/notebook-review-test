import argparse

parser = argparse.ArgumentParser()
parser.add_argument("square", help="display a square of a given number", type=int)
parser.add_argument("secretnumber", help="a secret number from Cloud Build vars", type=int)


args = parser.parse_args()
answer = args.square**2
print("Hello World from the hello_world.py file!")
print(f"the square of {args.square} equals {answer}")
print(f"The secret number is {args.secretnumber}")