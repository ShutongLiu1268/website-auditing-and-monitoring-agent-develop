from fastapi.testclient import TestClient

from app import main

NUMBERED_PROMPT = (
    "Can you help me to audit those 3 pages against R3 checkpoints: "
    "1. https://www.dell.com/en-ca/shop/laptop-computers/spd/dell16laptopdc16251  "
    "2.https://www.dell.com/en-us/shop/laptop-computers/spd/dell16laptopdc16251 "
    "3. https://www.dell.com/fr-ca/shop/laptop-computers/spd/dell16laptopdc16251\n"
    "https://www.dell.com/fr-ca/shop/laptop-computers/spd/dell16laptopdc16251\n"
    "https://www.dell.com/fr-ca/shop/laptop-computers/spd/dell16laptopdc16251"
)


def test_parse_route_reads_three_pages_from_numbered_prompt():
    response = TestClient(main.app).post(
        "/api/prompt/parse", json={"prompt": NUMBERED_PROMPT}
    )

    assert response.status_code == 200
    body = response.json()
    assert [target["locale"] for target in body["targets"]] == [
        "en-CA",
        "en-US",
        "fr-CA",
    ]
    assert body["problems"] == []
