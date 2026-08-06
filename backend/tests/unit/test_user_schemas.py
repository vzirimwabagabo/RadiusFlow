from schemas import CreateUserRequest, CreateUserWithPackageRequest


def test_create_user_request_accepts_status():
    request = CreateUserRequest(username="demo", password="secret", status="blocked")

    assert request.status == "blocked"


def test_create_user_with_package_request_accepts_status():
    request = CreateUserWithPackageRequest(
        username="demo",
        password="secret",
        package_name="basic",
        status="blocked",
    )

    assert request.status == "blocked"