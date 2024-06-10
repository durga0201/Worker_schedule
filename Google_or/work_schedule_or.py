from typing import Union
from ortools.sat.python import cp_model
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib

matplotlib.use('Agg') 
def scheduler() -> None:
    # Number of nurses, shifts, and days
    num_nurses = 5
    num_shifts = 3
    num_days = 7
    all_nurses = range(num_nurses)
    all_shifts = range(num_shifts)
    all_days = range(num_days)

    # Shift requests by nurses
    shift_requests = [
        [[0, 0, 1], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 0, 1]],
        [[0, 0, 0], [0, 0, 0], [0, 1, 0], [0, 1, 0], [1, 0, 0], [0, 0, 0], [0, 0, 1]],
        [[0, 1, 0], [0, 1, 0], [0, 0, 0], [1, 0, 0], [0, 0, 0], [0, 1, 0], [0, 0, 0]],
        [[0, 0, 1], [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0], [1, 0, 0], [0, 0, 0]],
        [[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0]],
    ]

    # Holiday requests by nurses (1 indicates a request for a holiday on that day)
    holiday_requests = [
        [0, 1, 0, 0, 0, 0, 0],  # Nurse 0 requests holiday on day 1
        [0, 0, 0, 1, 0, 0, 0],  # Nurse 1 requests holiday on day 3
        [1, 0, 0, 0, 0, 0, 0],  # Nurse 2 requests holiday on day 0
        [0, 0, 0, 0, 0, 1, 0],  # Nurse 3 requests holiday on day 5
        [0, 0, 0, 0, 1, 0, 0],  # Nurse 4 requests holiday on day 4
    ]

    # Create the model
    model = cp_model.CpModel()

    # Create shift variables
    shifts = {}
    for n in all_nurses:
        for d in all_days:
            for s in all_shifts:
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

    # Print solution
    if status == cp_model.OPTIMAL:
        print("Solution:")
        sched = []
        for d in all_days:
            print("Day", d)
            for n in all_nurses:
                for s in all_shifts:
                    if solver.Value(shifts[(n, d, s)]) == 1:
                        sched.append((n, d, s))
                        if shift_requests[n][d][s] == 1:
                            print("Nurse", n, "works shift", s, "(requested).")
                        else:
                            print("Nurse", n, "works shift", s, "(not requested).")
            print()
        print(
            f"Number of shift requests met = {solver.ObjectiveValue}",
            f"(out of {num_nurses * min_shifts_per_nurse})",
        )
        visualize_schedule(sched, num_days, num_shifts, num_nurses)
    else:
        print("No optimal solution found!")


    # Statistics
    print("\nStatistics")
    print(f"  - conflicts: {solver.NumConflicts}")
    print(f"  - branches : {solver.NumBranches}")
    print(f"  - wall time: {solver.WallTime()}s")

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
    plt.savefig("schedule_or.png")
    plt.show()

    # Print schedule to command-line
    print("\nSchedule:\n")
    for n in range(n_nurses-1, -1, -1):
        str_row = ""
        for d in range(n_days):
            for s in range(n_shifts):
                outcome = "X" if (n, d, s) in sched else " "
                str_row += " " + outcome
        print(f"Nurse {n}", str_row)

    str_header_for_output = " " * 11
    str_header_for_output += "  ".join(f"{d}-{s}" for d in range(n_days) for s in range(n_shifts))
    print(str_header_for_output, "\n")

    print("Schedule saved as schedule.png.")


if __name__ == "__main__":
    scheduler()
