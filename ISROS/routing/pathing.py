import heapq

class PriorityQueue:
    def __init__(self):
        self.elements = []
    
    def empty(self):
        return len(self.elements) == 0
    
    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))
    
    def get(self):
        return heapq.heappop(self.elements)[1]

def heuristic(a, b):
    (x1, y1) = a
    (x2, y2) = b
    return abs(x1 - x2) + abs(y1 - y2)

def a_star_search(grid, start, goal):
    frontier = PriorityQueue()
    frontier.put(start, 0)
    came_from = {}
    cost_so_far = {}
    came_from[start] = None
    cost_so_far[start] = 0
    
    while not frontier.empty():
        current = frontier.get()
        
        if current == goal:
            break
        
        for next in neighbors(grid, current):
            new_cost = cost_so_far[current] + 1  # Assumes a cost of 1 for moving to a neighbor
            if next not in cost_so_far or new_cost < cost_so_far[next]:
                cost_so_far[next] = new_cost
                priority = new_cost + heuristic(goal, next)
                frontier.put(next, priority)
                came_from[next] = current
    
    return reconstruct_path(came_from, start, goal)

def neighbors(grid, current):
    (x, y) = current
    results = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]
    # Remove neighbors that are out-of-bounds or not walkable
    results = filter(lambda point: 0 <= point[0] < len(grid) and 0 <= point[1] < len(grid[0]) and grid[point[0]][point[1]], results)
    return results

def reconstruct_path(came_from, start, end):
    current = end
    path = []
    while current != start:
        path.append(current)
        current = came_from[current]
    path.append(start)  # optional
    path.reverse()  # optional
    return path

# Example usage:
if __name__ == "__main__":
    # Create a grid where 'False' indicates an obstacle and 'True' indicates open space
    grid = [[True] * 10 for _ in range(10)]
    grid[1][2] = False  # Example obstacle

    start = (0, 0)
    goal = (9, 9)
    path = a_star_search(grid, start, goal)
    print("Path from start to goal:")
    print(path)