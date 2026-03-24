from contracts.collection import CollectionCreate
from contracts.shared import Visibility


def test_collection_create_model():
    c = CollectionCreate(
        name="Senior Backend — London",
        description="Top backend candidates in London",
        visibility=Visibility.shared_all,
        tags=["backend", "london", "senior"],
    )
    assert c.name == "Senior Backend — London"
    assert c.visibility == Visibility.shared_all
    assert len(c.tags) == 3


def test_collection_create_defaults():
    c = CollectionCreate(name="My List")
    assert c.visibility == Visibility.private
    assert c.shared_with is None
    assert c.tags == []
