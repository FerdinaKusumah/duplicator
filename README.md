# Django Duplicator 🔁

A lightweight mixin for Django Admin that adds object duplication functionality, both in bulk (via an Admin Action) and
for single objects (via a "Duplicate and continue editing" button on the change form).

---

## ✨ Key Features

* **Single Object Duplication**: A "Duplicate and continue editing" button appears on the object detail page.
* **Bulk Duplication (Admin Action)**: An Admin Action is provided to duplicate selected objects from the changelist
  page.
* **DRY and Flexible**: Uses simple model and Admin mixins that are easy to integrate into any Django model.

---

## 💻 Installation

```shell
  pip install django-duplicator
```

Add `duplicator` to your `INSTALLED_APPS` in settings.py:

```shell
# settings.py
INSTALLED_APPS = [
    # ...
    'django.contrib.admin',
    # ...
    'duplicator',
]
```

## 🚀 Usage

1. Model (Enabling Duplication)

To make your model duplicatable, you must inherit from DuplicatorMixin.

```shell
    # models.py
    from django.db import models
    from duplicator import DuplicatorMixin
    
    class Customer(DuplicatorMixin, models.Model):
        name = models.CharField(max_length=255)
        # ... other fields ...
    
        def __str__(self):
            return self.name
```

2. Admin (Enabling Buttons and Actions)

To enable both the single duplication button and the bulk duplication Admin Action, inherit from
DuplicatorAdminMixin.

```shell
# admin.py
from django.contrib import admin
from duplicator import DuplicatorAdminMixin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(DuplicatorAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'id')
    # ... other admin configurations ...
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