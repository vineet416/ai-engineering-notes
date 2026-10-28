from rag_eval.data import load_docs, load_questions
from rag_eval.metrics import first_hit_rank, is_hit, normalise


def test_every_answer_sentence_is_in_the_docs():
    corpus = " ".join(normalise(t) for t in load_docs().values())
    for q in load_questions():
        assert normalise(q["evidence"]) in corpus, q["id"]


def test_question_ids_are_unique():
    ids = [q["id"] for q in load_questions()]
    assert len(ids) == len(set(ids))


def test_hit_ignores_case_and_line_breaks():
    assert is_hit("The Whole\ncontents  will be stored", "the whole contents will be stored")


def test_half_a_sentence_is_a_miss():
    assert not is_hit("the whole contents", "the whole contents will be stored")


def test_first_hit_rank():
    texts = ["nothing", "answer is here", "answer is here too"]
    assert first_hit_rank(texts, [0, 2, 1], "answer is here") == 2
    assert first_hit_rank(texts, [0], "answer is here") is None
