import pytest
from src.database import init_db
from src.models.page import Page
from src.models.content_block import ContentBlock
from src.repositories.page_repo import PageRepo
from src.repositories.block_repo import BlockRepo
from src.repositories.task_repo import TaskRepo
from src.models.task import Task


@pytest.fixture
def db_init():
    init_db()


@pytest.fixture
def block_repo():
    return BlockRepo()


@pytest.fixture
def page_repo():
    return PageRepo()


@pytest.fixture
def task_repo():
    return TaskRepo()


@pytest.fixture
def sample_page(page_repo):
    return page_repo.create(Page(title="Test Page"))


class TestBlockRepoCreate:
    def test_creates_block_and_returns_id(self, block_repo, sample_page):
        block_id = block_repo.create(ContentBlock(page_id=sample_page, block_type="text"))
        assert block_id > 0

    def test_sets_block_id_on_object(self, block_repo, sample_page):
        block = ContentBlock(page_id=sample_page, block_type="text")
        block_repo.create(block)
        assert block.id is not None

    def test_auto_computes_sort_order(self, block_repo, sample_page):
        b1 = ContentBlock(page_id=sample_page, block_type="text")
        b2 = ContentBlock(page_id=sample_page, block_type="table")
        block_repo.create(b1)
        block_repo.create(b2)
        blocks = block_repo.get_by_page(sample_page)
        assert blocks[0].sort_order == 0
        assert blocks[1].sort_order == 1

    def test_stores_all_properties(self, block_repo, sample_page):
        block = ContentBlock(
            page_id=sample_page, block_type="table",
            content_markdown="| a | b |", height=300, width=400,
            header="My Table", header_font_size=16,
            header_align_h="center", header_align_v="top",
            header_height=50, content_font_size=14,
            pos_x=100, pos_y=200,
        )
        block_repo.create(block)
        blocks = block_repo.get_by_page(sample_page)
        assert len(blocks) == 1
        assert blocks[0].header == "My Table"
        assert blocks[0].height == 300
        assert blocks[0].pos_x == 100


class TestBlockRepoRead:
    def test_get_by_page_returns_blocks(self, block_repo, sample_page):
        block_repo.create(ContentBlock(page_id=sample_page, block_type="text"))
        blocks = block_repo.get_by_page(sample_page)
        assert len(blocks) == 1

    def test_get_by_page_empty(self, block_repo, sample_page):
        blocks = block_repo.get_by_page(sample_page)
        assert blocks == []

    def test_get_by_page_ordered_by_sort_order(self, block_repo, sample_page):
        block_repo.create(ContentBlock(page_id=sample_page, block_type="table"))
        block_repo.create(ContentBlock(page_id=sample_page, block_type="text"))
        blocks = block_repo.get_by_page(sample_page)
        assert blocks[0].block_type == "table"
        assert blocks[1].block_type == "text"


class TestBlockRepoUpdate:
    def test_updates_block(self, block_repo, sample_page):
        block = ContentBlock(page_id=sample_page, block_type="text")
        block_repo.create(block)
        block.content_markdown = "Updated content"
        block.height = 500
        block.header = "New Header"
        block_repo.update(block)
        blocks = block_repo.get_by_page(sample_page)
        assert blocks[0].content_markdown == "Updated content"
        assert blocks[0].height == 500
        assert blocks[0].header == "New Header"

    def test_update_preserves_page_id(self, block_repo, sample_page):
        block = ContentBlock(page_id=sample_page, block_type="text")
        block_repo.create(block)
        original_page_id = block.page_id
        block.content_markdown = "changed"
        block_repo.update(block)
        blocks = block_repo.get_by_page(sample_page)
        assert blocks[0].page_id == original_page_id


class TestBlockRepoDelete:
    def test_deletes_block(self, block_repo, sample_page):
        block = ContentBlock(page_id=sample_page, block_type="text")
        bid = block_repo.create(block)
        block_repo.delete(bid)
        assert block_repo.get_by_page(sample_page) == []

    def test_delete_cascades_to_tasks(self, block_repo, sample_page, task_repo):
        block = ContentBlock(page_id=sample_page, block_type="text")
        bid = block_repo.create(block)
        task_repo.create(Task(content_block_id=bid, text="task"))
        block_repo.delete(bid)
        assert task_repo.get_by_block(bid) == []

    def test_delete_by_page(self, block_repo, sample_page):
        block_repo.create(ContentBlock(page_id=sample_page, block_type="text"))
        block_repo.create(ContentBlock(page_id=sample_page, block_type="table"))
        block_repo.delete_by_page(sample_page)
        assert block_repo.get_by_page(sample_page) == []

    def test_delete_by_page_cascades_tasks(self, block_repo, sample_page, task_repo):
        bid = block_repo.create(ContentBlock(page_id=sample_page, block_type="text"))
        task_repo.create(Task(content_block_id=bid, text="t"))
        block_repo.delete_by_page(sample_page)
        assert task_repo.get_by_block(bid) == []
