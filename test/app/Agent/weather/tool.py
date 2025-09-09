# greeting.py in app/services/tools
def handle_greeting(query: str) -> str:
    return "Hello! How can I assist you today?"



def handle_estimate(query: str) -> str:
    """
    Handles the estimation query and provides a response based on the query content.
    """
    # Example response based on the query
    if "replace faucet" in query.lower():
        return "The cost to replace a faucet usually ranges from $100 to $300, depending on the type and location."
    elif "install new sink" in query.lower():
        return "Installing a new sink typically costs between $150 and $500, including labor and materials."
    elif "repair pipes" in query.lower():
        return "Pipe repairs can vary depending on the issue, but the average cost is between $200 and $600."
    else:
        return "Could you please provide more details about the service you need a cost estimate for?"
    


def handle_support(query: str) -> str:
    """
    Handles the support query and returns a response based on the query content.
    """
    # Example response based on the query
    if "refund" in query.lower():
        return "I can help you with refund requests. Please provide your order number."
    elif "technical issue" in query.lower():
        return "I understand you're facing a technical issue. Please describe the problem in detail."
    elif "customer service" in query.lower():
        return "For customer service, please contact us via the support hotline or email support@supercar.com."
    else:
        return "How can I assist you with your support needs today?"