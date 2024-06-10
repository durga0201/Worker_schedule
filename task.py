import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from collections import defaultdict
from copy import deepcopy
from dwave.system import LeapHybridSampler
from dwave.samplers import SimulatedAnnealingSampler

# Parameters
n_nurses = 5      # count nurses n = 0 ... n_nurses-1
n_days = 7       # count scheduling days as d = 0 ... n_days-1
n_shifts = 2     # count shifts per day as s = 0 ... n_shifts-1
size = n_days * n_shifts * n_nurses

# Constraint parameters
a = 3.5
lagrange_hard_shift = 1.3
lagrange_soft_nurse = 0.3
preference = 1
min_duty_days = int(n_days * n_shifts / n_nurses)

# Composite index
def get_index(nurse_index, day_index, shift_index):
    return nurse_index * n_days * n_shifts + day_index * n_shifts + shift_index

# Inverse of composite index
def get_nurse_day_shift(index):
    nurse_index, remainder = divmod(index, n_days * n_shifts)
    day_index, shift_index = divmod(remainder, n_shifts)
    return nurse_index, day_index, shift_index

# Building QUBO
Q = defaultdict(int)

# Hard nurse constraint: no nurse works two consecutive shifts or consecutive days' shifts
for nurse in range(n_nurses):
    for day in range(n_days):
        for shift in range(n_shifts - 1):
            ind1 = get_index(nurse, day, shift)
            ind2 = get_index(nurse, day, shift + 1)
            Q[ind1, ind2] = a
        if day < n_days - 1:
            ind1 = get_index(nurse, day, n_shifts - 1)
            ind2 = get_index(nurse, day + 1, 0)
            Q[ind1, ind2] = a

# Hard shift constraint: only one nurse per shift
for day in range(n_days):
    for shift in range(n_shifts):
        for nurse1 in range(n_nurses):
            ind1 = get_index(nurse1, day, shift)
            Q[ind1, ind1] += lagrange_hard_shift * (1 - 2 * 1)
            for nurse2 in range(nurse1 + 1, n_nurses):
                ind2 = get_index(nurse2, day, shift)
                Q[ind1, ind2] += 2 * lagrange_hard_shift

# Soft nurse constraint: even distribution of work
for nurse in range(n_nurses):
    for day in range(n_days):
        for shift in range(n_shifts):
            ind = get_index(nurse, day, shift)
            Q[ind, ind] += lagrange_soft_nurse * (preference ** 2 - (2 * min_duty_days * preference))

# Off-diagonal terms for soft nurse constraint
for nurse in range(n_nurses):
    for day1 in range(n_days):
        for shift1 in range(n_shifts):
            for day2 in range(day1 + 1, n_days):
                for shift2 in range(n_shifts):
                    ind1 = get_index(nurse, day1, shift1)
                    ind2 = get_index(nurse, day2, shift2)
                    Q[ind1, ind2] += 2 * lagrange_soft_nurse * preference ** 2

# Solve the problem
from dimod import BinaryQuadraticModel

bqm = BinaryQuadraticModel.from_qubo(Q)
sampler = SimulatedAnnealingSampler()
results = sampler.sample(bqm)

# Get the results
smpl = results.first.sample

# Building schedule
sched = [get_nurse_day_shift(j) for j in range(size) if smpl[j] == 1]

# Checking constraints
def check_hard_shift_constraint(sched, n_days, n_shifts):
    shifts_per_day = [[False] * n_shifts for _ in range(n_days)]
    for _, day, shift in sched:
        shifts_per_day[day][shift] = True
    for shifts in shifts_per_day:
        if not all(shifts):
            return "Unsatisfied"
    return "Satisfied"

def check_hard_nurse_constraint(sched, n_nurses):
    satisfied = [True] * n_nurses
    for nurse, day, shift in sched:
        if ((nurse, day, shift+1) in sched) or ((nurse, day+1, 0) in sched):
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

print("\nHard shift constraint:", check_hard_shift_constraint(sched, n_days, n_shifts))
print("\nHard nurse constraint:", check_hard_nurse_constraint(sched, n_nurses))
print("\nSoft nurse constraint:", check_soft_nurse_constraint(sched, n_nurses))

# Save image of schedule
x, y, z = zip(*sched)
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(y, x, z)
width = 1
height = 1
depth = 1
colors = ['blue', 'red', 'green', 'yellow', 'purple']
for a_y, a_x, a_z in sched:
    ax.bar3d(a_y-width/2, a_x-height/2, a_z-depth/2, width, height, depth, color=colors[a_x])
ax.set_xticks(range(n_days))
ax.set_yticks(range(n_nurses))
ax.set_zticks(range(n_shifts))
ax.set_xlabel("Days")
ax.set_ylabel("Nurses")
ax.set_zlabel("Shifts")
plt.savefig("schedule.png")

# Print schedule to command-line
print("\nSchedule:\n")
for n in range(n_nurses-1, -1, -1):
    str_row = ""
    for d in range(n_days):
        for s in range(n_shifts):
            outcome = "X" if (n, d, s) in sched else " "
            str_row += "  " + outcome
    print("Nurse ", n, str_row)

str_header_for_output = " " * 11
str_header_for_output += "  ".join([f"{d}-{s}" for d in range(n_days) for s in range(n_shifts)])
print(str_header_for_output, "\n")

print("Schedule saved as schedule.png.")
