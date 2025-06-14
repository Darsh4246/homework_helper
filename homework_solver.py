from sympy import *
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

# Initialize symbols
x, y, z = symbols('x y z')

# Set up transformations for parsing (including implicit multiplication)
transformations = (standard_transformations + (implicit_multiplication_application,))


def evaluate_expression(expression):
    try:
        expression = expression.strip()

        # Try solving if equation
        if '=' in expression:
            parts = expression.split('=', 1)  # Split on first '=' only
            if len(parts) != 2:
                return "Error: Equation must contain exactly one '='"

            lhs, rhs = parts
            try:
                lhs_expr = parse_expr(lhs, transformations=transformations)
                rhs_expr = parse_expr(rhs, transformations=transformations)
                equation = Eq(lhs_expr, rhs_expr)
                solution = solve(equation)
                return f"Solution: {solution}"
            except Exception as e:
                return f"Error parsing equation: {e}"
        else:
            try:
                result = parse_expr(expression, transformations=transformations)
                simplified = simplify(result)
                expanded = expand(result)
                return (f"Simplified: {simplified}\n"
                        f"Expanded: {expanded}\n"
                        f"Evaluated: {result.evalf() if result.is_number else result}")
            except Exception as e:
                return f"Error parsing expression: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# Sample usage
print("Math Expression Evaluator")
print("Enter expressions like '2*x + 3', 'x^2 - 1 = 0', or 'sin(pi/2)'")
print("Type 'exit' to quit\n")

while True:
    expr = input("Enter a math expression: ")
    if expr.lower() in ('exit', 'quit'):
        break
    print(evaluate_expression(expr))
    print()  # Add blank line for readability