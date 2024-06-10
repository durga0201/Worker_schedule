from flask import Flask, request, jsonify
from ortools.sat.python import cp_model
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from typing import Union

app = Flask(__name__)

def visualize_schedule(sched, n_days, n_shifts, n_nurses):
    x, y = zip(*[(day * n_shifts + shift, nurse) for nurse, day, shift in sched])
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.scatter(x, y)
    width = 1
    height = 1
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for nurse, day, shift in sched:
        color = colors[nurse % len(colors)]
        ax.add_patch(Rectangle(
            xy=((day * n_shifts + shift) - width / 2, nurse - height / 2),
            width=width, height=height,
            linewidth=1, color=color, fill=True))
    
    ax.axis('equal')
    ax.set_xticks(range(n_days * n_shifts))
    ax.set_yticks(range(n_nurses))
    ax.set_xlabel("Shifts")
    ax.set_ylabel("Nurses")
    plt.savefig("schedule.png")
    plt.close()  # Close the plot to prevent memory leaks

@app.route('/schedule', methods=['POST'])
def solve_schedule():
    data = request.json

    # Extract data
    num_nurses = data['num_nurses']
    num_shifts = data['num_shifts']
    num_days = data['num_days']
    all_nurses = range(num_nurses)
    all_shifts = range(num_shifts)
    all_days = range(num_days)
    shift_requests = data['shift_requests']
    holiday_requests = data['holiday_requests']

    # Create the model
    model = cp_model.CpModel()

    # Create shift variables
    shifts = {}
    for n in range(num_nurses):
        for d in range(num_days):
            for s in range(num_shifts):
                shifts[(n, d, s)] = model.NewBoolVar(f"shift_n{n}_d{d}_s{s}")

    # Each shift is assigned to exactly one nurse on each day
    for d in all_days:
        for s in all_shifts:
            model.AddExactlyOne(shifts[(n, d, s)] for n in all_nurses)

    # Each nurse works at most one shift per day
    for n in all_nurses:
        for d in all_days:
            model.AddAtMostOne(shifts[(n, d, s)] for s in all_shifts)

    # Distribute the shifts evenly among nurses
    min_shifts_per_nurse = (num_shifts * num_days) // num_nurses
    max_shifts_per_nurse = min_shifts_per_nurse + (1 if num_shifts * num_days % num_nurses != 0 else 0)
    for n in all_nurses:
        num_shifts_worked: Union[cp_model.LinearExpr, int] = 0
        for d in all_days:
            for s in all_shifts:
                num_shifts_worked += shifts[(n, d, s)]
        model.Add(min_shifts_per_nurse <= num_shifts_worked)
        model.Add(num_shifts_worked <= max_shifts_per_nurse)

    # Maximize the number of fulfilled shift requests
    model.Maximize(
        sum(
            shift_requests[n][d][s] * shifts[(n, d, s)]
            for n in all_nurses
            for d in all_days
            for s in all_shifts
        )
    )

    # Add constraints for holiday requests
    for n in all_nurses:
        for d in all_days:
            if holiday_requests[n][d] == 1:
                for s in all_shifts:
                    model.Add(shifts[(n, d, s)] == 0)

    # Add constraint to prevent a nurse from working the last shift of day d and the first shift of day d+1
    for n in all_nurses:
        for d in range(num_days - 1):  # last day does not need this constraint
            model.Add(shifts[(n, d, num_shifts - 1)] + shifts[(n, d + 1, 0)] <= 1)

    # Create the solver and solve
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # Visualize schedule
    if status == cp_model.OPTIMAL:
        sched = []
        for d in range(num_days):
            for n in range(num_nurses):
                for s in range(num_shifts):
                    if solver.Value(shifts[(n, d, s)]) == 1:
                        sched.append((n, d, s))
        #visualize_schedule(sched, num_days, num_shifts, num_nurses)

    return jsonify({"status": sched})

if __name__ == '__main__':
    app.run(debug=True)