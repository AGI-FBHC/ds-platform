from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


DATASET_IMAGE_COLUMNS = {
    "source_page_title": "ALTER TABLE dataset_images ADD COLUMN source_page_title VARCHAR(500) DEFAULT ''",
    "source_page_url": "ALTER TABLE dataset_images ADD COLUMN source_page_url VARCHAR(2000) DEFAULT ''",
    "mask_relative_path": "ALTER TABLE dataset_images ADD COLUMN mask_relative_path VARCHAR(500) DEFAULT ''",
    "mask_status": "ALTER TABLE dataset_images ADD COLUMN mask_status VARCHAR(32) DEFAULT 'not_requested'",
    "labels": "ALTER TABLE dataset_images ADD COLUMN labels JSON NULL",
    "search_metadata": "ALTER TABLE dataset_images ADD COLUMN search_metadata JSON NULL",
    "extra": "ALTER TABLE dataset_images ADD COLUMN extra JSON NULL",
}

DATASET_IMAGE_INDEXES = {
    "ix_img_ds_order": "CREATE INDEX ix_img_ds_order ON dataset_images (dataset_id, sort_order)",
    "ix_img_ds_keyword": "CREATE INDEX ix_img_ds_keyword ON dataset_images (dataset_id, keyword)",
    "ix_img_ds_width": "CREATE INDEX ix_img_ds_width ON dataset_images (dataset_id, width)",
}


def ensure_runtime_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    if "dataset_images" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("dataset_images")}
    indexes = {index["name"] for index in inspector.get_indexes("dataset_images")}

    with engine.begin() as conn:
        for column_name, ddl in DATASET_IMAGE_COLUMNS.items():
            if column_name not in columns:
                conn.execute(text(ddl))

        for index_name, ddl in DATASET_IMAGE_INDEXES.items():
            if index_name not in indexes:
                conn.execute(text(ddl))
