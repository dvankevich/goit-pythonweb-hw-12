import pytest

# Базові тестові дані для контактів
contact_data = {
    "first_name": "Taras",
    "last_name": "Shevchenko",
    "email": "taras@example.com",
    "phone": "+380123456789",
    "birthday": "1814-03-09",
}

contact_data_2 = {
    "first_name": "Lesya",
    "last_name": "Ukrainka",
    "email": "lesya@example.com",
    "phone": "+380987654321",
    "birthday": "1871-02-25",
}

PREFIX = "/api/contacts"


def test_create_contact_success(client, get_token):
    """Перевірка успішного створення контакту"""
    response = client.post(
        f"{PREFIX}/",
        json=contact_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["first_name"] == contact_data["first_name"]
    assert data["email"] == contact_data["email"]
    assert "id" in data


def test_create_contact_conflict(client, get_token):
    """Перевірка конфлікту: спроба створити контакт з існуючим email"""
    # Спробуємо додати той самий контакт ще раз
    response = client.post(
        f"{PREFIX}/",
        json=contact_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 409, response.text
    data = response.json()
    assert "already exists" in data["detail"]


def test_read_contacts_list(client, get_token):
    """Перевірка отримання списку контактів"""
    response = client.get(
        f"{PREFIX}/", headers={"Authorization": f"Bearer {get_token}"}
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    # Має бути як мінімум 1 контакт, який ми створили в першому тесті
    assert len(data) > 0
    assert data[0]["email"] == contact_data["email"]


def test_read_contact_by_id(client, get_token):
    """Перевірка отримання конкретного контакту за ID"""
    response = client.get(
        f"{PREFIX}/1",  # ID першого створеного контакту
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["id"] == 1
    assert data["email"] == contact_data["email"]


def test_read_contact_not_found(client, get_token):
    """Перевірка помилки 404 для неіснуючого контакту"""
    response = client.get(
        f"{PREFIX}/9999", headers={"Authorization": f"Bearer {get_token}"}
    )

    assert response.status_code == 404, response.text


def test_update_contact_success(client, get_token):
    """Перевірка успішного оновлення контакту"""
    update_data = {"first_name": "Taras (Updated)", "email": contact_data["email"]}

    response = client.put(
        f"{PREFIX}/1",
        json=update_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["first_name"] == "Taras (Updated)"
    assert data["email"] == contact_data["email"]


def test_update_contact_conflict(client, get_token):
    """Перевірка конфлікту при оновленні: email вже зайнятий іншим контактом"""
    # 1. Спочатку створюємо другий контакт
    client.post(
        f"{PREFIX}/",
        json=contact_data_2,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    # 2. Намагаємося оновити другий контакт (ID=2), вказавши email першого контакту
    update_data = {"email": contact_data["email"]}

    response = client.put(
        f"{PREFIX}/2",
        json=update_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 409, response.text
    data = response.json()
    assert "already taken by another of your contacts" in data["detail"]


def test_delete_contact_success(client, get_token):
    """Перевірка успішного видалення контакту"""
    response = client.delete(
        f"{PREFIX}/1", headers={"Authorization": f"Bearer {get_token}"}
    )

    assert response.status_code == 204
    # Переконуємось, що контенту дійсно немає
    assert response.text == ""

    # Перевіряємо, що він дійсно видалився
    check_response = client.get(
        f"{PREFIX}/1", headers={"Authorization": f"Bearer {get_token}"}
    )
    assert check_response.status_code == 404


def test_delete_contact_not_found(client, get_token):
    """Перевірка помилки 404 при спробі видалити неіснуючий контакт"""
    response = client.delete(
        f"{PREFIX}/9999", headers={"Authorization": f"Bearer {get_token}"}
    )

    assert response.status_code == 404


def test_read_contacts_with_query_params(client, get_token):
    """Перевірка отримання списку контактів із фільтрами (Query параметри)"""
    response = client.get(
        f"{PREFIX}/?first_name=Taras&last_name=Shevchenko&email=taras@example.com&upcoming_birthdays=true",
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_update_contact_not_found(client, get_token):
    """Перевірка помилки 404 при оновленні неіснуючого контакту"""
    update_data = {"first_name": "Ghost"}

    response = client.put(
        f"{PREFIX}/9999",  # Неіснуючий ID
        json=update_data,
        headers={"Authorization": f"Bearer {get_token}"},
    )

    assert response.status_code == 404
    assert "Contact not found" in response.json()["detail"]
