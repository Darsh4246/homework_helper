from sympy import symbols, Eq, solveset, sin, cos, tan, log, exp, pi, S
from sympy.parsing.sympy_parser import parse_expr

# Define symbols
x, y, z = symbols('x y z')

def advanced_solver(expression):
    try:
        expression = expression.strip()
        
        # If the expression contains '=', treat it as an equation
        if '=' in expression:
            lhs, rhs = expression.split('=')
            eq = Eq(parse_expr(lhs), parse_expr(rhs))
            solution = solveset(eq, x, domain=S.Reals)
            return f"Solution: {solution}"
        else:
            result = parse_expr(expression)
            return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"

# Main loop to interact with the user
if __name__ == '__main__':
    print("🔢 Welcome to the Python Homework Solver!")
    print("Supports algebra, trig, log, and exponential equations!")
    print("Use 'x' as the variable. Type 'exit' to quit.\n")

    while True:
        user_input = input("Enter an expression or equation: ")
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        result = advanced_solver(user_input)
        print(result)
        print("-")
