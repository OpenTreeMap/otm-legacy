
def set_auto_now(clazz, field_name, val):
    for field in clazz._meta.local_fields:
        if field.name == field_name:
            field.auto_now = val
