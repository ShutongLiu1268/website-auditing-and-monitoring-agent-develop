from datetime import datetime

import pytest
from bson import BSON
from pytest_mock import MockerFixture

from app.domain.models import AuditDefinition, AuditMode, PageTarget
from app.persistence.repositories import AuditDefinitionRepository


class TestAuditDefinitionRepository:
    @pytest.mark.asyncio
    async def test_create_stores_bson_encodable_target_url(self, mocker: MockerFixture):
        # Arrange
        collection = mocker.Mock(insert_one=mocker.AsyncMock())
        database = mocker.Mock(audit_definitions=collection)
        repository = AuditDefinitionRepository(database)
        definition = AuditDefinition(
            id="audit-1",
            mode=AuditMode.R3,
            targets=[
                PageTarget(
                    url="https://www.dell.com/en-ca/shop/laptops",
                    locale="en-CA",
                )
            ],
            rule_version="v1",
        )

        # Act
        result = await repository.create(definition)

        # Assert
        stored_document = collection.insert_one.await_args.args[0]
        BSON.encode(stored_document)
        assert stored_document["targets"][0]["url"] == str(definition.targets[0].url)
        assert isinstance(stored_document["created_at"], datetime)
        assert result is definition
