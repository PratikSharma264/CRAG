"""MedCPT Query Encoder (same encoding as query.py). torch and transformers load on first use."""

from functools import lru_cache

from . import config


@lru_cache(maxsize=1)
def _load_query_encoder():
    # Imported here, not at the top, so `runserver` and `migrate` start even without loading torch.
    from transformers import AutoModel, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(config.QUERY_MODEL_NAME)
    model = AutoModel.from_pretrained(config.QUERY_MODEL_NAME)
    model.eval()
    return tokenizer, model


def encode_query(question):
    """Return the 768-dimensional MedCPT embedding of a question as a list of floats."""
    import torch

    tokenizer, model = _load_query_encoder()

    encoded = tokenizer(
        [question],
        truncation=True,
        padding=True,
        return_tensors="pt",
        max_length=config.MAX_TOKENS,
    )

    with torch.no_grad():
        output = model(**encoded)

    # CLS token embedding
    return output.last_hidden_state[:, 0, :].squeeze().numpy().tolist()
