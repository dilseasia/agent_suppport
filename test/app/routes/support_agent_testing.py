# app/routes/support_agent_testing.py
from app.Agent.support.tool import SupportAgent
from app.Agent.support.schema import SupportRequest

def run_user_session(agent, thread_id, queries):
    print(f"\n=== Conversation for {thread_id} ===\n")
    for query in queries:
        request = SupportRequest(message=query)
        response = agent.handle_request(request, thread_id=thread_id)

        print(f"👤 User: {query}")
        print(f"🤖 Agent: {response.response}")
        print(f"🔧 Tool used: {response.tool_used}")
        print(f"📊 Tool output: {response.tool_output}")
        if response.error_message:
            print(f"⚠️ Error: {response.error_message}")
        print("-" * 60)

    # Debug: print memory at the end
    if thread_id in agent.memory:
        print(f"\n🧠 Memory for {thread_id}:")
        for msg in agent.memory[thread_id]:
            role = "User" if msg.type == "human" else "Agent"
            print(f"{role}: {msg.content}")
        print("=" * 60)

def interactive_chat(agent, thread_id="interactive"):
    """Optional REPL-style chat loop for testing"""
    print("\n💬 Interactive Chat Mode (type 'exit' to quit)\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting chat...")
            break

        request = SupportRequest(message=user_input)
        response = agent.handle_request(request, thread_id=thread_id)

        print(f"🤖 Agent: {response.response}")
        if response.tool_used:
            print(f"(Tool: {response.tool_used}, Output: {response.tool_output})")

def main():
    # Initialize agent
    agent = SupportAgent()

    # Predefined test queries for user1
    user1_queries = [
        "Book an appointment for servicing my Honda Civic",
        "Reschedule my appointment to next Monday",
        "Do I have any upcoming appointments?",
    ]

    # Predefined test queries for user2
    user2_queries = [
        "Show me all available vehicles in the dealership",
        "Do you have any electric cars?",
        "Give me the dealership contact number for LA01",
    ]

    # Run scripted sessions
    run_user_session(agent, thread_id="user1", queries=user1_queries)
    run_user_session(agent, thread_id="user2", queries=user2_queries)

    # Optional: enable interactive REPL
    interactive_chat(agent)

if __name__ == "__main__":
    main()
