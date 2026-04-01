def login():
    """Authenticate a user and return an access token.

    TODO: Implement real authentication:
      - Accept a username + password from the request body
      - Verify the password against the stored hash (use hash_password from security.py)
      - Generate a signed JWT token (use encode_token from security.py)
      - Return the token in the OAuth2 response format: {"access_token": ..., "token_type": "bearer"}
    """
    return {"token": "test"}
