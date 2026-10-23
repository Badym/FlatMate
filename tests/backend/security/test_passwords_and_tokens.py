from __future__ import annotations

import re

import pytest

from backend.core.constants import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH
from backend.security.passwords import PasswordPolicyError, hash_password, verify_password
from backend.security.tokens import hash_token, new_invite_token, new_session_token

PASSWORD = "a" * PASSWORD_MIN_LENGTH


def test_hash_is_salted_and_verifiable() -> None:
    first, second = hash_password(PASSWORD), hash_password(PASSWORD)

    assert first != second
    assert first.startswith("scrypt:")
    assert verify_password(first, PASSWORD)
    assert not verify_password(first, PASSWORD + "b")


@pytest.mark.parametrize("length", [PASSWORD_MIN_LENGTH - 1, PASSWORD_MAX_LENGTH + 1])
def test_password_length_policy(length: int) -> None:
    with pytest.raises(PasswordPolicyError):
        hash_password("a" * length)


def test_unknown_account_never_verifies() -> None:
    assert verify_password(None, PASSWORD) is False


def test_session_tokens_are_random_hex() -> None:
    tokens = {new_session_token() for _ in range(50)}

    assert len(tokens) == 50
    assert all(re.fullmatch(r"[0-9a-f]{64}", token) for token in tokens)


def test_invite_token_has_256_bits() -> None:
    assert len(new_invite_token()) >= 43
    assert new_invite_token() != new_invite_token()


def test_hash_token_is_sha256() -> None:
    assert hash_token("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
