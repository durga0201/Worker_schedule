from collections import defaultdict
from copy import deepcopy
from dimod import BinaryQuadraticModel
from dwave.system import LeapHybridSampler
from dwave.system import DWaveSampler
from dwave.samplers import SimulatedAnnealingSampler

from dimod import BinaryQuadraticModel
from collections import defaultdict
from copy import deepcopy
import matplotlib

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
except ImportError:
    matplotlib.use("agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle


# Problem size
n_nurses = 5
n_days = 7
n_shifts = 2
size = n_nurses * n_days * n_shifts

# Parameters for hard nurse constraint
a = 3.5

# Parameters for hard shift constraint
lagrange_hard_shift = 1.3
workforce = 1  # Only one nurse per shift
effort = 1

# Parameters for soft nurse constraint
lagrange_soft_nurse = 0.5
preference = 1
min_duty_days = int(n_days * n_shifts / n_nurses)

# Preferred days off (list of lists where each sublist corresponds to a nurse's preferred off days)
preferred_off_days = [
    [],       # Nurse 0
    [],   # Nurse 1 prefers days 1 and 4 off
    [],       # Nurse 2 prefers day 2 off
    [],
    []
]

# Helper functions for index mapping
def get_index(nurse_index, day_index, shift_index):
    return nurse_index * n_days * n_shifts + day_index * n_shifts + shift_index

def get_nurse_day_shift(index):
    nurse_index, remainder = divmod(index, n_days * n_shifts)
    day_index, shift_index = divmod(remainder, n_shifts)
    return nurse_index, day_index, shift_index

# Building the QUBO model
Q = defaultdict(int)

# Hard nurse constraint: no nurse works two consecutive shifts
for nurse in range(n_nurses):
    for day in range(n_days):
        for shift in range(n_shifts - 1):
            ind1 = get_index(nurse, day, shift)
            ind2 = get_index(nurse, day, shift + 1)
            Q[ind1, ind2] = a

# Hard nurse constraint: no nurse works last shift of one day and first shift of next day
for nurse in range(n_nurses):
    for day in range(n_days - 1):
        ind1 = get_index(nurse, day, n_shifts - 1)
        ind2 = get_index(nurse, day + 1, 0)
        Q[ind1, ind2] = a

# Hard shift constraint: at least 1 nurse working per shift each day
for day in range(n_days):
    for shift in range(n_shifts):
        for nurse1 in range(n_nurses):
            ind1 = get_index(nurse1, day, shift)
            Q[ind1, ind1] += lagrange_hard_shift * (effort ** 2 - 2 * workforce * effort)
            for nurse2 in range(nurse1 + 1, n_nurses):
                ind2 = get_index(nurse2, day, shift)
                Q[ind1, ind2] += 2 * lagrange_hard_shift * effort ** 2

# Soft nurse constraint: even distribution of work days
for nurse in range(n_nurses):
    for day in range(n_days):
        for shift in range(n_shifts):
            ind = get_index(nurse, day, shift)
            Q[ind, ind] += lagrange_soft_nurse * (preference ** 2 - 2 * min_duty_days * preference)
            for other_shift in range(shift + 1, n_shifts):
                ind2 = get_index(nurse, day, other_shift)
                Q[ind, ind2] += 2 * lagrange_soft_nurse * preference ** 2

# Preference constraint: ensure certain nurses get preferred days off
penalty_off_day = 10  # Large penalty for working on preferred off days
for nurse in range(n_nurses):
    for day in preferred_off_days[nurse]:
        for shift in range(n_shifts):
            ind = get_index(nurse, day, shift)
            Q[ind, ind] += penalty_off_day

# Solve the problem
e_offset = (lagrange_hard_shift * n_days * n_shifts * workforce ** 2) + (lagrange_soft_nurse * n_nurses * min_duty_days ** 2)
bqm = BinaryQuadraticModel.from_qubo(Q, offset=e_offset)


sampler = SimulatedAnnealingSampler()
results = sampler.sample(bqm, label='Example - Nurse Scheduling')

# Get the results
smpl = results.first.sample

# Graphics
print("\nBuilding schedule and checking constraints...\n")
sched = [get_nurse_day_shift(j) for j in range(size) if smpl[j] == 1]

def check_hard_shift_constraint(sched, n_days, n_shifts):

    satisfied = [[False] * n_shifts for _ in range(n_days)]
    for _, day, shift in sched:
        satisfied[day][shift] = True

    if all(all(shift for shift in day) for day in satisfied):
        return "Satisfied"
    else:
        return "Unsatisfied"

def check_hard_nurse_constraint(sched, n_nurses):

    satisfied = [True] * n_nurses
    for nurse, day, shift in sched:
        if (shift == 0 and ((nurse, day, 1) in sched or (nurse, day-1, 1) in sched)) or \
           (shift == 1 and ((nurse, day, 0) in sched or (nurse, day+1, 0) in sched)):
            satisfied[nurse] = False
    if all(satisfied):
        return "Satisfied"
    else:
        return "Unsatisfied"

def check_soft_nurse_constraint(sched, n_nurses):

    num_shifts = [0] * n_nurses
    for nurse, _, _ in sched:
        num_shifts[nurse] += 1

    if num_shifts.count(num_shifts[0]) == len(num_shifts):
        return "Satisfied"
    else:
        return "Unsatisfied"

print("\tHard shift constraint:", check_hard_shift_constraint(sched, n_days, n_shifts))
print("\tHard nurse constraint:", check_hard_nurse_constraint(sched, n_nurses))
print("\tSoft nurse constraint:", check_soft_nurse_constraint(sched, n_nurses))

# Save image of schedule
x, y = zip(*[(day * n_shifts + shift, nurse) for nurse, day, shift in sched])
fig = plt.figure()
ax = fig.add_subplot(111)
ax.scatter(x, y)
width = 1
height = 1
colors = ['blue', 'red', 'green']
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