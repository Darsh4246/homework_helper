import streamlit as st
from sympy import *
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
                                        implicit_multiplication_application)

# Set page title and icon
st.set_page_config(page_title="Math Expression Evaluator", page_icon="➗")

# Initialize symbols
x, y, z = symbols('x y z')

# Set up transformations for parsing
transformations = (standard_transformations +
                   (implicit_multiplication_application,))


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
                return solution
            except Exception as e:
                return f"Error parsing equation: {e}"
        else:
            try:
                result = parse_expr(expression, transformations=transformations)
                simplified = simplify(result)
                expanded = expand(result)
                return {
                    "original": result,
                    "simplified": simplified,
                    "expanded": expanded,
                    "evaluated": result.evalf() if result.is_number else result
                }
            except Exception as e:
                return f"Error parsing expression: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


# Streamlit UI
st.title("Math Expression Evaluator")
st.markdown("""
Enter mathematical expressions like:
- `2*x + 3` 
- `x**2 - 1 = 0` 
- `sin(pi/2)`
- `integrate(x**2, x)`
""")

# Input field
expr = st.text_input("Enter a math expression:", "x**2 + 2*x + 1")

if expr:
    result = evaluate_expression(expr)

    if isinstance(result, dict):
        st.success("Expression parsed successfully!")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Simplified")
            st.latex(f"{latex(result['simplified'])}")

        with col2:
            st.subheader("Expanded")
            st.latex(f"{latex(result['expanded'])}")

        st.subheader("Evaluated")
        st.latex(f"{latex(result['evaluated'])}")

        st.subheader("Original")
        st.latex(f"{latex(result['original'])}")

    elif isinstance(result, list) or isinstance(result, dict):
        st.success("Solution found:")
        st.latex(f"Solution: {latex(result)}")
    else:
        st.error(result)

# Add some examples
st.markdown("### Examples")
examples = [
    "x**2 - 4 = 0",
    "diff(sin(x) + x**2, x)",
    "integrate(exp(-x**2), x)",
    "limit(sin(x)/x, x, 0)",
    "Matrix([[1, 2], [3, 4]]) * Matrix([x, y])"
]

cols = st.columns(len(examples))
for col, example in zip(cols, examples):
    with col:
        if st.button(example):
            st.session_state.math_expr = example
            st.experimental_rerun()

# Initialize session state
if 'math_expr' not in st.session_state:
    st.session_state.math_expr = expr