session_nonce_key = "session_nonce"


def check_nonce(nonce, session_id, redis):
    try:
        nonce_value = int(nonce)
        current_nonce = redis.hget(session_nonce_key, session_id)
        if not current_nonce:
            current_nonce = 0

        current_nonce = int(current_nonce)
        if nonce_value <= current_nonce:
            return False
        redis.hset(session_nonce_key, session_id, nonce_value)
    except ValueError:
        return False

    return True


def get_nonce(session_id, redis):
    last_nonce = redis.hget(session_nonce_key, session_id)
    if not last_nonce:
        last_nonce = 0
    else:
        try:
            last_nonce = int(last_nonce)
        except ValueError:
            return None

    return last_nonce + 1
