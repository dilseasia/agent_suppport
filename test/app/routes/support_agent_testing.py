# app/routes/support_agent_testing.py
from app.Agent.support.tool import SupportAgent
from app.Agent.support.schema import SupportRequest

def run_user_session(agent, thread_id, queries):
    print(f"\n--- Conversation for {thread_id} ---\n")
    for query in queries:
        request = SupportRequest(message=query)
        response = agent.handle_request(request, thread_id=thread_id)

        print(f"User query: {query}")
        print(f"Agent response: {response.response}")
        print(f"Tool used: {response.tool_used}")
        print(f"Tool output: {response.tool_output}")
        print("-" * 50)

def main():
    # Initialize agent
    agent = SupportAgent()

    # Queries for user1
    user1_queries = [
        "Book an appointment for servicing my Honda Civic",
        "Reschedule my appointment to next Monday",
        "Do I have any upcoming appointments?",
    ]

    # Queries for user2
    user2_queries = [
        "Show me all available vehicles in the dealership",
        "Do you have any electric cars?",
        "Give me the dealership contact number for LA01",
    ]

    # Run sessions for both users
    run_user_session(agent, thread_id="user1", queries=user1_queries)
    run_user_session(agent, thread_id="user2", queries=user2_queries)

if __name__ == "__main__":
    main()
