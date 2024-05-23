import argparse

parser = argparse.ArgumentParser()
parser.add_argument("square", help="display a square of a given number")

answer = args.square**2
print("Hello World from the hello_world.py file!")
print(f"the square of {args.square} equals {answer}")