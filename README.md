# Django Duplicator 🔁

A lightweight mixin for Django Admin that adds object duplication functionality, both in bulk (via an Admin Action) and
for single objects (via a "Duplicate and continue editing" button on the change form).

---

## ✨ Key Features

* **Single Object Duplication**: A "Duplicate and continue editing" button appears on the object detail page.
* **Bulk Duplication (Admin Action)**: An Admin Action is provided to duplicate selected objects from the changelist
  page.
* **Data Control**: Easily **exclude specific fields** from duplication to ensure data integrity (e.g., unique fields,
  timestamps).
* **DRY and Flexible**: Uses simple model and Admin mixins that are easy to integrate into any Django model.

---

## 💻 Installation

```shell
  pip install django-duplicator
```

Add `duplicator` to your `INSTALLED_APPS` in settings.py:

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'django.contrib.admin',
    # ...
    'duplicator',
]
```

## 🚀 Usage

### 1. Model (Enabling Duplication)

To make your model duplicatable, you must inherit from DuplicatorMixin.

```python
# models.py
from django.db import models
from duplicator import DuplicatorMixin


class Customer(DuplicatorMixin, models.Model):
    name = models.CharField(max_length=255)

    # ... other fields ...

    def __str__(self):
        return self.name
```

### 2. Admin (Enabling Buttons and Actions)

To enable both the single duplication button and the bulk duplication Admin Action, inherit from DuplicatorAdminMixin.

```python
# admin.py
from django.contrib import admin
from duplicator import DuplicatorAdminMixin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(DuplicatorAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'id')
    # ... other admin configurations ...
```

---

## ⚙️ Customization: Excluding Fields (Safety Feature)

By default, the duplicator performs a shallow copy of all fields. You can prevent specific fields (like unique fields,
slugs, or timestamps) from being copied by defining the **DUPLICATOR_EXCLUDE_FIELDS** list in your model.

Fields in this list will be ignored during the copy process and will revert to their model's default value or None (
behaving like a new record).

```python
# models.py
from duplicator import DuplicatorMixin


class Product(DuplicatorMixin, models.Model):
    # 🛡️ EXCLUDE FIELDS: Use this list to prevent certain fields from being copied.
    DUPLICATOR_EXCLUDE_FIELDS = [
        'sku',  # Assuming 'sku' must be unique or has a default
        'created_at',  # Should be set to the current time by Django
        'last_modified',  # Should be updated by Django
    ]

    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # ...
```

## 📸 Feature Demonstration

### A. Bulk Duplication (Admin Action)

The duplication option appears in the Actions dropdown menu on the changelist page.

![Action](./images/action.png)

### B. Single Duplication (Change Form Button)

The "Duplicate and continue editing" button is prominently placed on the object detail page.

![Detail](./images/detail.png)

## 🤝 Contributing

We welcome all contributions! If you find a bug or have a feature suggestion, please open an Issue or submit a Pull
Request.

## 📄 License

This project is licensed under the [Your License Type, e.g., MIT License]. See the LICENSE file for full details.