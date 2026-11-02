def test_health(client):
    response=client.get("/health")
    assert response.status_code==200
    assert response.json()["status"]=="ok"

def test_register_login_and_me(client):
    r=client.post("/auth/register",json={"full_name":"Test Customer","email":"customer@example.com","password":"SecurePass123"})
    assert r.status_code==201, r.text
    login=client.post("/auth/login",data={"username":"customer@example.com","password":"SecurePass123"})
    assert login.status_code==200, login.text
    token=login.json()["access_token"]
    me=client.get("/auth/me",headers={"Authorization":f"Bearer {token}"})
    assert me.status_code==200
    assert me.json()["email"]=="customer@example.com"

def test_products_list_empty(client):
    response=client.get("/products?page=1&limit=10")
    assert response.status_code==200
    assert response.json()==[]


def test_duplicate_registration_rejected(client):
    payload = {
        "full_name": "Test Customer",
        "email": "duplicate@example.com",
        "password": "SecurePass123"
    }

    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201, first.text

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 409, second.text


def test_invalid_login_rejected(client):
    response = client.post(
        "/auth/login",
        data={
            "username": "nobody@example.com",
            "password": "WrongPassword123"
        }
    )

    assert response.status_code == 401


def test_customer_cannot_create_restaurant(client):
    # Register a customer
    client.post(
        "/auth/register",
        json={
            "full_name": "Test Customer",
            "email": "restaurant_customer@example.com",
            "password": "SecurePass123"
        }
    )

    # Log in
    login = client.post(
        "/auth/login",
        data={
            "username": "restaurant_customer@example.com",
            "password": "SecurePass123"
        }
    )

    assert login.status_code == 200, login.text

    token = login.json()["access_token"]

    # Customer tries to create a restaurant
    response = client.post(
        "/restaurants",
        json={
            "name": "Unauthorized Restaurant",
            "description": "Test restaurant",
            "location": "Kumasi"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403, response.text


def test_restaurant_list_is_public(client):
    response = client.get("/restaurants")

    assert response.status_code == 200, response.text
    assert isinstance(response.json(), list)


def test_customer_cannot_create_order_with_empty_cart(client):
    # Register a customer
    client.post(
        "/auth/register",
        json={
            "full_name": "Order Test Customer",
            "email": "emptycart@example.com",
            "password": "SecurePass123"
        }
    )

    # Log in
    login = client.post(
        "/auth/login",
        data={
            "username": "emptycart@example.com",
            "password": "SecurePass123"
        }
    )

    assert login.status_code == 200, login.text

    token = login.json()["access_token"]

    # Try creating an order with an empty cart
    response = client.post(
        "/orders",
        json={},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cart is empty"

