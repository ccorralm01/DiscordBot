def get_response(user_input):
    lowered = user_input.lower()
    
    if lowered == "":
        return "Silent"
    elif "hello":
        return "hello!!!"