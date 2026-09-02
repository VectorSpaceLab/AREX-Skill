def shortest_path_oracle(width, height, goal):
    actions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    policy = []
    for y in range(height):
        for x in range(width):
            best = []
            best_dist = 10**9
            for action, (dx, dy) in enumerate(actions):
                nx = min(width - 1, max(0, x + dx))
                ny = min(height - 1, max(0, y + dy))
                dist = abs(goal[0] - nx) + abs(goal[1] - ny)
                if dist < best_dist:
                    best = [action]
                    best_dist = dist
                elif dist == best_dist:
                    best.append(action)
            policy.append(best)
    return policy
