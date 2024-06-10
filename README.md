
# Worker Scheduling API

This Flask API allows you to solve worker scheduling problems using OR-Tools/DWAVE and visualize the results. It accepts shift requests and holiday requests as input and returns the optimal schedule if found.

## Requirements

- Python 3
- Flask
- OR-Tools
- Dwave
- Matplotlib

## Installation

1. Clone this repository:

```bash
git clone [https://github.com/yourusername/nurse-scheduling-api.git](https://github.com/durga0201/Worker_schedule.git)
```

##Install the required dependencies:
```bash
pip install flask ortools matplotlib
```
## Start the Flask server:

```
python app.py
```

## Send a POST request to the /schedule endpoint with the scheduling data in the JSON format. Here's an example using curl:
```bash
curl -X POST -H "Content-Type: application/json" -d '{
    "num_nurses": 5,
    "num_shifts": 3,
    "num_days": 7,
    "shift_requests": [
        [[0, 0, 1], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 0, 1]],
        [[0, 0, 0], [0, 0, 0], [0, 1, 0], [0, 1, 0], [1, 0, 0], [0, 0, 0], [0, 0, 1]],
        [[0, 1, 0], [0, 1, 0], [0, 0, 0], [1, 0, 0], [0, 0, 0], [0, 1, 0], [0, 0, 0]],
        [[0, 0, 1], [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0], [1, 0, 0], [0, 0, 0]],
        [[0, 0, 0], [0, 0, 1], [0, 1, 0], [0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0]]
    ],
    "holiday_requests": [
        [0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 1, 0],
        [0, 0, 0, 0, 1, 0, 0]
    ]
}' http://localhost:5000/schedule
```
