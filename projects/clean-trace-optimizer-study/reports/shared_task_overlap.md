# Shared-Task Overlap

Distinct tasks: 500. Tasks appearing in >1 solver enable task-fixed-effect models.

## Pairwise task overlap (Jaccard / intersection)

| | solver_A | solver_B | solver_C | solver_E | solver_F | solver_G | solver_H |
|---|---|---|---|---|---|---|---|
| solver_A | 466 | 466 | 466 | 466 | 466 | 466 | 466 |
| solver_B | 466 | 500 | 500 | 500 | 466 | 500 | 500 |
| solver_C | 466 | 500 | 500 | 500 | 466 | 500 | 500 |
| solver_E | 466 | 500 | 500 | 500 | 466 | 500 | 500 |
| solver_F | 466 | 466 | 466 | 466 | 466 | 466 | 466 |
| solver_G | 466 | 500 | 500 | 500 | 466 | 500 | 500 |
| solver_H | 466 | 500 | 500 | 500 | 466 | 500 | 500 |

## Task multiplicity (how many solvers share each task)

- in 5 solver(s): 34 tasks
- in 7 solver(s): 466 tasks

- Tasks shared by all 3 core development solvers (A,B,C): **466**
- Tasks shared by ALL 7 solvers: **466**

These 466 A/B/C-shared tasks support within-task paired comparisons and task-fixed-effect token models (RQ1 task-FE).