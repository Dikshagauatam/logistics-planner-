import heapq
cities = {
    "Delhi": {"lat": 28.7041, "lon": 77.1025},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639},
    "Chennai": {"lat": 13.0827, "lon": 80.2707},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
}

transport_modes = {
    "Road": {"speed_kmph": 40, "cost_per_km": 15, "flexibility": 0.9, "weather_sensitivity": 0.8},
    "Rail": {"speed_kmph": 50, "cost_per_km": 10, "flexibility": 0.5, "weather_sensitivity": 0.2},
    "Air": {"speed_kmph": 600, "cost_per_km": 100, "flexibility": 0.1, "weather_sensitivity": 0.9}, # Air cargo is faster but expensive
}
routes = {
    ("Delhi", "Mumbai"): 1400,
    ("Delhi", "Kolkata"): 1500,
    ("Delhi", "Bengaluru"): 2100,
    ("Mumbai", "Bengaluru"): 980,
    ("Mumbai", "Chennai"): 1350,
    ("Kolkata", "Chennai"): 1670,
    ("Bengaluru", "Chennai"): 350,
    ("Hyderabad", "Mumbai"): 710,
    ("Hyderabad", "Bengaluru"): 570,
    ("Delhi", "Hyderabad"): 1500,
}
current_impacts = {
    "Delhi_Mumbai_Road": { 
        "weather": {"time_factor": 1.5, "cost_factor": 1.2},
        "law_order": {"time_factor": 1.0, "cost_factor": 1.0},
        "strikes": {"time_factor": 1.0, "cost_factor": 1.0},
    },
    "Kolkata_Road": {
        "weather": {"time_factor": 1.0, "cost_factor": 1.0},
        "law_order": {"time_factor": 1.2, "cost_factor": 1.1},
        "strikes": {"time_factor": 1.8, "cost_factor": 1.5},
    },
    "Bengaluru_Air": { 
        "weather": {"time_factor": 1.3, "cost_factor": 1.05},
        "law_order": {"time_factor": 1.0, "cost_factor": 1.0},
        "strikes": {"time_factor": 1.0, "cost_factor": 1.0},
    },
  
    "default": {
        "weather": {"time_factor": 1.0, "cost_factor": 1.0},
        "law_order": {"time_factor": 1.0, "cost_factor": 1.0},
        "strikes": {"time_factor": 1.0, "cost_factor": 1.0},
    }
}

def get_impact_factors(route_name, mode):
    """Retrieves combined impact factors for a given route and mode."""
    impact_data = current_impacts.get(route_name + "_" + mode, current_impacts["default"])

    total_time_factor = 1.0
    total_cost_factor = 1.0

    for category in ["weather", "law_order", "strikes"]:
        total_time_factor *= impact_data.get(category, {}).get("time_factor", 1.0)
        total_cost_factor *= impact_data.get(category, {}).get("cost_factor", 1.0)
    return total_time_factor, total_cost_factor

graph = {}

for (city_a, city_b), distance in routes.items():
    for mode_name, mode_props in transport_modes.items():
        base_time = distance / mode_props["speed_kmph"]
        base_cost = distance * mode_props["cost_per_km"]

        route_impact_name = f"{city_a}{city_b}" if f"{city_a}{city_b}_{mode_name}" in current_impacts else \
                            f"{city_b}{city_a}" if f"{city_b}{city_a}_{mode_name}" in current_impacts else \
                            city_a if city_a in current_impacts and not (f"{city_a}{city_b}" in current_impacts or f"{city_b}{city_a}" in current_impacts) else \
                            city_b if city_b in current_impacts and not (f"{city_a}{city_b}" in current_impacts or f"{city_b}{city_a}" in current_impacts) else \
                            "default" 
        time_factor, cost_factor = get_impact_factors(route_impact_name, mode_name)

   
        actual_time = base_time * time_factor
        actual_cost = base_cost * cost_factor

        edge_weight = actual_time * 500 + actual_cost

        if city_a not in graph:
            graph[city_a] = []
        if city_b not in graph:
            graph[city_b] = []

        graph[city_a].append((city_b, mode_name, actual_time, actual_cost, edge_weight))
        graph[city_b].append((city_a, mode_name, actual_time, actual_cost, edge_weight)) # Bidirectional routes

def find_best_route(start_city, end_city):
    """
    Finds the best route (shortest path) using Dijkstra's algorithm.
    The "best" is defined by the minimum 'edge_weight'.
    """
    if start_city not in cities or end_city not in cities:
        return "Invalid city names.", None

    distances = {city: float('inf') for city in cities}
    distances[start_city] = 0

    previous_nodes = {city: None for city in cities}
    previous_modes = {city: None for city in cities}

    pq = [(0, start_city, 0, 0)]

    while pq:
        current_weighted_cost, current_city, current_time, current_cost = heapq.heappop(pq)

        if current_weighted_cost > distances[current_city]:
            continue

        for neighbor, mode, travel_time, travel_cost, edge_weight in graph.get(current_city, []):
            new_weighted_cost = current_weighted_cost + edge_weight
            new_time = current_time + travel_time
            new_cost = current_cost + travel_cost

            if new_weighted_cost < distances[neighbor]:
                distances[neighbor] = new_weighted_cost
                previous_nodes[neighbor] = current_city
                previous_modes[neighbor] = mode
                heapq.heappush(pq, (new_weighted_cost, neighbor, new_time, new_cost))
    path = []
    current = end_city
    while current is not None:
        path.insert(0, (current, previous_modes[current]))
        current = previous_nodes[current]

    
    formatted_path = []
    total_time = 0
    total_cost = 0

    if path[0][0] != start_city: 
        return "No path found between the cities.", None

    for i in range(len(path) - 1):
        city_from, _ = path[i]
        city_to, mode = path[i+1]
        for neighbor, m, time, cost, _ in graph.get(city_from, []):
            if neighbor == city_to and m == mode:
                formatted_path.append(f"  {city_from} --({mode}, Est. Time: {time:.2f} hrs, Est. Cost: ₹{cost:.2f})--> {city_to}")
                total_time += time
                total_cost += cost
                break
    
    return formatted_path, {"total_time": total_time, "total_cost": total_cost}

if __name__ == "_main_":
    print("Welcome to the India Goods Delivery Route Planner!")
    print("Available Cities:", ", ".join(cities.keys()))

    while True:
        start_city_input = input("Enter the origin city: ").strip().title()
        end_city_input = input("Enter the destination city: ").strip().title()

        if start_city_input not in cities:
            print(f"Error: Origin city '{start_city_input}' not found. Please choose from available cities.")
            continue
        if end_city_input not in cities:
            print(f"Error: Destination city '{end_city_input}' not found. Please choose from available cities.")
            continue
        if start_city_input == end_city_input:
            print("Origin and destination cities cannot be the same. Please try again.")
            continue

        print(f"\nSearching for the best route from {start_city_input} to {end_city_input}...")
        route_details, totals = find_best_route(start_city_input, end_city_input)

        if isinstance(route_details, str): # Error message returned
            print(route_details)
        else:
            print("\n--- Recommended Route ---")
            for step in route_details:
                print(step)
            print(f"\nTotal Estimated Time: {totals['total_time']:.2f} hours")
            print(f"Total Estimated Cost: ₹{totals['total_cost']:.2f}")

        print("\n" + "="*50 + "\n")
        another_search = input("Do you want to plan another route? (yes/no): ").lower()
        if another_search != 'yes':
            break

    print("Thank you for using the Route Planner!")