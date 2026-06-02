from src.generation.legal_generator import SubstantiveLegalGenerator


def test_generation_tokens_are_capped_for_groq():
    generator = SubstantiveLegalGenerator.__new__(SubstantiveLegalGenerator)

    capped = generator._cap_max_tokens(6000, provider="groq")

    assert capped == 1800


def test_generation_tokens_are_capped_for_non_groq():
    generator = SubstantiveLegalGenerator.__new__(SubstantiveLegalGenerator)

    capped = generator._cap_max_tokens(6000, provider="openai")

    assert capped == 1800
